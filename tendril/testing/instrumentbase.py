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


class InstrumentChannelBase(object):
    def __init__(self, parent):
        self._parent = parent

    @property
    def is_enabled(self):
        if self in self._parent.channels:
            return True
        else:
            return False


class InstrumentInputChannelBase(InstrumentChannelBase):
    def __init__(self, parent):
        super(InstrumentInputChannelBase, self).__init__(parent)

    def get(self):
        raise NotImplementedError


class InstrumentOutputChannelBase(InstrumentChannelBase):
    def __init__(self, parent):
        super(InstrumentOutputChannelBase, self).__init__(parent)

    def set(self, signal):
        raise NotImplementedError


class InstrumentBase(object):
    def __init__(self, channels=None):
        self._ident = None
        self._sno = None
        self._channels = channels
        self._configurations = []

        self._connected = None
        self._consumers = []

    def consumer_register(self, consumer):
        if self._connected is not True:
            try:
                self.connect()
            except NotImplementedError:
                pass
        self._consumers.append(consumer)

    def consumer_done(self, consumer):
        self._consumers.remove(consumer)
        if len(self._consumers) == 0:
            try:
                self.disconnect()
            except NotImplementedError:
                pass

    @property
    def connected(self):
        return self._connected

    def connect(self):
        raise NotImplementedError

    def disconnect(self):
        raise NotImplementedError

    def _detect(self):
        raise NotImplementedError

    def configure(self, configuration):
        raise NotImplementedError

    @property
    def configurations(self):
        return self._configurations

    @property
    def channels(self):
        return self._channels

    @property
    def ident(self):
        if self._sno is not None:
            return str(self._ident) + ' ' + str(self._sno)
        else:
            return self._ident
