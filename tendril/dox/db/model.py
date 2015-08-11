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

from sqlalchemy import Column, String, Integer, ForeignKey
from sqlalchemy.orm import relationship
from sqlalchemy.orm import backref

from tendril.utils.db import DeclBase
from tendril.utils.db import BaseMixin
from tendril.utils.db import TimestampMixin


class DocStoreDocument(TimestampMixin, BaseMixin, DeclBase):
    docpath = Column(String, unique=True, nullable=False)
    doctype = Column(String, unique=False, nullable=True)
    efield = Column(String, unique=False, nullable=True)

    serialno_id = Column(Integer, ForeignKey('SerialNumber.id'), nullable=False)

    # This does not work :
    # serialno = relationship("SerialNumber", backref=backref("document", cascade="all, delete"))
    serialno = relationship("SerialNumber", backref="documents")

    def __repr__(self):
        return '<DocStoreDocument {0:<20} {2:<25} {1:<40}>'.format(str(self.doctype), str(self.docpath), str(self.efield))
