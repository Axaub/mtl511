from multiprocessing import cpu_count
import os

bind = '0.0.0.0:' + os.environ.get('OPEN511_PORT', '42000')
workers = cpu_count() + 1
worker_class = 'eventlet'

proc_name = 'open511-web-server'

_log_dir = os.path.join(
    os.path.dirname(os.path.dirname(os.path.abspath(__file__))),
    'logs')

accesslog = os.path.join(_log_dir, 'web_access')
errorlog = os.path.join(_log_dir, 'web_error')
