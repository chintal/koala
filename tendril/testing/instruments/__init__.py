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


import os

from tendril.utils.config import INSTANCE_ROOT
from tendril.utils.fs import import_


INSTANCE_INSTRUMENTS_ROOT = os.path.join(INSTANCE_ROOT, 'instruments')
INSTANCE_INSTRUMENTS = import_(INSTANCE_INSTRUMENTS_ROOT)

instument_pool = {}


def get_instrument_object(instst, dedicated=False):
    modname = instst
    modstr = 'tendril.testing.instruments.' + modname
    clsname = 'Instrument' + instst

    if dedicated is False:
        if modname in instument_pool.keys():
            if len(instument_pool[modname]) > 0:
                return instument_pool[modname][0]

    try:
        instance = INSTANCE_INSTRUMENTS.get_test_object(instst)
    except ValueError:
        try:
            mod = __import__(modstr, fromlist=[clsname])
            cls = getattr(mod, clsname)
            instance = cls()
        except ImportError:
            raise ValueError("Instrument Unrecognized :" + instst)

    if modname in instument_pool.keys():
        instument_pool[modname].append(instance)
    else:
        instument_pool[modname] = [instance]

    return instance
