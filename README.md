# Projet Open511/Géo-Trafic Montreal

[![Build Status](https://api.travis-ci.org/rhymeswithcycle/mtl511.png)](https://travis-ci.org/rhymeswithcycle/mtl511)

## Installation

Vous avez besoin de Python 3.5, et access à un BD PostgreSQL 9.x, avec PostGIS 2.x. Pour l'installation, vous avez aussi besoin de git et de node.js (avec npm).

### Création de l'environnement Python

`pyvenv env-geotrafic` pour créer
`source env-geotrafic/bin/activate` pour activer

On sait que l'environnement Python est activé quand (env-geotrafic) apparaît dans le prompt shell. Il doit être activé avant d'executer les programmes Python.

`mkdir ~/logs` pour creer un endroit pour mettre les logs

### Installation des modules Python

Assurez-vous que `pg_config` est accessible dans le PATH.

`pip install -r requirements.txt`

### Création du BD

Créer un usager et un BD Postgres (e.g. en executant `su postgres` et en suite `createuser open511` et `createdb open511 -O open511`), et initializer PostGIS avec `psql -c "CREATE EXTENSION postgis;" open511`.

### Configuration

Du directoire `geotrafic511`, faire `cp settings.py.example settings.py`, et en suite modifier `settings.py`. Ici on met les informations du connexion BD, et on peut changer plusieurs autres choses.

### Préparation

`python manage.py migrate`
`python manage.py collectstatic`
Pour mettre la jurisdiction Ville de Montréal dans le BD, faire `python manage.py loaddata juridiction_mtl.json`

### Serveur

Si vous voulez éxécuter manuellement le serveur, faire:

`gunicorn -c gunicorn_settings.py geotrafic511.wsgi`

`python import_runner.py` pour ramasser les données

Des fichiers upstart sont en `deployment` -- vous pouvez les copier en `/etc/init` (en modifiant les paths et les noms d'usager), et en suite démarrer les services avec `start open511-web` et `start open511-importer`

### Mettre à jour

Un script, `update_app.sh`, devrait faire les étapes nécessaires. Assurez-vous que l'environnement Python est activé avant d'executer le script.

## Administration

### Configuration de l'interface admin

En `settings.py`, assurez-vous que `ENABLE_ADMIN` est `True`; si vous avez du changer l'option, redémarrer le serveur avec `./restart_server.sh` (ou `kill -HUP `cat gunicorn.pid``).

Établir un mot de passe avec `python manage.py createsuperuser`. En suite, naviguer à `/api/open511/admin/`.

### Supprimer les événements

Via le BD: connecter à Postgres (`psql -U geotrafic511 geotrafic511`, avec le mot de passe BD disponible en `settings.py`), et faire `TRUNCATE TABLE open511_roadevent;`. Ou utiliser l'interface admin.

### Recommencer l'importation de Géo-Trafic

En géneral, l'application demande de l'API Géo-Trafic seulement les événements qui ont changés depuis la dernière demande. Pour demander tous les événements, faire `DELETE FROM open511_importtaskstatus;` en Postgres, ou naviguer au section Import Task Statuses dans l'interface admin et supprimer l'objet trouvé là.

### Redémarrer les services

`./restart_server.sh` pour redémarrer les deux services

`kill -HUP `cat gunicorn.pid`` (dans la même directoire que gunicorn.pid, ~/mtl511) pour redémarrer le serveur web

`killall open511-importer` pour redémarrer le service d'importation

## Conversion manuelle de données XML Géo-Trafic

n.b. ceci n'est pas nécessaire pour faire opérer le serveur Open511

`python geotrafic511/converter.py input.xml > open511_output.xml`

`python geotrafic511/converter.py -f json input.xml > open511_output.json`
