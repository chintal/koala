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

import math

from decimal import Decimal
from lengths import Length


class CartesianPoint(object):
    unit = 'mm'

    def __init__(self, x, y):
        self.x = self._norm_repr(x)
        self.y = self._norm_repr(y)

    @staticmethod
    def _norm_repr(v):
        return Decimal(v)

    def __eq__(self, other):
        if self.x == other.x and self.y == other.y:
            return True
        else:
            return False


class CartesianLineSegment(object):
    def __init__(self, p1, p2):
        self.p1 = p1
        self.p2 = p2
        if p1 == p2:
            raise Exception("Line can't have zero length")
        if p1.unit != p2.unit:
            raise ValueError

    def x(self, t):
        return self.p1.x + t * (self.p2.x - self.p1.x)

    def y(self, t):
        return self.p1.y + t * (self.p2.y - self.p1.y)

    def t_x(self, x):
        if self.p1.x != self.p2.x:
            return (Decimal(x) - self.p1.x) / (self.p2.x - self.p1.x)
        else:
            raise ZeroDivisionError

    def t_y(self, y):
        if self.p1.y != self.p2.y:
            return (Decimal(y) - self.p1.y) / (self.p2.y - self.p1.y)
        else:
            raise ZeroDivisionError

    def length(self):
        return Length(str(math.sqrt((self.p2.x - self.p1.x)**2 + (self.p2.y - self.p1.y)**2)) + self.p1.unit)

    def __contains__(self, p):
        try:
            t = self.t_x(p.x)
            if 0 <= t <= 1:
                try:
                    if t == self.t_y(p.y):
                        return True
                    else:
                        return False
                except ZeroDivisionError:
                    if p.y == self.p1.y:
                        return True
            else:
                return False
        except ZeroDivisionError:
            t = self.t_y(p.y)
            if 0 <= t <= 1 and p.x == self.p1.x:
                return True
            else:
                return False
