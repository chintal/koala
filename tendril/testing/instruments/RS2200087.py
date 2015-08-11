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
RadioShack 2200087 DMM Interface Module (:mod:`tendril.testing.instruments.RS2200087`)
====================================================================================

This module provides the instrument object for RadioShack's 2200087 Digital
Multimeter with PC interface. It uses the :mod:`driver2200087` module to
handle the communication with the instrument, while subclassing the Twisted
protocol of that module to provide one which produces
:class:`tendril.utils.types.signalbase.SignalPoint` and
:class:`tendril.utils.types.signalbase.SignalWave` objects instead, which contain
Type objects from the :mod:`tendril.utils.types` module. This allows seamless
integration with Tendril's :mod:`tendril.testing` module.

.. rubric:: Usage example

>>> from crochet import setup
>>> setup()
>>> from tendril.testing.instruments import get_instrument_object
>>> o = get_instrument_object('RS2200087')
>>> o.channel.get()
>>> o.channel.reset_wave()
>>> wave = o.channel.get_next_chunk()
>>> wave += o.channel.get_next_chunk()

.. rubric:: Module Contents

.. rubric:: Classes

.. autosummary::

    InstrumentRS2200087
    DMMInputChannel
    TendrilProtocol2200087
    TendrilFactory2200087
    factory


.. rubric:: Processors

.. autosummary::

    rex_list
    voltage_processor
    resistance_processor
    capacitance_processor
    frequency_processor
    time_processor
    current_processor
    power_processor
    duty_processor
    hfe_processor
    continuity_processor

"""

from tendril.utils import log
logger = log.get_logger(__name__, log.DEFAULT)

import re
import copy
from collections import deque

from driver2200087.runner import InstProtocol2200087
from driver2200087.runner import InstInterface2200087
from driver2200087.runner import InstFactory2200087

from tendril.utils.types.signalbase import SignalPoint
from tendril.utils.types.signalbase import SignalWave

from tendril.utils.types.time import TimeDelta
from tendril.utils.types.time import timestamp_factory

from tendril.utils.types import electromagnetic
from tendril.utils.types import thermodynamic
from tendril.utils.types import time
from tendril.utils.types.unitbase import DummyUnit

from tendril.testing.instrumentbase import InstrumentBase
from tendril.testing.instrumentbase import InstrumentInputChannelBase

from decimal import Decimal
from decimal import InvalidOperation


def voltage_processor(m):
    """
    Processor that converts a regex match of a Voltage string from :mod:`driver2200087.serialDecoder`
    and returns a string compatible with Tendril Unit Types

    :param m: :class:`re.match` object from one of the Voltage regexs in :data:`rex_list`
    :return: String compatible with the :class:`tendril.utils.types.electromagnetic.Voltage` class and its subclasses
    :rtype: str

    """
    num = m.group('number')
    try:
        rng = m.group('range')
        if rng == 'K':
            rng = 'k'
    except IndexError:
        rng = ''
    rval = num + rng + 'V'
    return rval


def resistance_processor(m):
    """
    Processor that converts a regex match of a Resistance string from :mod:`driver2200087.serialDecoder`
    and returns a string compatible with Tendril Unit Types

    :param m: :class:`re.match` object from one of the Resistance regexs in :data:`rex_list`
    :return: String compatible with the :class:`tendril.utils.types.electromagnetic.Resistance` class and its subclasses
    :rtype: str

    """
    num = m.group('number')
    try:
        rng = m.group('range')
        if rng is None:
            rng = ''
        if rng == 'K':
            rng = 'k'
    except IndexError:
        rng = 'E'
    rval = num + rng
    return rval


def capacitance_processor(m):
    """
    Processor that converts a regex match of a Capacitance string from :mod:`driver2200087.serialDecoder`
    and returns a string compatible with Tendril Unit Types

    :param m: :class:`re.match` object from one of the Capacitance regexs in :data:`rex_list`
    :return: String compatible with the :class:`tendril.utils.types.electromagnetic.Capacitance` class and its subclasses
    :rtype: str

    """
    num = m.group('number')
    rng = m.group('range')
    if rng is None:
        rng = ''
    rval = num + rng + 'F'
    return rval


def frequency_processor(m):
    """
    Processor that converts a regex match of a Frequency string from :mod:`driver2200087.serialDecoder`
    and returns a string compatible with Tendril Unit Types

    :param m: :class:`re.match` object from one of the Frequency regexs in :data:`rex_list`
    :return: String compatible with the :class:`tendril.utils.types.time.Frequency` class and its subclasses
    :rtype: str

    """
    num = m.group('number')
    try:
        rng = m.group('range')
        if rng is None:
            rng = ''
    except IndexError:
        rng = ''
    rval = num + rng + 'Hz'
    return rval


def time_processor(m):
    """
    Processor that converts a regex match of a Time string from :mod:`driver2200087.serialDecoder`
    and returns a string compatible with Tendril Unit Types

    :param m: :class:`re.match` object from one of the Time regexs in :data:`rex_list`
    :return: String compatible with the :class:`tendril.utils.types.time.TimeSpan` class and its subclasses
    :rtype: str

    """
    num = Decimal(m.group('number'))
    try:
        rng = m.group('range')
        if rng is None:
            rng = 1
        elif rng == 'm':
            rng = Decimal(1)/1000
        elif rng == 'u':
            rng = Decimal(1)/1000000
        elif rng == 'n':
            rng = Decimal(1)/1000000000
    except IndexError:
        rng = 1
    rval = num * rng
    return rval


def current_processor(m):
    """
    Processor that converts a regex match of a Current string from :mod:`driver2200087.serialDecoder`
    and returns a string compatible with Tendril Unit Types

    :param m: :class:`re.match` object from one of the Current regexs in :data:`rex_list`
    :return: String compatible with the :class:`tendril.utils.types.electromagnetic.Current` class and its subclasses
    :rtype: str

    """
    num = m.group('number')
    try:
        rng = m.group('range')
        if rng == 'K':
            rng = 'k'
    except IndexError:
        rng = ''
    rval = num + rng + 'A'
    return rval


def power_processor(m):
    """
    Processor that converts a regex match of a PowerRatio string from :mod:`driver2200087.serialDecoder`
    and returns a string compatible with Tendril Unit Types

    :param m: :class:`re.match` object from one of the PowerRatio regexs in :data:`rex_list`
    :return: String compatible with the :class:`tendril.utils.types.electromagnetic.PowerRatio` class and its subclasses
    :rtype: str

    """
    return m.group('number') + 'dBm'


def hfe_processor(m):
    """
    Processor that converts a regex match of a HFR string from :mod:`driver2200087.serialDecoder`
    and returns a string compatible with Tendril Unit Types

    :param m: :class:`re.match` object from one of the HFE regexs in :data:`rex_list`
    :return: String compatible with the :class:`tendril.utils.types.electromagnetic.HFE` class and its subclasses
    :rtype: str

    """
    return m.group('number') + 'HFE'


def duty_processor(m):
    """
    Processor that converts a regex match of a DutyCycle string from :mod:`driver2200087.serialDecoder`
    and returns a string compatible with Tendril Unit Types

    :param m: :class:`re.match` object from one of the DutyCycle regexs in :data:`rex_list`
    :return: String compatible with the :class:`tendril.utils.types.electromagnetic.DutyCycle` class and its subclasses
    :rtype: str

    """
    return m.group('number') + '%'


def continuity_processor(m):
    """
    Processor that converts a regex match of a Continuity string from :mod:`driver2200087.serialDecoder`
    and returns a string compatible with Tendril Unit Types

    :param m: :class:`re.match` object from one of the Continuity regexs in :data:`rex_list`
    :return: String compatible with the :class:`tendril.utils.types.electromagnetic.Continuity` class and its subclasses
    :rtype: str

    """
    rval = 'CLOSED'
    if m.group('string') == '0PEN':
        rval = 'OPEN'
    return rval

#: List of regular expressions, each of which matches the string for one type of data from
#: :mod:`driver2200087.serialDecoder`. Each element of the list is a `tuple`, containing the
#: following elements:
#:
#: 0. Tendril type class from :mod:`tendril.utils.types` which is applicable to the data point.
#: 1. The compiled regular expression.
#: 2. The applicable processor, which acts on the match object to produce a string. If the
#:    processor is None, then the named match group 'string' is used to instantiate the
#:    appropriate unit class.
#:
rex_list = [(thermodynamic.Temperature,
             re.compile(ur'^(?P<string>[-?[0-9\\.]+[CFK])(?P<HOLD> HOLD)?$'),
             None),
            (electromagnetic.VoltageDC,
             re.compile(ur'^(?P<number>[-?[0-9\\.]+)(?P<AUTO> AUTO)?(?P<HOLD> HOLD)?( (?P<range>[munKM]) \(1e(?P<power>-?[\d]+)\))? VOLTS$'),
             voltage_processor),
            (electromagnetic.VoltageAC,
             re.compile(ur'^(?P<number>[-?[0-9\\.]+) AC(?P<AUTO> AUTO)?(?P<HOLD> HOLD)?( (?P<range>[munKM]) \(1e(?P<power>-?[\d]+)\))? VOLTS$'),
             voltage_processor),
            (electromagnetic.CurrentDC,
             re.compile(ur'^(?P<number>[-?[0-9\\.]+)(?P<AUTO> AUTO)?(?P<HOLD> HOLD)?( (?P<range>[munKM]) \(1e(?P<power>-?[\d]+)\))? AMPS$'),
             current_processor),
            (electromagnetic.CurrentAC,
             re.compile(ur'^(?P<number>[-?[0-9\\.]+) AC(?P<AUTO> AUTO)?(?P<HOLD> HOLD)?( (?P<range>[munKM]) \(1e(?P<power>-?[\d]+)\))? AMPS$'),
             current_processor),
            (electromagnetic.Continuity,
             re.compile(ur'^(?P<string>0PEN) CONTINUITY(?P<HOLD> HOLD)?$'),
             continuity_processor),
            (electromagnetic.DiodeVoltageDC,
             re.compile(ur'^(?P<number>[-?[0-9\\.]+) DIODE(?P<HOLD> HOLD)? VOLTS$'),
             voltage_processor),
            (electromagnetic.Resistance,
             re.compile(ur'^(?P<number>[-?[0-9\\.]+)(?P<AUTO> AUTO)?(?P<HOLD> HOLD)?( (?P<range>[munKM]) \(1e(?P<power>-?[\d]+)\))? OHMS$'),
             resistance_processor),
            (electromagnetic.Capacitance,
             re.compile(ur'^(?P<number>[-?[0-9\\.]+)(?P<AUTO> AUTO)?(?P<HOLD> HOLD)?( (?P<range>[munKM]) \(1e(?P<power>-?[\d]+)\))? FARADS$'),
             capacitance_processor),
            (time.Frequency,
             re.compile(ur'^(?P<number>[-?[0-9\\.]+)(?P<AUTO> AUTO)?(?P<HOLD> HOLD)? Hz$'),
             frequency_processor),
            (electromagnetic.PowerRatio,
             re.compile(ur'^(?P<number>[-?[0-9\\.]+)(?P<HOLD> HOLD)? dBm$'),
             power_processor),
            (electromagnetic.DutyCycle,
             re.compile(ur'^(?P<number>[-?[0-9\\.]+)(?P<AUTO> AUTO)(?P<HOLD> HOLD)? Percent$'),
             duty_processor),
            (time.TimeSpan,
             re.compile(ur'^(?P<number>[-?[0-9\\.]+)(?P<AUTO> AUTO)?(?P<HOLD> HOLD)? SECONDS( (?P<range>[mun]) \(1e(?P<power>-?[\d]+)\))?$'),
             time_processor),
            (electromagnetic.HFE,
             re.compile(ur'^(?P<number>[-?[0-9\\.]+)(?P<HOLD> HOLD)? HFE$'),
             hfe_processor),
            ]

# TODO Handle closed continuty
# TODO Handle open diode
# TODO Handle open resistor
# TODO Handle shorted capacitor
# TODO Handle Logic


class TendrilProtocol2200087(InstProtocol2200087):
    """
    This subclasses the twisted protocol from :mod:`driver2200087.runner`
    which handles serial communications with 2200087 multimeters. It produces
    :class:`tendril.utils.types.signalbase.SignalPoint` and
    :class:`tendril.utils.types.signalbase.SignalWave` objects instead of strings and
    deque objects, which contain Type objects from the
    :mod:`tendril.utils.types` module.

    This protocol exists and operates within the context of a twisted reactor.
    Applications themselves built on twisted should be able to simply import this
    protocol (or its factory).

    Synchronous / non-twisted applications should directly use the
    :class:`driver2200087.runner.InstInterface2200087` class instead, and pass this
    protocol's factory to modify its behavior.

    :param port: Port on which the device is connected. Default '/dev/ttyUSB0'.
    :type port: str
    :param buffer_size: Length of the point buffer in the protocol.
    :type buffer_size: int
    """
    def __init__(self, port, buffer_size):
        InstProtocol2200087.__init__(self, port=port, buffer_size=buffer_size)

    def reset_buffer(self, unitclass=DummyUnit):
        """
        Resets the point buffer to a new :class:`tendril.utils.types.signalbase.SignalWave`
        with the unitclass as specified by the parameter. Any data presently within it
        will be lost.

        :param unitclass: Class of Unit that the Wave points are composed of.

        """
        logger.debug("Resetting buffer to type : " + repr(unitclass))
        self.point_buffer = SignalWave(unitclass,
                                       spacing=TimeDelta(microseconds=100000),
                                       ts0=timestamp_factory.now(),
                                       buffer_size=1000,
                                       use_point_ts=False)

    def next_chunk(self):
        """

        :returns: The next chunk of data points in the form of a SignalWave
        :rtype: :class:`tendril.utils.types.signalbase.SignalWave`

        """
        rval = copy.copy(self.point_buffer)
        self.point_buffer = SignalWave(rval.unitclass,
                                       points=deque([rval.pop()], maxlen=rval._buffer_size),
                                       spacing=rval._spacing,
                                       ts0=rval._ts0,
                                       buffer_size=rval._buffer_size,
                                       use_point_ts=rval._use_point_ts)
        return rval

    @staticmethod
    def _get_point(string):
        """
        Processes a string returned by :mod:`driver2200087.serialDecoder` and converts it into
        a :class:`tendril.utils.types.signalbase.SignalPoint` instance composed of the correct
        Unit class.

        :return:  SignalPoint composed of the correct type and value from the string
        :rtype: :class:`tendril.utils.types.signalbase.SignalPoint`

        .. seealso:: :data:`rex_list`

        """
        if string is None:
            return SignalPoint(DummyUnit, None)
        for rex in rex_list:
            m = rex[1].match(string.strip())
            if m is not None:
                if rex[2] is not None:
                    rstring = rex[2](m)
                else:
                    rstring = m.group('string')
                try:
                    return SignalPoint(rex[0], rstring)
                except (InvalidOperation, ValueError):
                    logger.error("Unable to make unit from string : " + rstring + " : " + repr(rex[0]))
                    return SignalPoint(rex[0], 0)
        raise ValueError("String not recognized : " + string)

    def frame_received(self, frame):
        """
        Re-implements the Base class's frame_received function, producing SignalPoints instead.
        When a signal point of a different type as the point buffer is encountered, it resets
        the point buffer and initializes it to the new type.

        .. seealso:: :meth:`_get_point`

        """
        frame = [byte.encode('hex') for byte in frame]
        chunk = ' '.join(frame)
        string = self._frame_processor(chunk)
        point = self._get_point(string)
        if not point.unitclass == self.point_buffer.unitclass:
            self.reset_buffer(point.unitclass)
        self.point_buffer.add_point(point)


class TendrilFactory2200087(InstFactory2200087):
    """
    This factory produces protocols integrated with Tendril unit classes,
    producing SignalPoints and SignalWaves instead of strings.

    See the :class:`driver2200087.runner.InstFactory2200087` documentation
    for more detailed information.
    """
    def buildProtocol(self, port='/dev/ttyUSB0', buffer_size=100):
        """
        This function returns a TendrilProtocol2200087 instance, bound to the
        port specified by the param port.

        :param port: Serial port identifier to which the device is connected
        :type port: str
        :param buffer_size: Length of the point buffer in the protocol. Default 100.
        :type buffer_size: int
        """
        instance = TendrilProtocol2200087(port=port, buffer_size=buffer_size)
        return instance


#: Module's instance of the Protocol Factory.
#: This should be used whenever the Protocol class
#: is to be instantiated (as opposed to subclassed)
factory = TendrilFactory2200087()


class DMMInputChannel(InstrumentInputChannelBase):
    """
    This class provides the bulk of the accessors to the instrument
    for downstream use.

    :param parent: The instrument of which this channel is a part of.
    :param interface: The interface to the instrument.

    """
    def __init__(self, parent, interface):
        super(DMMInputChannel, self).__init__(parent)
        self._interface = interface
        self._wave = None

    def get(self, unitclass=None, flush=True):
        """
        Gets the latest data point in the channel's point buffer. By default, it
        also flushes any older points from the buffer. This behavior can be
        suppressed by passing flush=False.

        :param unitclass: Unit class of which the data point is expected, or None if you don't care.
        :param flush: Whether or not older points should be flushed. Default True.
        :return: Latest datapoint.
        :rtype: :class:`tendril.utils.types.signalbase.SignalPoint`

        """
        value = self._interface.latest_point(flush=flush)
        if unitclass is None or value.unitclass == unitclass:
            return value
        else:
            raise TypeError

    def get_next_chunk(self, unitclass=None):
        """
        Gets the next chunk of data from the instrument channel. Note that the
        chunk returned has already been removed from the channel's point buffer.

        :param unitclass: Unit class of which the data point is expected, or None if you don't care.
        :return: Wave containing all but the latest data point in the channel's point buffer.
        :rtype: :class:`tendril.utils.types.signalbase.SignalWave`

        """
        chunk = self._interface.next_chunk()
        if unitclass is None or chunk.unitclass == unitclass:
            return chunk
        else:
            raise TypeError

    def reset_wave(self):
        """
        Resets the point / wave buffer in the channel
        """
        self._interface.reset_buffer()


class InstrumentRS2200087(InstrumentBase):
    """
    This is the primary class provided by this module, and the object
    generated by :meth:`tendril.testing.instruments.get_instrument_object`
    is an instance of this class. All downstream Tendril application code
    interfaces with this class, and through it, with :class:`DMMInputChannel`.

    The primary code access to this class is though it's :attr:`channel`
    property.

    Instantiating this object results in the calling of :meth:`_detect`,
    which prepares the object for use.

    :ivar _dmm: The underlying instrument interface object
    :type _dmm: :class:`InstInterface2200087`

    """
    def __init__(self):
        super(InstrumentRS2200087, self).__init__(None)
        self._ident = "RadioShack 2200087 Digital Multimeter"

    def connect(self):
        self._detect()

    def _detect(self):
        """
        Creates and initializes the :class:`driver2200087.runner.InstInterface2200087`
        object, which in turn creates the protocol object and establishes the
        connection to the device.

        The instrument interface object created is stored in the object's
        :attr:`_dmm` instance variable.

        Subsequently, a :class:`DMMInputChannel` instance is instantiated
        and linked to the interface.

        """
        self._dmm = InstInterface2200087(pfactory=factory)
        self._dmm.connect()
        self._channels = [DMMInputChannel(self, self._dmm)]

    def configure(self, configuration):
        raise NotImplementedError

    @property
    def channel(self):
        """

        :return: The IntrumentInputChannel object.
        :rtype: :class:`DMMInputChannel`

        """
        return self._channels[0]

    def reset_waves(self):
        """
        Resets the point / wave buffers in the instrument's channels
        """
        for channel in self._channels:
            channel.reset_wave()


if __name__ == "__main__":
    i = InstrumentRS2200087()
