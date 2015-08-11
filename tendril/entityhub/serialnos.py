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

import idstring

import tendril.utils.state
from tendril.utils.db import with_db


from db import controller
from sqlalchemy.orm.exc import NoResultFound


nsno_table = tendril.utils.state.state_ds['nsno']


def get_series(sno):
    return sno.split('-')[0]


@with_db
def get_serialno_object(sno=None, session=None):
    return controller.get_serialno_object(sno=sno, session=session)


@with_db
def get_serialno_efield(sno=None, session=None):
    return controller.get_serialno_object(sno=sno, session=session).efield


@with_db
def serialno_exists(sno=None, session=None):
    try:
        controller.get_serialno_object(sno=sno, session=session)
        return True
    except NoResultFound:
        return False


@with_db
def register_serialno(sno=None, efield=None, session=None):
    logger.info("Registering new serial number : " + sno)
    return controller.register_serialno(sno=sno, efield=efield, session=session)


@with_db
def link_serialno(child=None, parent=None, association_type=None, session=None):
    if child is None:
        raise AttributeError("child cannot be None")
    if parent is None:
        raise AttributeError("parent cannot be None")
    logger.info("Linking " + child + " to parent " + parent)
    return controller.link_serialno(child=child, parent=parent,
                                    association_type=association_type,
                                    session=session)


@with_db
def get_parent_serialnos(sno=None, session=None):
    if sno is None:
        raise AttributeError("child cannot be None")
    return controller.get_serialno_object(sno=sno, session=session).parents


@with_db
def get_child_serialnos(sno=None, session=None):
    if sno is None:
        raise AttributeError("child cannot be None")
    return controller.get_serialno_object(sno=sno, session=session).children


@with_db
def delete_serialno(sno, recurse=False, session=None):
    if recurse is True:
        for snoi in get_child_serialnos(sno):
            controller.delete_serialno(snoi, recurse, session)
    controller.delete_serialno(sno, recurse, session)


# def delete_series(series):
#     for serialno in get_all_serialnos():
#         if get_series(serialno) == series:
#             logger.info("Deleting Serial No : " + serialno)
#             delete_serialno(serialno)
#     logger.info("Deleting Series : " + series)
#     nsno_table.delete(series=series)


@with_db
def get_serialno(series, efield=None, register=True, start_seed='100A', session=None):
    series = series.upper()
    if series in [x['series'] for x in nsno_table]:
        last_seed = nsno_table.find_one(series=series)['last_seed']
        logger.debug("Found last seed for series " + str(series) + " : " + str(last_seed))
        generator = idstring.IDstring(seed=last_seed)
        new_sno = generator + 1
        if register is True:
            logger.info("Updating seed for series " + series + " : " + str(new_sno.get_seed()))
            nsno_table.update(dict(series=series, last_seed=new_sno.get_seed()), ['series'])
            register_serialno(sno=series + '-' + new_sno, efield=efield, session=session)
        else:
            logger.info("Not updating seed for series " + series + " : " + str(new_sno.get_seed()))
        return series + '-' + new_sno
    else:
        logger.info("Could not find series in db : " + series)
        generator = idstring.IDstring(seed=start_seed)
        if register is True:
            logger.info("Creating series in db : " + series)
            nsno_table.insert(dict(series=series, last_seed=start_seed))
            register_serialno(sno=series + '-' + generator, efield=efield, session=session)
        else:
            logger.info("NOT Creating series in db : " + series)
        return series + '-' + generator
