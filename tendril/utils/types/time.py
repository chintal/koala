# Copyright (C) 2015 Chintalagiri Shashank
#
# This file is part of Tendril.
#
# This program is free software: you can redistribute it and/or modify
# it under the terms of the GNU Affero General Public License as published by
# the Free Software Foundation, either version 3 of the License, or
# (at your option) any later version.
#
# This program is distributed in the hope that it will be useful,
# but WITHOUT ANY WARRANTY; without even the implied warranty of
# MERCHANTABILITY or FITNESS FOR A PARTICULAR PURPOSE.  See the
# GNU Affero General Public License for more details.
#
# You should have received a copy of the GNU Affero General Public License
# along with this program.  If not, see <http://www.gnu.org/licenses/>.
"""
This file is part of tendril
See the COPYING, README, and INSTALL files for more information
"""

import arrow.arrow

from unitbase import NumericalUnitBase
from unitbase import parse_none

from decimal import Decimal
from numbers import Number
import re


def parse_frequency(string):
    rex = re.compile(r'^((?P<number>\d+(.\d+)*)(?P<order>[mkMG])?Hz)$')
    try:
        rdict = rex.search(string).groupdict()
        num = Decimal(rdict['number'])
        order = rdict['order']
        if order == 'm':
            return num / 1000
        elif order == 'k':
            return num * 1000
        elif order == 'M':
            return num * 1000000
        elif order == 'G':
            return num * 1000000000
        elif order is None:
            return num
    except:
        raise ValueError


class Frequency(NumericalUnitBase):
    def __init__(self, value):
        _ostrs = ['mHz', 'Hz', 'kHz', 'MHz', 'GHz']
        _dostr = 'Hz'
        _parse_func = parse_frequency
        super(Frequency, self).__init__(value, _ostrs, _dostr, _parse_func)

    def __rdiv__(self, other):
        if isinstance(other, Number):
            return TimeSpan(Decimal(other) / self._value)


class TimeSpan(NumericalUnitBase):
    def __init__(self, value):
        _ostrs = None
        _dostr = None
        _parse_func = parse_none
        if not isinstance(value, Number):
            raise TypeError("Only numerical time spans (in seconds) are supported at this time")
        super(TimeSpan, self).__init__(value, _ostrs, _dostr, _parse_func)

    def __repr__(self):
        return repr(self.timedelta)

    @property
    def timedelta(self):
        seconds = int(self._value)
        microseconds = int((self._value-seconds) * 1000000)
        return TimeDelta(seconds=seconds, microseconds=microseconds)


class TimeStamp(arrow.arrow.Arrow):
    def __sub__(self, other):
        if isinstance(other, TimeDelta):
            return self.clone().replace(years=-other.years,
                                        months=-other.months,
                                        days=-other.days,
                                        hours=-other.hours,
                                        minutes=-other.minutes,
                                        seconds=-other.seconds,
                                        microseconds=-other.microseconds)
        elif isinstance(other, TimeStamp):
            return TimeDelta(years=self.year-other.year,
                             months=self.month-other.month,
                             days=self.day-other.day,
                             hours=self.hour-other.hour,
                             minutes=self.minute-other.minute,
                             seconds=self.second-other.second,
                             microseconds=self.microsecond-other.microsecond)
        else:
            raise NotImplementedError

    def __add__(self, other):
        if isinstance(other, TimeDelta):
            return self.clone().replace(years=other.years,
                                        months=other.months,
                                        days=other.days,
                                        hours=other.hours,
                                        minutes=other.minutes,
                                        seconds=other.seconds,
                                        microseconds=other.microseconds)
        elif isinstance(other, TimeStamp):
            # return self.clone().replace(years=other.year,
            #                             months=other.month,
            #                             days=other.day,
            #                             hours=other.hour,
            #                             minutes=other.minute,
            #                             seconds=other.second,
            #                             microseconds=other.microsecond)
            raise ValueError
        else:
            raise NotImplementedError


class TimeDelta(object):
    def __init__(self, years=0, months=0, days=0, hours=0, minutes=0, seconds=0, microseconds=0):
        self.years = years
        self.months = months
        self.days = days
        self.hours = hours
        self.minutes = minutes
        self.seconds = seconds
        self.microseconds = microseconds

    def __sub__(self, other):
        if isinstance(other, TimeDelta):
            return TimeDelta(years=self.years - other.years,
                             months=self.months - other.months,
                             days=self.days - other.days,
                             hours=self.hours - other.hours,
                             minutes=self.minutes - other.minutes,
                             seconds=self.seconds - other.seconds,
                             microseconds=self.microseconds - other.microseconds)
        else:
            raise NotImplementedError

    def __add__(self, other):
        if isinstance(other, TimeDelta):
            return TimeDelta(years=self.years + other.years,
                             months=self.months + other.months,
                             days=self.days + other.days,
                             hours=self.hours + other.hours,
                             minutes=self.minutes + other.minutes,
                             seconds=self.seconds + other.seconds,
                             microseconds=self.microseconds + other.microseconds)
        else:
            raise NotImplementedError

    def __repr__(self):
        return ':'.join([str(self.years), str(self.months), str(self.days),
                         str(self.hours), str(self.minutes), str(self.seconds),
                         str(self.microseconds)])


timestamp_factory = arrow.ArrowFactory(TimeStamp)
