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
Docstring for model
"""

from tendril.utils import log
logger = log.get_logger(__name__, log.DEFAULT)

from sqlalchemy import Column, String, Integer, ForeignKey, Boolean
from sqlalchemy.dialects.postgresql import JSON
from sqlalchemy.orm import relationship

from tendril.utils.db import DeclBase
from tendril.utils.db import BaseMixin
from tendril.utils.db import TimestampMixin


class TestSuiteResult(TimestampMixin, BaseMixin, DeclBase):
    suite_class = Column(String, unique=False, nullable=False)
    desc = Column(String, unique=False, nullable=True)

    serialno_id = Column(Integer, ForeignKey('SerialNumber.id'), nullable=False)
    serialno = relationship("SerialNumber", backref="test_suites")

    passed = Column(Boolean, unique=False, nullable=False)

    def __repr__(self):
        return '<TestSuiteResult {0:<20} {2:<25} {1:<40}>'.format(str(self.created_at),
                                                                  str(self.serialno),
                                                                  str(self.suite_class))


class TestResult(TimestampMixin, BaseMixin, DeclBase):
    test_class = Column(String, unique=False, nullable=False)
    desc = Column(String, unique=False, nullable=True)

    testsuite_id = Column(Integer, ForeignKey('TestSuiteResult.id'), nullable=False)
    testsuite = relationship("TestSuiteResult", backref="tests")

    result = Column(JSON, unique=False, nullable=False)
    passed = Column(Boolean, unique=False, nullable=False)

    def __repr__(self):
        return '<TestResult {0:<20} {2:<25} {1:<40}>'.format(str(self.created_at),
                                                             str(self.testsuite.serialno),
                                                             str(self.test_class))
