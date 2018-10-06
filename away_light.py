#!/usr/bin/python3

import datetime, random, astral, pytz, holidays, database, threading, fileinput, configparser, os, subprocess

path = os.path.dirname(os.path.abspath(__file__)) + '/'
 
settings = configparser.ConfigParser()
settings.read(path + 'away_light.ini')


def calculate_switch_times(start, end, probability_on, probability_off, min_on, min_off):
    switch_times = []
    if start >= end:
        return switch_times

    pos = start
    state = False

    while pos < end:
        diff = 1
        if not state and random.random() < probability_on:
            state = True
            switch_times.append({'time': pos, 'state': 1})
            diff = min_on
        elif state and random.random() < probability_off:
            state = False
            switch_times.append({'time': pos, 'state': 0})
            diff = min_off

        pos = pos + datetime.timedelta(minutes = diff)

    if state:
        state = False
        switch_times.append({'time': pos, 'state': 0})

    return switch_times
        

def calculate_todays_switch_times():
    a = astral.Astral()
    city = a['Vienna']


    today = datetime.date.today()
    now = datetime.datetime.now(pytz.timezone(city.timezone))
    if now.hour > 3:
        today = today + datetime.timedelta(days = 1)
        now = now + datetime.timedelta(days = 1)
    print('Calculating switch times for %s' % (today, ))


    sun = city.sun(date=today, local=True)


    today_holiday = today in holidays.Austria()
    tomorrow_holiday = today + datetime.timedelta(days = 1) in holidays.Austria()

    today_weekend = today.isoweekday() in (6, 7)
    tomorrow_weekend = today.isoweekday() in (5, 6)

    today_off = today_holiday or today_weekend
    tomorrow_off = tomorrow_holiday or tomorrow_weekend


    if today_off:
        morning_start = now.replace(hour=9, minute=0, second=0, microsecond=0)
    else:
        morning_start = now.replace(hour=5, minute=30, second=0, microsecond=0)
    morning_end = sun['sunrise'] + datetime.timedelta(hours = 1)

    morning_start = morning_start + datetime.timedelta(minutes = random.randrange(-30, 60))
    morning_end = morning_end + datetime.timedelta(minutes = random.randrange(-20, 20))


    evening_start = sun['sunset'] - datetime.timedelta(hours = 1)
    evening_end = now.replace(hour=23, minute=0, second=0, microsecond=0)
    if tomorrow_off:
        evening_end = evening_end + datetime.timedelta(hours = 2)

    evening_start = evening_start + datetime.timedelta(minutes = random.randrange(-30, 90))
    evening_end = evening_end + datetime.timedelta(minutes = random.randrange(-60, 60))


    switch_times = []
    switch_times.extend(calculate_switch_times(morning_start, morning_end, .2, .05, 20, 15))
    switch_times.extend(calculate_switch_times(evening_start, evening_end, .2, .05, 20, 15))

    return switch_times


def switch(parameter):
    subprocess.call(['pilight-send', '-p', 'elro_800_switch', '-s', settings['system_code'], '-u', settings['unit_code'], parameter])


def switch_off():
    switch('-t')
    print('Turning OFF at %s' % (datetime.datetime.now(), ))
    schedule_next_switch()


def switch_on():
    switch('-f')
    print('Turning ON at %s' % (datetime.datetime.now(), ))
    schedule_next_switch()


def schedule_next_switch():
    next_switch_time = database.get_next_switch_time()
    if next_switch_time is None:
        switch_times = calculate_todays_switch_times()
        database.save_switch_times(switch_times)
        next_switch_time = database.get_next_switch_time()

    now = datetime.datetime.now()
    run_at = next_switch_time[0]
    delay = (run_at - now).total_seconds()

    print('Current time: %s' % (datetime.datetime.now(), ))
    print('Next switch time: %s' % (run_at, ))
    print('Delay: %s seconds' % (delay, ))

    if next_switch_time[1] == 1:
        print('Next switch will be to ON')
        threading.Timer(delay, switch_on).start()
    else:
        print('Next switch will be to OFF')
        threading.Timer(delay, switch_off).start()


database.init_db(settings['database'])

schedule_next_switch()

