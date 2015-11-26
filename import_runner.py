#!/usr/bin/env python
import os


if __name__ == "__main__":
    os.environ.setdefault("DJANGO_SETTINGS_MODULE", "geotrafic511.settings")

    from open511_server.task_runner import task_runner
    from setproctitle import setproctitle
    setproctitle('open511-importer')
    task_runner()
