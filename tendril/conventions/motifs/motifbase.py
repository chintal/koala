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


class MotifBase(object):
    columns = ['refdes', 'device', 'value', 'footprint',
               'fillstatus', 'group', 'package', 'status']

    def __init__(self, identifier):
        self._type = None
        self._ident = None
        self._elements = []
        self.refdes = identifier

    @property
    def refdes(self):
        return self._type + '.' + self._ident

    @refdes.setter
    def refdes(self, value):
        value = value.split(':')[0]
        self._type, self._ident = value.split('.')

    def _line_generator(self):
        for elem in self._elements:
            yield elem

    def get_configdict_stub(self):
        raise NotImplementedError

    def configure(self, configdict):
        raise NotImplementedError

    def get_line_gen(self):
        return self._line_generator()

    def get_elem_by_idx(self, idx):
        for elem in self._elements:
            if elem.data['motif'].split(':')[1] == idx:
                return elem
        raise KeyError(self.refdes, idx)

    def add_element(self, bomline):
        self._elements.append(bomline)

    def validate(self):
        raise NotImplementedError

    def __repr__(self):
        return "MOTIF OBJECT : " + self.refdes

    @property
    def listing(self):
        raise NotImplementedError
