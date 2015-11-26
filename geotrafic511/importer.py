import logging

from django import db

from lxml import etree
import requests

from open511_server.importer import BaseImporter
from . import converter

logger = logging.getLogger(__name__)

class GeoTraficImporter(BaseImporter):

    default_language = 'fr'

    def fetch(self):
        url = self.opts['URL']
        if self.status.get('max_updated'):
            url += self.status['max_updated']
        else:
            url += '2000-01-01'
        resp = requests.get(url)
        resp.raise_for_status()

        xml_string = resp.content.decode('utf8').replace('<Events xmlns="GeoTrafic">', '<Events>')
        root = etree.fromstring(xml_string)

        try:
            self.status['max_updated'] = max(root.xpath('Event/last-update-time/text()'))
        except ValueError:
            # Empty list of events, presumably
            pass

        for ev in root.xpath('Event'):
            yield ev

    def convert(self, input_document):
        try:
            yield converter.convert_event(input_document, db.connection)
        except Exception as e:
            logger.exception("{} importing event-sid {}".format(e.__class__.__name__,
                input_document.findtext('event-sid')))

