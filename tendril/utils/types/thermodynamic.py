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


from decimal import Decimal
from unitbase import NumericalUnitBase


def parse_temperature(value):
    num_val = Decimal(value[:-1])
    ostr = value[-1:]
    if ostr == 'C':
        return num_val + Decimal('273.14')
    elif ostr == 'K':
        return num_val
    elif ostr == 'F':
        return ((num_val - 32) * 5) / 9


class Temperature(NumericalUnitBase):
    def __init__(self, value):
        _ostrs = ['C', 'F', 'K']
        _dostr = 'K'
        _parse_func = parse_temperature
        super(Temperature, self).__init__(value, _ostrs, _dostr, _parse_func)

    def __repr__(self):
        return str(self._value) + self._dostr
