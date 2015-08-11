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

from decimal import Decimal
from decimal import InvalidOperation

from unitbase import UnitBase
from unitbase import NumericalUnitBase
from unitbase import Percentage
from unitbase import parse_none


def parse_resistance(value):
    num_val = Decimal(value[:-1])
    ostr = value[-1:]
    if ostr == 'm':
        return num_val / 1000
    elif ostr == 'E':
        return num_val
    elif ostr == 'K':
        return num_val * 1000
    elif ostr == 'M':
        return num_val * 1000 * 1000


def parse_capacitance(value):
    num_val = Decimal(value[:-2])
    ostr = value[-2:]
    if ostr == 'pF':
        return num_val / 1000
    elif ostr == 'nF':
        return num_val
    elif ostr == 'uF':
        return num_val * 1000
    elif ostr == 'mF':
        return num_val * 1000 * 1000


def parse_voltage(value):
    value = value.strip()

    try:
        num_val = Decimal(value[:-1])
        ostr = value[-1:]
    except InvalidOperation:
        num_val = Decimal(value[:-2])
        ostr = value[-2:]

    if ostr == 'V':
        return num_val
    elif ostr == 'mV':
        return num_val / 1000
    elif ostr == 'uV':
        return num_val / 1000000
    elif ostr == 'nV':
        return num_val / 1000000000
    elif ostr == 'pV':
        return num_val / 1000000000000
    elif ostr == 'kV':
        return num_val * 1000
    else:
        raise ValueError


def parse_current(value):
    value = value.strip()
    try:
        num_val = Decimal(value[:-1])
        ostr = value[-1:]
    except InvalidOperation:
        num_val = Decimal(value[:-2])
        ostr = value[-2:]

    if ostr == 'A':
        return num_val * 1000
    elif ostr == 'mA':
        return num_val
    elif ostr == 'uA':
        return num_val / 1000
    elif ostr == 'nA':
        return num_val / 1000000
    elif ostr == 'pA':
        return num_val / 1000000000
    elif ostr == 'fA':
        return num_val / 1000000000000
    else:
        raise ValueError


def parse_dbm(value):
    num_val = Decimal(value[:-3])
    ostr = value[-3:]
    if ostr == 'dBm':
        return num_val


def parse_hfe(value):
    num_val = Decimal(value[:-3])
    ostr = value[-3:]
    if ostr == 'HFE':
        return num_val


class Resistance(NumericalUnitBase):
    def __init__(self, value):
        _ostrs = ['m', 'E', 'K', 'M']
        _dostr = 'E'
        _parse_func = parse_resistance
        super(Resistance, self).__init__(value, _ostrs, _dostr, _parse_func)


class Capacitance(NumericalUnitBase):
    def __init__(self, value):
        _ostrs = ['pF', 'nF', 'uF', 'mF']
        _dostr = 'nF'
        _parse_func = parse_capacitance
        super(Capacitance, self).__init__(value, _ostrs, _dostr, _parse_func)


class Voltage(NumericalUnitBase):
    def __init__(self, value):
        _ostrs = ['pV', 'nV', 'uV', 'mV', 'V', 'kV']
        _dostr = 'V'
        _parse_func = parse_voltage
        super(Voltage, self).__init__(value, _ostrs, _dostr, _parse_func)


class VoltageAC(Voltage):
    pass


class VoltageDC(Voltage):
    pass


class DiodeVoltageDC(VoltageDC):
    pass


class Current(NumericalUnitBase):
    def __init__(self, value):
        _ostrs = ['fA', 'pA', 'nA', 'uA', 'mA', 'A']
        _dostr = 'mA'
        _parse_func = parse_current
        super(Current, self).__init__(value, _ostrs, _dostr, _parse_func)


class CurrentAC(Current):
    pass


class CurrentDC(Current):
    pass


class PowerRatio(NumericalUnitBase):
    def __init__(self, value):
        _ostrs = ['dBm']
        _dostr = 'dBm'
        _parse_func = parse_dbm
        super(PowerRatio, self).__init__(value, _ostrs, _dostr, _parse_func)

    def __repr__(self):
        return str(self._value) + self._dostr


class HFE(UnitBase):
    def __init__(self, value):
        _dostr = 'HFE'
        _parse_func = parse_hfe
        super(HFE, self).__init__(value, _dostr, _parse_func)

    def __repr__(self):
        return str(self._value) + self._dostr


class Continuity(UnitBase):
    def __init__(self, value):
        _dostr = None
        _parse_func = parse_none
        super(Continuity, self).__init__(value, _dostr, _parse_func)

    def __repr__(self):
        return str(self._value)


class DutyCycle(Percentage):
    pass
