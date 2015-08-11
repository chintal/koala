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


from tendril.utils.types.time import timestamp_factory
from tendril.utils.types.time import TimeStamp
from tendril.utils.types.time import TimeDelta

from collections import deque
import copy


class SignalBase(object):
    def __init__(self, unitclass):
        self._unitclass = unitclass

    @property
    def unitclass(self):
        return self._unitclass


class SignalErrorBar(object):
    def __init__(self, quantization=None, noise_floor=None, error_pc=None):
        self.quantization = quantization
        self.noise_floor = noise_floor
        self.error_pc = error_pc


class SignalPoint(SignalBase):
    def __init__(self, unitclass, value, ts=None):
        super(SignalPoint, self).__init__(unitclass)

        if not isinstance(value, unitclass):
            self.value = unitclass(value)
        else:
            self.value = value

        if ts is None:
            self.timestamp = timestamp_factory.now()
        else:
            self.timestamp = ts

        self._error_bar = None

    @property
    def error_bar(self):
        return self._error_bar

    @error_bar.setter
    def error_bar(self, value):
        self._error_bar = value

    def __repr__(self):
        return "<SignalPoint at " + repr(self.timestamp) + " :: " + repr(self.value) + " >"


class SignalWave(SignalBase):
    def __init__(self, unitclass, points=None, spacing=None, ts0=None,
                 interpolation="piecewise_linear", buffer_size=None,
                 use_point_ts=True):
        super(SignalWave, self).__init__(unitclass)

        self._buffer_size = buffer_size
        self._use_point_ts = use_point_ts

        if spacing is not None:
            if not isinstance(spacing, TimeDelta):
                raise TypeError("spacing must be an instance of TimeDelta")
            self._spacing = spacing

        if ts0 is not None:
            if not isinstance(ts0, TimeStamp):
                raise TypeError("ts0 must be an instance of TimeStamp")
            self._ts0 = ts0
        else:
            self._ts0 = timestamp_factory.now()

        if points and isinstance(points, deque):
            if isinstance(points[0], tuple):
                self._points = points
            else:
                if not self._use_point_ts:
                    self._points = deque([(ts0 + idx*spacing, point) for idx, point in enumerate(points)],
                                         maxlen=buffer_size)
                else:
                    self._points = deque([(point.timestamp, point) for point in points],
                                         maxlen=buffer_size)
        else:
            self._points = deque(maxlen=buffer_size)

        self._interpolation = interpolation

    @property
    def last_timestamp(self):
        if len(self._points) == 0:
            if self._ts0 is not None:
                return self._ts0 - self._spacing
            else:
                return None
        return self._points[-1][0]

    @property
    def points(self):
        return sorted(self._points, key=lambda x: x[0])

    def add_point(self, point, ts=None):
        if point.unitclass != self.unitclass:
            raise TypeError
        if ts is None:
            if self._use_point_ts is False:
                if self.last_timestamp is None:
                    self._ts0 = timestamp_factory.now()
                ts = self.last_timestamp + self._spacing
            elif point.timestamp is not None:
                if self.last_timestamp is None:
                    self._ts0 = point.timestamp
                ts = point.timestamp
        if ts is None:
            raise ValueError
        self._points.append((ts, point))

    def __add__(self, other):
        if isinstance(other, SignalWave):
            if self.unitclass != other.unitclass:
                raise TypeError
            rval = copy.copy(self)
            rval.extend(other._points)
            return rval
        elif isinstance(other, SignalPoint):
            self.add_point(other)
            return self
        else:
            raise NotImplementedError

    def __radd__(self, other):
        if isinstance(other, SignalWave):
            if self.unitclass != other.unitclass:
                raise TypeError
            return self._points.extendleft(reversed(other._points))
        elif isinstance(other, SignalPoint):
            if self.unitclass != other.unitclass:
                raise TypeError
            return self._points.appendleft(other)
        else:
            raise NotImplementedError

    def __len__(self):
        return len(self._points)

    def __getitem__(self, item):
        return self._points.__getitem__(item)

    def __setitem__(self, key, value):
        return self._points.__setitem__(key, value)

    def __delitem__(self, key):
        return self._points.__delitem__(key)

    def __iter__(self):
        return self._points.__iter__()

    def __reversed__(self):
        return self._points.__reversed__()

    def __contains__(self, item):
        return self._points.__contains__(item)

    def clear(self):
        return self._points.clear()

    def popleft(self, *args, **kwargs):
        return self._points.popleft(*args, **kwargs)

    def pop(self, *args, **kwargs):
        return self._points.pop(*args, **kwargs)

    def append(self, *args, **kwargs):
        return self._points.append(*args, **kwargs)

    def appendleft(self, *args, **kwargs):
        return self._points.appendleft(*args, **kwargs)

    def extend(self, *args, **kwargs):
        return self._points.extend(*args, **kwargs)

    def extendleft(self, *args, **kwargs):
        return self._points.extendleft(*args, **kwargs)
