# coding: utf-8

import argparse
import csv
import datetime
import json
import logging
import os
import re
import sys

import dateutil.parser
from lxml import etree
import psycopg2
import pytz

from open511.converter.o5xml import json_struct_to_xml
from open511.converter.o5json import xml_to_json
from open511.utils.serialization import get_base_open511_element
from open511.validator import validate_single_item

JURISDICTION = 'ville.montreal.qc.ca'
TIMEZONE = pytz.timezone('America/Montreal')
SOURCE_SRID = 32188

POSTGRES_DSN = os.environ.get('POSTGRES_DSN', 'dbname=open511 user=postgres')

logger = logging.getLogger(__name__)

db_conn = psycopg2.connect(POSTGRES_DSN)

class DataError(Exception):
    pass

conv_funcs = []
def task(f):
    """Simple decorator to keep a list of conversion tasks."""
    conv_funcs.append(f)
    return f

@task
def _id(src, ev):
    ev['id'] = JURISDICTION + '/' + src.findtext('event-sid')
    # ev['url'] = BASE_URL + ev['id']

@task
def _headline(src, ev):
    ev['headline'] = src.findtext('event-name')

@task
def _description(src, ev):
    descr = src.findtext('project_references/project-description')
    if descr:
        ev['description'] = descr.replace("\r", '')

@task
def _status_id(src, ev):
    status_id = src.findtext('event-status-tmdd-id')
    if status_id and status_id.isdigit():
        if status_id in ('11', '12', '13'):
            # ended/deleted/cancelled
            ev['status'] = 'ARCHIVED'
        elif status_id == '5':
            # reported
            ev['certainty'] = 'POSSIBLE'
        elif status_id == '6':
            # confirmed
            ev['certainty'] = 'OBSERVED'

@task
def _active_flag(src, ev):
    ev.setdefault('status', 'ACTIVE')
    if src.findtext('event-flag-tmdd-id') == '2':
        ev['status'] = 'ARCHIVED'

@task
def _severity(src, ev):
    sev = src.findtext('event-severity-tmdd-id')
    if sev in ('1', '2'):
        ev['severity'] = 'MINOR'
    elif sev in ('3', '4'):
        ev['severity'] = 'MAJOR'
    else:
        ev['severity'] = 'UNKNOWN'

@task
def _event_type(src, ev):
    code = src.findtext('event-planned-event-class-id')
    if code == '2':
        ev['event_type'] = 'CONSTRUCTION'
    elif code == '3':
        ev['event_type'] = 'SPECIAL_EVENT'
    else:
        ev['event_type'] = 'INCIDENT'

ITIS_CATEGORIES = dict()
def _load_categories():
    my_dir = os.path.dirname(os.path.realpath(__file__))
    with open(os.path.join(my_dir, 'itis_categories.csv')) as f:
        reader = csv.DictReader(f)
        for row in reader:
            ITIS_CATEGORIES[row['id']] = row

@task
def _event_subtypes(src, ev):
    codes = set(src.xpath('event-descriptions/event-cause/ITIS-event-category-id/text()'))
    if codes and not ITIS_CATEGORIES:
        _load_categories()
    subtypes = set()
    itis_category_names = set()
    for code in codes:
        if code in ITIS_CATEGORIES:
            for o5_subtype in ITIS_CATEGORIES[code]['open511_subtype'].split(','):
                if o5_subtype:
                    subtypes.add(o5_subtype.strip())
            itis_category_names.add(ITIS_CATEGORIES[code]['name'].strip())
        else:
            logger.warning("Categorie ITIS non reconnu: %s", code)
    if subtypes:
        ev['event_subtypes'] = list(subtypes)
    # uncomment to add custom itis_categories field
    # if itis_category_names:
    #     ev['+itis_categories'] = list(itis_category_names)


@task
def _last_update(src, ev):
    timestring = src.findtext('last-update-time')
    if timestring:
        timestamp = dateutil.parser.parse(timestring)
        if not timestamp.tzinfo:
            timestamp = TIMEZONE.localize(timestamp) # make timezone-aware
    else:
        timestamp = datetime.datetime.now(TIMEZONE) # use current time if none in source
    timestamp = timestamp.replace(microsecond=0) # too much detail
    ev['created'] = ev['updated'] = timestamp.isoformat().replace('+00:00', 'Z')

@task
def _roads(src, ev):
    roads = []
    for lol in src.xpath('event-locations/event-Location/location-on-link'):
        name = lol.findtext('link-name')
        if not name:
            continue
        r = {'name': name.strip()}
        fr = lol.findtext('cross-street-name-from')
        if fr:
            r['from'] = fr.strip()
        to = lol.findtext('cross-street-name-to')
        if to and fr and to != fr:
            r['to'] = to.strip()
        roads.append(r)

    # Merge adjacent road segments
    i = 1
    while i < len(roads):
        if roads[i]['name'] == roads[i-1]['name'] and len(roads[i]) == 3 and len(roads[i-1]) == 3:
            if roads[i]['to'] == roads[i-1]['from']:
                roads[i-1]['from'] = roads[i]['from']
                del roads[i]
                continue
            elif roads[i]['from'] == roads[i-1]['to']:
                roads[i-1]['to'] = roads[i]['to']
                del roads[i]
                continue
        i += 1

    if roads:
        ev['roads'] = roads

@task
def _geography(src, ev):
    geoms = [reproject_geometry(g) for g in
        src.xpath('event-locations/event-location/location-on-link/link-geometry')]
    if not geoms:
        raise DataError("Event is missing link-geometry")
    if len(geoms) == 1:
        geom = geoms[0]
    else:
        if len(set(g['type'] for g in geoms)) > 1:
            raise DataError("Event has multiple link-geometries of different types")
        if geoms[0]['type'] not in ('Point', 'LineString', 'Polygon'):
            raise DataError("Unsupported geometry type %s" % geoms[0]['type'])
        geom = {
            'type': 'Multi' + geoms[0]['type'],
            'coordinates': [g['coordinates'] for g in geoms]
        }
    ev['geography'] = geom

INTERVALS_FORMAT = '%Y-%m-%dT%H:%M'
@task
def _schedule(src, ev):
    start_dt = src.findtext('expected-start-time')
    start_dt = dateutil.parser.parse(start_dt) if start_dt else datetime.datetime.now()
    start_dt = start_dt.replace(tzinfo=None)
    end_dt = src.findtext('expected-end-time')
    end_dt = dateutil.parser.parse(end_dt) if end_dt else None
    if end_dt:
        end_dt = end_dt.replace(tzinfo=None)
    if end_dt and end_dt <= start_dt:
        raise Exception("End DT %s before start %s" % (end_dt, start_dt))

    recurrences = src.xpath('recurent-times/recurent-time/schedule-times/text()')
    recurrences = [r for r in recurrences
        if r not in ('00012359', '00002359')] # unnecessary to specify if it's all-day

    if recurrences:
        # Build a recurring schedule
        scheds = []
        start_date, end_date, exceptions = _convert_recurrences(start_dt, end_dt, recurrences)
        for r in recurrences:
            assert len(r) == 8
            sched = {
                'start_date': start_date.isoformat(),
                'daily_start_time': r[0:2] + ':' + r[2:4],
                'daily_end_time': r[4:6] + ':' + r[6:8]
            }
            if end_date:
                sched['end_date'] = end_date.isoformat()
            scheds.append(sched)

        ev['schedule'] = {'recurring_schedules': scheds}
        if exceptions:
            ev['schedule']['exceptions'] = exceptions
    else:
        if (start_dt.hour == 0 and start_dt.minute == 0
                and ((not end_dt) or (end_dt.hour == 23 and end_dt.minute == 59))):
            # An intervals schedule would still be valid here,
            # I just think it's nicer to use a recurring schedule and
            # omit the time if they're not really specific times.
            sched = {
                'start_date': start_dt.date().isoformat()
            }
            if end_dt:
                sched['end_date'] = end_dt.date().isoformat()
            ev['schedule'] = {'recurring_schedules': [sched]}
        else:
            ev['schedule'] = {'intervals':
                [start_dt.strftime(INTERVALS_FORMAT) + '/' +
                    (end_dt.strftime(INTERVALS_FORMAT) if end_dt else '')]}

def _convert_recurrences(start_dt, end_dt, recurrences):
    # Deals with weird edge cases where expected-start-time or expected-end-time intersect
    # with scheduled times, e.g. the event starts at noon on August 1, but in general
    # the event starts at 9am daily.
    # Returns a tuple of start_date, end_date, exceptions, where the dates are datetime.date objects
    # and exceptions is a list of strings in the Open511 exception format
    recurrences = [(datetime.time(int(r[0:2]), int(r[2:4])), datetime.time(int(r[4:6]), int(r[6:8])))
        for r in recurrences]
    recurrences.sort()

    start_time = start_dt.time()
    start_date = start_dt.date()
    exceptions = []
    if start_time > recurrences[-1][1]:
        # Our start time is after the latest in-effect time, so we actually start the next day
        start_date = start_date + datetime.timedelta(days=1)
    elif start_time > recurrences[0][0]:
        exc = [max(start_time, rstart).strftime('%H:%M') + '-' + rend.strftime('%H:%M')
            for rstart, rend in recurrences
            if start_time < rend]
        exceptions.append(start_date.isoformat() + ' ' + ' '.join(exc))

    end_date = None
    if end_dt:
        end_time = end_dt.time()
        end_date = end_dt.date()
        if end_time < recurrences[0][0]:
            # Our end time is before the earliest in-effect time, so we actually end the previous day
            end_date = end_date - datetime.timedelta(days=1)
        elif end_time < recurrences[-1][1]:
            exc = [rstart.strftime('%H:%M') + '-' + min(end_time, rend).strftime('%H:%M')
                for rstart, rend in recurrences
                if end_time > rstart]
            exceptions.append(end_date.isoformat() + ' ' + ' '.join(exc))
    
    return start_date, end_date, exceptions

ARRONDISSEMENTS = [
    ('Ahuntsic-Cartierville', 5882726),
    ('Anjou', 5885369),
    ('Côte-des-Neiges–Notre-Dame-de-Grâce', 5928430),
    ("L'Île-Bizard–Sainte-Geneviève", 6053852),
    ('LaSalle', 6945990),
    ('Lachine', 6545041),
    ('Le Plateau-Mont-Royal', 6052594),
    ('Le Sud-Ouest', 6053102),
    ('Mercier–Hochelaga-Maisonneuve', 6072211),
    ('Montréal-Nord', 6077254),
    ('Outremont', 6095438),
    ('Pierrefonds-Roxboro', 6104320),
    ('Rivière-des-Prairies–Pointe-aux-Trembles', 6123696),
    ('Rosemont–La Petite-Patrie', 6127689),
    ('Saint-Laurent', 6138610),
    ('Saint-Léonard', 6138625),
    ('Verdun', 6173767),
    ('Ville-Marie', 6174337),
    ('Villeray–Saint-Michel–Parc-Extension', 6174349),
]

def _normalize_arrondissement(s):
    return re.sub(r'[\s–-]', '', s.lower())

ARRONDISSEMENTS_LOOKUP = {_normalize_arrondissement(name): (name, geo_id) for name, geo_id in ARRONDISSEMENTS}

@task
def _areas(src, ev):
    area_names = set(
        src.xpath('event-locations/event-location/location-on-link/link-left-jurisdiction-name/text()') +
        src.xpath('event-locations/event-location/location-on-link/link-right-jurisdiction-name/text()')
    )
    areas = []
    for area_name in area_names:
        area_name_normalized = _normalize_arrondissement(area_name)
        if area_name_normalized not in ARRONDISSEMENTS_LOOKUP:
            logger.warning("Arrondissement non reconnu: %s", area_name)
        else:
            areas.append({
                'name': ARRONDISSEMENTS_LOOKUP[area_name_normalized][0],
                'id': 'geonames.org/' + str(ARRONDISSEMENTS_LOOKUP[area_name_normalized][1])
            })
    if areas:
        ev['areas'] = areas

def reproject_geometry(link_geometry):
    """
    Argument: an etree Element for the <link-geometry> tag.
    Returns a GeoJSON dict, reprojected into WGS84.
    """
    src = etree.tostring(link_geometry[0], encoding='unicode')
    cursor = db_conn.cursor()
    cursor.execute("SELECT ST_AsGeoJSON(ST_Transform(ST_GeomFromGML(%s, %s), 4326));",
        (src, SOURCE_SRID))
    result = cursor.fetchone()[0]
    cursor.close()
    return json.loads(result)


def convert_event(src):
    """
    Convert a single lxml Event from the Geo-Trafic source file into an lxml
    Element for an Open511 <event>
    """
    ev = {}
    for conv_func in conv_funcs:
        conv_func(src, ev)
    xml_ev = json_struct_to_xml(ev, root='event',
        custom_namespace='http://ville.montreal.qc.ca/open511-extensions')
    validate_single_item(xml_ev, ignore_missing_urls=True)
    return xml_ev

def geotrafic_to_xml(xml_string):
    """
    Converts a string containing a Geo-Trafic XML document into an lxml Element
    containing an open511 document.
    """
    xml_string = xml_string.replace('<Events xmlns="GeoTrafic">', '<Events>') # simpler
    srcdoc = etree.fromstring(xml_string)
    srcevents = srcdoc.xpath('Event')
    root = get_base_open511_element(lang='fr', version='v1')
    events = etree.Element('events')
    root.append(events)
    for srcevent in srcevents:
        try:
            ev = convert_event(srcevent)
            events.append(ev)
        except:
            logger.exception("Error processing event %s" % srcevent.findtext('event-sid'))
            continue
    return root

def main():
    logging.basicConfig()

    parser = argparse.ArgumentParser(description="Convertir XML Geo-Trafic en format Open511")
    parser.add_argument('fichier', metavar='FICHIER_XML',
        type=str, help="Nom du fichier contenant l'XML Geo-Trafic")
    parser.add_argument('-f', '--format', choices=('xml', 'json'), default='xml',
        help='Format du resultat')
    args = parser.parse_args()
    with open(args.fichier, encoding='utf8') as f:
        data = f.read()
    result = geotrafic_to_xml(data)
    if args.format == 'json':
        result = json.dumps(xml_to_json(result), indent=4)
    else:
        result = etree.tostring(result, encoding='unicode', pretty_print=True)
    sys.stdout.write(result)

if __name__ == '__main__':
    main()
