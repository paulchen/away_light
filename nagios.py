#!/usr/bin/python3

import datetime, database, configparser, os, logging, psutil, sys, time

path = os.path.dirname(os.path.abspath(__file__)) + '/'
 
settings = configparser.ConfigParser()
settings.read(path + 'away_light.ini')

logfile = path + 'log/away_light.log'

logger = logging.getLogger()
handler = logging.FileHandler(logfile)
handler.setFormatter(logging.Formatter('%(asctime)s %(name)-12s %(levelname)-8s %(message)s'))
logger.addHandler(handler)
logger.setLevel(logging.DEBUG)

last_update_file = path + 'tmp/last_update'

database.init_db(settings['database'])


def check_last_update(filename):
    if not os.path.exists(filename):
        print('State file %s not found' % (filename, ))
        sys.exit(3)

    stat = os.stat(filename)
    mtime = stat.st_mtime
    age = time.time() - mtime

    warning_limit = 86400
    critical_limit = 2 * warning_limit
    if age > critical_limit:
        print('Last state change is %s seconds ago (more than %s seconds)' % (age, critical_limit))
        sys.exit(2)
    elif age > warning_limit:
        print('Last state change is %s seconds ago (more than %s seconds)' % (age, warning_limit))
        sys.exit(1)


def check_running():
    for pid in psutil.pids():
        p = psutil.Process(pid)
        if p.name() == 'away_light.py':
            return

    print('away_light.py not running');
    sys.exit(2)


def check_future_switch():
    if database.get_next_switch_time() is None:
        print('Next switch time not set')
        sys.exit(2)


check_last_update(last_update_file)
check_running()
check_future_switch()

print('Everything fine, relax.')

