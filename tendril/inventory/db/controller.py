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

from sqlalchemy.sql import exists
from sqlalchemy.orm.exc import MultipleResultsFound
from sqlalchemy.orm.exc import NoResultFound

import tendril.utils.db
from model import InventoryLocationCode

from tendril.utils.config import INVENTORY_LOCATIONS


def get_inventorylocationcode(name, create=False):
    with tendril.utils.db.get_session() as session:
        try:
            return session.query(InventoryLocationCode).filter_by(name=name).one().id
        except MultipleResultsFound:
            logger.warning("Found Multiple Codes for Inventory Location : " + name)
        except NoResultFound:
            if create is True:
                obj = InventoryLocationCode(name=name)
                session.add(obj)
                return obj.id
            else:
                return None


def populate_inventorylocationcodes():
    logger.info("Populating Inventory Location Codes")
    for location in INVENTORY_LOCATIONS:
        with tendril.utils.db.get_session() as session:
            if not session.query(exists().where(InventoryLocationCode.name == location)).scalar():
                logger.info("Creating location code for : " + location)
                obj = InventoryLocationCode(name=location)
                session.add(obj)
            else:
                logger.debug("Found preexisting location code for : " + location)
