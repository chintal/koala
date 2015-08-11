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
Electronics Conventions Module documentation (:mod:`conventions.electronics`)
=============================================================================
"""

from decimal import Decimal

import logging
import re


DEVICE_CLASSES_DOC = [
    ('RES SMD', 'SMD Resistors'),
    ('RES THRU', 'THRU Resistors'),
    ('RES POWER', 'Off-PCB power resistors for direct mounting onto heatsinks'),
    ('RES ARRAY THRU', 'THRU Resistor Arrays'),
    ('RES ARRAY SMD', 'SMD Resistor Arrays'),
    ('POT TRIM', 'Trimpots'),
    ('VARISTOR', 'Varistors and MOVs'),
    ('CAP CER SMD', 'SMD Ceramic Capacitors'),
    ('CAP TANT SMD', 'SMD Tantalum Capacitors'),
    ('CAP CER THRU', 'THRU Ceramic Capacitors'),
    ('CAP ELEC THRU', 'THRU Electrolytic Capacitors'),
    ('CAP POLY THRU', 'THRU Poly Capacitors'),
    ('CAP PAPER THRU', 'THRU Paper Capacitors'),
    ('INDUCTOR SMD', 'SMD Inductors'),
    ('INDUCTOR THRU', 'THRU Inductors'),
    ('FERRITE BEAD SMD', 'SMD Ferrite Beads'),
    ('TRANSFORMER HEAVY', 'Transformers'),
    ('TRANSFORMER SMD', 'SMD Transformers'),
    ('DIODE SMD', 'SMD Diodes'),
    ('DIODE THRU', 'THRU Diodes'),
    ('ZENER SMD', 'SMD Zener Diodes'),
    ('ZENER THRU', 'THRU Zener Diodes'),
    ('TRIAC', 'Triacs'),
    ('LED SMD', 'SMD LEDs'),
    ('LED THRU', 'THRU LEDs'),
    ('LED MODULE', 'LED Modules'),
    ('BRIDGE RECTIFIER', 'Bridge Rectifiers'),
    ('CRYSTAL AT', 'AT cut Crystals'),
    ('CRYSTAL TF', 'Tuning Fork Crystals'),
    ('CRYSTAL OSC', 'Integrated Crystal Oscillators'),
    ('TRANSISTOR THRU', 'THRU Transistors including MOSFETs'),
    ('TRANSISTOR SMD', 'SMD Transistors including MOSFETs'),
    ('IC THRU', 'THRU Hole ICs'),
    ('IC DIP', '(Phase out) THRU Hole ICs'),
    ('IC SMD', 'SMD ICs'),
    ('IC PLCC', 'PLCC ICs, separated because of their need for a socket'),
    ('IC POWER', 'Off-PCB power ICs for direct mounting onto heatsinks'),
    ('SOCKET STRIP', 'SIP sockets'),
    ('SOCKET DIP', 'IC sockets and bases'),
    ('RELAY', 'Relays'),
    ('MODULE', 'Modules'),
    ('PCB', 'Printed Circuit Board'),
    ('BUZZER', 'Buzzers'),
    ('CONN BANANA', 'Banana Connectors'),
    ('CONN BERG STRIP', 'Berg Strips'),
    ('CONN TERMINAL BLOCK', 'Terminal Blocks, usually single-part'),
    ('CONN TERMINAL', 'Terminal Connectors, usually two-part.'),
    ('CONN DTYPE HOOD', 'Hood for DTYPE Connectors'),
    ('CONN DTYPE', 'DTYPE Connectors'),
    ('CONN INTERBOARD', 'Stackthrough Headers'),
    ('CONN FRC', 'FRC Connectors'),
    ('CONN MINIDIN', 'MiniDIN Connectors'),
    ('CONN MOLEX MINIFIT', 'Molex Minifit connectors'),
    ('CONN MOLEX', 'Molex Connector'),
    ('CONN BARREL', 'DC Power Jacks and similar barrel connectors'),
    ('CONN SIP', 'SIP connectors'),
    ('CONN STEREO', 'Stereo Connectors'),
    ('CONN DF13 HOUS', 'Hirose DF13 Connector Housings'),
    ('CONN DF13 WIRE', 'Prefabricated Hirose DF13 Connector Wires'),
    ('CONN DF13 CRIMP', 'Hirose DF13 Connector Crimps'),
    ('CONN DF13', 'Hirose DF13 PCB Mount Connectors'),
    ('CONN MODULAR', 'Modular Connectors'),
    ('CONN USB', 'USB Connectors'),
    ('SWITCH TACT', 'Tactile Switches'),
    ('SWITCH PUSHBTN', 'Pushbutton Switches'),
    ('SWITCH ROCKER', 'Rocker Switches'),
    ('TESTPOINT', 'Test Points'),
    ('SOLDER DOT', 'Solder Dots'),
    ('BATTERY', 'Battery and Battery Holders'),
    ('HEAT SINK', 'Heat Sinks'),
    ('CABLE FRC', 'FRC Cables'),
    ('CABLE SIP SSC', 'Prefabricated SIP Cables'),
    ('CABLE MARKER', 'Cable Markers'),
    ('CABLE ROUND SHLD', 'Round Shielded Cables'),
    ('CONN CIRCULAR', 'Circular Connectors'),
    ('WIRE INSULATED', 'Insulated Wires'),
    ('SLEEVE SHRINK', 'Heat shrinking sleeves'),
    ('CRIMP', 'Crimps'),
    ('THIMBLE', 'Thimbles'),
    ('FUSE HOLDER', 'Fuse Holders'),
    ('FUSE', 'Fuses'),
    ('SOCKET POWER', 'Power Sockets'),
    ('POWER CORD', 'Power Cords'),
    ('USB CABLE', 'USB Cables'),
]


DEVICE_CLASSES = [x[0] for x in DEVICE_CLASSES_DOC]

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


from tendril.utils.types.electromagnetic import parse_resistance
from tendril.utils.types.electromagnetic import parse_capacitance
from tendril.utils.types.electromagnetic import parse_current
from tendril.utils.types.electromagnetic import parse_voltage

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
