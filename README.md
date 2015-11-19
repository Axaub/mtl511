# Projet Open511/Géo-Trafic Montreal

[![Build Status](https://api.travis-ci.org/rhymeswithcycle/mtl511.png)](https://travis-ci.org/rhymeswithcycle/mtl511)

## Conversion de données

### Installation

Vous avez besoin de Python 3.5, et access à un BD PostGIS. (Pour la conversion de données, rien n'est écrit au BD. PostGIS est utilisé pour transformer les coordonnées géospatiales.)

Créer et activer [un environnement Python](https://docs.python.org/3/library/venv.html); sur une système Unix, on fait ça avec `pyvenv geotrafic` pour créer et `source geotrafic/bin/activate` pour activer. En suite, installer les modules Python: `pip install -r requirements.txt`

Configurer l'acces au BD. Mettre un [connection string PostgreSQL](http://initd.org/psycopg/docs/module.html#psycopg2.connect) dans le variable d'environnement POSTGRES_DSN.

### Utilisation

`python geotrafic_convert.py input.xml > open511_output.xml`

`python geotrafic_convert.py -f json input.xml > open511_output.json`
