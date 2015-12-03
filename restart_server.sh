#!/bin/bash
kill -HUP `cat gunicorn.pid`
killall open511-importer
