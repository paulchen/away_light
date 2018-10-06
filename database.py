#!/usr/bin/python3

import enum
from datetime import datetime
from pony.orm import *
from decimal import Decimal
from pony.orm.dbapiprovider import StrConverter


db = Database()


class State(enum.Enum):
    OFF = 0
    ON = 1


class EnumConverter(StrConverter):
    def validate(self, val):
        if not isinstance(val, Enum):
            raise ValueError('Must be an Enum.  Got {}'.format(type(val)))
        return val

    def py2sql(self, val):
        return val.name

    def sql2py(self, value):
        return self.py_type[value]


class SwitchTime(db.Entity):
    id = PrimaryKey(int, auto=True)
    timestamp = Required(datetime)
    state = Required(int)


def init_db(settings):
    db.bind(provider='mysql', host=settings['host'], user=settings['username'], passwd=settings['password'], db=settings['database'])
#    db.provider.converter_classes.append((enum.Enum, EnumConverter))
    sql_debug(True)
    db.generate_mapping(create_tables=True)


@db_session
def save_switch_time(time, state):
    switch_time = SwitchTime(timestamp=time, state=state)


@db_session
def get_next_switch_time():
    query = select((s.timestamp, s.state) for s in SwitchTime if s.timestamp > datetime.now()).order_by(lambda: s.timestamp)
    return query.first()


def save_switch_times(switch_times):
    for switch_time in switch_times:
        save_switch_time(switch_time['time'], switch_time['state'])

