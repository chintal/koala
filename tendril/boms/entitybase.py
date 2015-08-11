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


class EntityBase(object):
    """ Placeholder class for potentially track-able objects.

        Depending on the implementation used, this class should inherit from
        an external class built for this purpose instead of from ``object``.

    """
    def __init__(self):
        self._defined = False
        self._refdes = ''

    def define(self, *args, **kwargs):
        raise NotImplementedError

    @property
    def defined(self):
        """ State of the component. The component should be used only when
        it is fully defined.

        This is a read-only property.
        """
        return self._defined

    @property
    def ident(self):
        raise NotImplementedError

    @property
    def refdes(self):
        """ Refdes string. """
        return self._refdes

    @refdes.setter
    def refdes(self, value):
        self._refdes = value


class EntityGroupBase(EntityBase):
    def __init__(self, groupname, contextname=''):
        super(EntityGroupBase, self).__init__()
        self.contextname = ''
        self.groupname = ''
        self.complist = []
        self.define(contextname, groupname)

    def insert(self, item):
        raise NotImplementedError

    @property
    def ident(self):
        return (self.contextname + ' ' + self.groupname).strip()

    def define(self, contextname, groupname):
        self.contextname = contextname
        self.groupname = groupname
        self._defined = True


class EntityBomBase(EntityBase):
    def __init__(self):
        super(EntityBomBase, self).__init__()
        self.grouplist = []

    @property
    def ident(self):
        raise NotImplementedError

    def create_output_bom(self, *args, **kwargs):
        raise NotImplementedError

    def define(self, *args, **kwargs):
        raise NotImplementedError
