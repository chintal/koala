# Copyright (C) 2015 Chintalagiri Shashank
# 
# This file is part of Koala.
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
Electronics Conventions Module documentation (:mod:`conventions.electronics`)
=============================================================================
"""

from decimal import Decimal

import logging
import re

DEVICE_CLASSES = [
    'RES SMD',
    'RES THRU',
    'RES POWER',
    'RES ARRAY THRU',
    'RES ARRAY SMD',
    'POT TRIM',
    'VARISTOR',
    'CAP CER SMD',
    'CAP TANT SMD',
    'CAP CER THRU',
    'CAP ELEC THRU',
    'CAP POLY THRU',
    'CAP PAPER THRU',
    'INDUCTOR SMD',
    'INDUCTOR THRU',
    'FERRITE BEAD SMD',
    'TRANSFORMER HEAVY',
    'TRANSFORMER SMD',
    'DIODE SMD',
    'DIODE THRU',
    'ZENER SMD',
    'ZENER THRU',
    'TRIAC',
    'LED SMD',
    'LED THRU',
    'LED MODULE',
    'BRIDGE RECTIFIER',
    'CRYSTAL AT',
    'CRYSTAL TF',
    'CRYSTAL OSC',
    'TRANSISTOR THRU',
    'TRANSISTOR SMD',
    'IC THRU',
    'IC DIP',  # Phase out
    'IC SMD',
    'IC PLCC',
    'IC POWER',
    'SOCKET STRIP',
    'SOCKET DIP',
    'RELAY',
    'MODULE',
    'PCB',
    'BUZZER',
    'CONN BANANA',
    'CONN BERG STRIP',
    'CONN TERMINAL BLOCK',
    'CONN TERMINAL',
    'CONN DTYPE HOOD',
    'CONN DTYPE',
    'CONN INTERBOARD',
    'CONN FRC',
    'CONN MINIDIN',
    'CONN MOLEX MINIFIT',
    'CONN MOLEX',
    'CONN BARREL',
    'CONN SIP',
    'CONN STEREO',
    'CONN DF13 HOUS',
    'CONN DF13 WIRE',
    'CONN DF13 CRIMP',
    'CONN DF13',
    'CONN MODULAR',
    'CONN USB',
    'SWITCH TACT',
    'SWITCH PUSHBTN',
    'SWITCH ROCKER',
    'TESTPOINT',
    'SOLDER DOT',
    'BATTERY',
    'HEAT SINK',
    'CABLE FRC',
    'CABLE SIP SSC',
    'CABLE MARKER',
    'CABLE ROUND SHLD',
    'CONN CIRCULAR',
    'WIRE INSULATED',
    'SLEEVE SHRINK',
    'CRIMP',
    'THIMBLE',
    'FUSE HOLDER',
    'FUSE',
    'SOCKET POWER',
    'POWER CORD',
    'USB CABLE'
]

nofp_strs = [
    "PCB",
    "CONN",
    "MODULE",
    "CRYSTAL OSC",
    "HEAT SINK",
    "SOCKET POWER",
    "FUSE",
    "SWITCH PUSHBTN",
    "SWITCH ROCKER",
    "TRANSFORMER HEAVY",
    "CRIMP",
    "THIMBLE",
    "CABLE MARKER",
    "POWER CORD",
    "USB CABLE"
]

fpiswire_strs = [
    "CABLE ROUND",
    "WIRE",
    "CABLE FRC",
    "SLEEVE SHRINK",
]

fpismodlen_strs = [
    "CABLE SIP SSC",
    "CONN DF13 WIRE"
]


def fpismodlen(device):
    for st in fpismodlen_strs:
        if device.startswith(st):
            return True
    return False


def fpiswire(device):
    for st in fpiswire_strs:
        if device.startswith(st):
            return True
    return False


def fpiswire_ident(ident):
    device, value, footprint = parse_ident(ident)
    if fpiswire(device):
        return True
    return False


def ident_transform(device, value, footprint, tf=None):
    """
    Auto-generated ident string from the component ``device``, ``value``
    and ``footprint`` attributes.

    If the device string starts with any of the strings in ``nofp_strings``,
    the ``footprint`` is excluded from the ``ident`` string.

    When applied to gEDA generated data (BOMs, gsymlib), the return value is
    the ``Canonical Representation`` for the component. The burden of ensuring
    uniqueness and consistency is on the gEDA schematic files and authors
    thereof. See conventions.rst listed in ``somewhere`` for relevant guidelines.

    For all other forms of data, the specific modules must provide a transform
    csv file to ensure correct mapping into the canonical form. For the format
    of this file, see ``somewhere``.

    :type device: str
    :type value: str
    :type footprint: str
    """

    try:
        ident = device + " " + value + " " + footprint
    except TypeError:
        logging.error('Error generating ident : ' + str(device) + ' ' + str(value) + ' ' + str(footprint))
        ident = 'FATAL'
    for st in nofp_strs:
        if device.startswith(st):
            ident = device + " " + value
    if tf is None:
        return ident
    else:
        return tf.get_canonical(tf)


def parse_ident(ident):
    """

    :type ident: str
    """
    device = None
    value = None
    footprint = None
    for st in DEVICE_CLASSES:
        if ident.startswith(st):
            device = st
    if device is not None:
        ident = ident[len(device):]
    parts = ident.split()
    for st in nofp_strs:
        if device is not None and device.startswith(st):
            footprint = None
            value = ' '.join(parts)
    if value is None:
        footprint = parts[-1]
        value = ' '.join(parts[:-1])
    # TODO Parse Value for Special Devices?
    # TODO Obtain gEDA symbol for fancier verification?
    # TODO Check Generators?
    return device, value, footprint


def construct_resistor(resistance, wattage=None):
    if wattage is not None:
        value = '/'.join([resistance, wattage])
    else:
        value = resistance
    try:
        cresistance, cwattage = parse_resistor(value)
        if cresistance != resistance:
            raise ValueError
        if cwattage != wattage:
            raise ValueError
    except AttributeError:
        raise ValueError
    return value


def construct_capacitor(capacitance, voltage):
    if voltage is not None:
        value = '/'.join([capacitance, voltage])
    else:
        value = capacitance
    try:
        ccapacitance, cvoltage = parse_capacitor(value)
        if ccapacitance != capacitance:
            raise ValueError
        if cvoltage != voltage:
            raise ValueError
    except AttributeError:
        raise ValueError
    return value


def construct_inductor(inductance):
    value = inductance
    try:
        cinductance = parse_inductor(value)
        if cinductance != inductance:
            raise ValueError
    except AttributeError:
        raise ValueError
    return value


def construct_crystal(frequency):
    value = frequency
    try:
        cfrequency = parse_crystal(value)
        if cfrequency != frequency:
            raise ValueError
    except AttributeError:
        raise ValueError
    return value


def parse_resistor(value):
    rex = re.compile(r'^(?P<resistance>\d+(.\d+)*[mEKM])(/(?P<wattage>\d+(.\d+)*W))*$')
    try:
        rdict = rex.search(value).groupdict()
        return rdict['resistance'], rdict['wattage']
    except AttributeError:
        return None


def parse_capacitor(value):
    rex = re.compile(r'^(?P<capacitance>\d+(.\d+)*[pnum]F)(/(?P<voltage>\d+(.\d+)*V(DC|AC)*))*$')
    try:
        rdict = rex.search(value).groupdict()
        return rdict['capacitance'], rdict['voltage']
    except AttributeError:
        return None


def parse_inductor(value):
    rex = re.compile(r'^(?P<inductance>\d+(.\d+)*[pnum]H)$')
    try:
        rdict = rex.search(value).groupdict()
        return rdict['inductance']
    except AttributeError:
        return None


def parse_crystal(value):
    rex = re.compile(r'^(?P<frequency>\d+(.\d+)*[KM]Hz)$')
    try:
        rdict = rex.search(value).groupdict()
        return rdict['frequency']
    except AttributeError:
        return None


from koala.utils.types.electromagnetic import parse_resistance
from koala.utils.types.electromagnetic import parse_capacitance
from koala.utils.types.electromagnetic import parse_current
from koala.utils.types.electromagnetic import parse_voltage

res_ostrs = ['m', 'E', 'K', 'M', 'G']


def normalize_resistance(res):
    res = Decimal(res)
    ostr_idx = 1
    while res < 1:
        res *= 1000
        ostr_idx -= 1
    while res >= 1000:
        res /= 1000
        ostr_idx += 1
    return str(res) + res_ostrs[ostr_idx]


def check_for_std_val(ident):
    device, value, footprint = parse_ident(ident)
    vals = None
    if device.startswith('RES'):
        vals = parse_resistor(value)
    if device.startswith('CAP'):
        vals = parse_capacitor(value)
    if device.startswith('CRYSTAL'):
        vals = parse_crystal(value)
    if vals is not None:
        return True
    return False
