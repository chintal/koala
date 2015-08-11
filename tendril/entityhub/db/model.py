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
logger = log.get_logger(__name__, log.DEFAULT)

from sqlalchemy import Column, Integer, String, ForeignKey
from sqlalchemy.orm import relationship
from sqlalchemy.orm import backref
from sqlalchemy.ext.declarative import declared_attr
from sqlalchemy import UniqueConstraint

from tendril.utils.db import DeclBase
from tendril.utils.db import BaseMixin
from tendril.utils.db import TimestampMixin


class SerialNumber(TimestampMixin, BaseMixin, DeclBase):
    sno = Column(String, unique=True, nullable=False)
    efield = Column(String, unique=False, nullable=True)

    def __repr__(self):
        return "<Serial Number (id = %s, sno='%s', efield='%s')>" % (self.id, self.sno, self.efield)


class SerialNumberAssociation(TimestampMixin, BaseMixin, DeclBase):
    parent_id = Column(Integer, ForeignKey('SerialNumber.id'))
    parent = relationship("SerialNumber", backref="children", primaryjoin=(SerialNumber.id == parent_id))
    child_id = Column(Integer, ForeignKey('SerialNumber.id'))
    child = relationship("SerialNumber", backref="parents", primaryjoin=(SerialNumber.id == child_id))
    association_type = Column(String, nullable=True, unique=False)

    __table_args__ = (
        UniqueConstraint('parent_id', 'child_id'),
    )


# These don't work :
# class BoundToSerialNumberMixin(object):
#     @declared_attr
#     def serialno_id(self):
#         return Column(Integer, ForeignKey('SerialNumber.id'))
#
#     @declared_attr
#     def serialno(self):
#         return relationship("SerialNumber", backref=lambda: backref(self._provides, cascade="all, delete"))
#
#
# class LinkedToSerialNumberMixin(object):
#     @declared_attr
#     def serialno_id(self):
#         return Column(Integer, ForeignKey('SerialNumber.id'))
#
#     @declared_attr
#     def serialno(self):
#         return relationship("SerialNumber", backref=lambda: self._provides)
