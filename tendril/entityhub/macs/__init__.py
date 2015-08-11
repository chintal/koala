#!/usr/bin/env python
# encoding: utf-8

# Copyright (C) 2015 Chintalagiri Shashank
#
# This file is part of tendril.
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
Docstring for __init__.py
"""


from tendril.utils import log
logger = log.get_logger(__name__, log.DEFAULT)

import os

from tendril.gedaif.conffile import ConfigsFile
from tendril.gedaif.conffile import NoGedaProjectException

from tendril.entityhub import serialnos
from tendril.entityhub import projects

from tendril.utils.db import with_db

from tendril.utils.config import INSTANCE_ROOT
from tendril.utils.fs import import_

macs_folder = os.path.join(INSTANCE_ROOT, 'macs')


@with_db
def get_mac_from_sno(serialno=None, session=None):
    devicetype = serialnos.get_serialno_efield(sno=serialno)

    try:
        projectfolder = projects.cards[devicetype]
    except KeyError:
        raise AttributeError("Project for " + devicetype + " not found.")

    try:
        gcf = ConfigsFile(projectfolder)
        logger.debug("Using gEDA configs file from : " + projects.cards[devicetype])
    except NoGedaProjectException:
        raise AttributeError("gEDA project for " + devicetype + " not found.")

    modname = gcf.mactype
    funcname = 'get_mac_from_sno'

    mod = import_(os.path.join(macs_folder, modname))
    func = getattr(mod, funcname)
    return func(serialno=serialno, session=session)


@with_db
def get_sno_from_mac(mac=None, mactype=None, devicetype=None, session=None):

    if mactype is None:
        try:
            projectfolder = projects.cards[devicetype]
        except KeyError:
            raise AttributeError("Project for " + devicetype + " not found.")

        try:
            gcf = ConfigsFile(projectfolder)
            logger.debug("Using gEDA configs file from : " + projects.cards[devicetype])
        except NoGedaProjectException:
            raise AttributeError("gEDA project for " + devicetype + " not found.")

        modname = gcf.mactype
    else:
        modname = mactype
    funcname = 'get_sno_from_mac'

    mod = import_(os.path.join(macs_folder, modname))
    func = getattr(mod, funcname)
    return func(mac=mac, session=session)


def get_device_mac(mactype='QASCv1'):
    if mactype == 'QASCv1':
        funcname = 'get_device_mac'
        modname = mactype
    else:
        raise ValueError("Unrecognized MACTYPE")

    mod = import_(os.path.join(macs_folder, modname))
    func = getattr(mod, funcname)
    return func()


def get_sno_from_device(mactype='QASCv1'):
    mac = get_device_mac(mactype)
    return get_sno_from_mac(mac=mac, mactype=mactype)
