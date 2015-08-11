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
EntityHub Transforms Module documentation (:mod:`entityhub.transforms`)
=======================================================================
"""

import csv


class TransformFile(object):
    def __init__(self, tfpath):
        self._transform = {}
        self._ideal = {}
        self._status = {}
        with open(tfpath) as f:
            rdr = csv.reader(f)
            for row in rdr:
                self._transform[row[0]] = row[1]
                self._ideal[row[0]] = row[2]
                try:
                    self._status[row[0]] = row[3]
                except IndexError:
                    self._status[row[0]] = ''

    def get_canonical_repr(self, contextual):
        return self._transform[contextual]

    def get_ideal_repr(self, contextual):
        return self._ideal[contextual]

    def get_status(self, contextual):
        return self._status[contextual]

    def get_contextual_repr(self, canonical):
        for (k, v) in self._transform:
            if v == canonical:
                return k
        return None

    def has_contextual_repr(self, contextual):
        if contextual in self._transform.keys():
            return True
        else:
            return False
