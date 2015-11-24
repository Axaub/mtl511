from multiprocessing import cpu_count
from os import environ

bind = '0.0.0.0:' + environ.get('OPEN511_PORT', '42000')
workers = cpu_count() + 1
worker_class = 'eventlet'
