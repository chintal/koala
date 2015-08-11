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


INSTANCE_TESTS_ROOT = os.path.join(INSTANCE_ROOT, 'tests')
INSTANCE_TESTS = import_(INSTANCE_TESTS_ROOT)


def get_test_object(testst):
    try:
        modname, clsname = testst.split(':')
        clsname = 'Test' + clsname
    except ValueError:
        modname = testst
        clsname = 'Test' + testst
    modstr = 'tendril.testing.tests.' + modname
    try:
        return INSTANCE_TESTS.get_test_object(testst)
    except ValueError:
        pass
    try:
        mod = __import__(modstr, fromlist=[clsname])
        cls = getattr(mod, clsname)
        instance = cls()
        return instance
    except ImportError:
        raise ValueError("Test Unrecognized :" + testst)
