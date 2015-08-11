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

from tendril.utils import log
logger = log.get_logger(__name__, log.INFO)

import time
import arrow


class TestPrepBase(object):
    """ Object representing a preparatory step for a Test """
    def __init__(self):
        self._parent = None

    @property
    def parent(self):
        return self._parent

    @parent.setter
    def parent(self, value):
        self._parent = value

    def run_prep(self):
        raise NotImplementedError


class TestPrepUser(TestPrepBase):
    def __init__(self, string):
        super(TestPrepUser, self).__init__()
        self._string = string

    def run_prep(self):
        print self._string
        raw_input("Press Enter to continue...")


class RunnableTest(object):
    def __init__(self):
        self._serialno = None
        self._parent = None
        self._desc = None

    @property
    def parent(self):
        return self._parent

    @parent.setter
    def parent(self, value):
        self._parent = value

    @property
    def serialno(self):
        if self._serialno is not None:
            return self._serialno
        else:
            return self._parent.serialno

    @serialno.setter
    def serialno(self, value):
        self._serialno = value

    def run_test(self):
        raise NotImplementedError

    @property
    def passed(self):
        raise NotImplementedError

    def render(self):
        raise NotImplementedError

    def finish(self):
        logger.info(repr(self) + " :: Result : " + str(self.passed))

    @property
    def desc(self):
        return self._desc

    @desc.setter
    def desc(self, value):
        self._desc = value


class TestBase(RunnableTest):
    """ Object representing a full runnable Test of the same Measurement type"""
    def __init__(self):
        super(TestBase, self).__init__()
        self._prep = []
        self._measurements = []
        self._result = None
        self.variables = {}

    def add_measurement(self, measurement):
        measurement.parent = self
        self._measurements.append(measurement)
        return measurement

    def run_test(self):
        logger.debug("Running Test : " + repr(self))
        for prep in self._prep:
            prep.run_prep()
        for measurement in self._measurements:
            measurement.do_measurement()

    def configure(self, **kwargs):
        self.variables.update(kwargs)

    def add_prep(self, prep):
        prep.parent = self
        self._prep.append(prep)

    @property
    def passed(self):
        raise NotImplementedError

    @property
    def render(self):
        raise NotImplementedError


class TestSuiteBase(RunnableTest):
    """ Object representing a full runnable Test Suite on a single entity """
    def __init__(self):
        super(TestSuiteBase, self).__init__()
        self._tests = []
        self._prep = []

    def add_prep(self, prep):
        assert isinstance(prep, TestPrepBase)
        prep.parent = self
        self._prep.append(prep)

    def add_test(self, test):
        test.parent = self
        self._tests.append(test)

    def run_test(self):
        logger.debug("Running Test Suite : " + repr(self))
        for prep in self._prep:
            prep.run_prep()
        for test in self._tests:
            test.run_test()

    @property
    def passed(self):
        rval = True
        for test in self._tests:
            if test.passed is False:
                rval = False
        return rval

    def render(self):
        raise NotImplementedError

    def finish(self):
        for test in self._tests:
            test.finish()

    @property
    def tests(self):
        return self._tests
