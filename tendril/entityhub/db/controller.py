#!/usr/bin/env python
# encoding: utf-8

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
Docstring for controller.py
"""

from tendril.utils import log
logger = log.get_logger(__name__, log.DEFAULT)

from sqlalchemy.orm.exc import NoResultFound

from tendril.utils.db import with_db

from model import SerialNumber
from model import SerialNumberAssociation


@with_db
def get_all_serialnos(session=None):
    return session.query(SerialNumber).all()


@with_db
def get_serialno_object(sno=None, session=None):
    if sno is None:
        raise AttributeError("sno cannot be None")
    return session.query(SerialNumber).filter_by(sno=sno).one()


@with_db
def register_serialno(sno=None, efield=None, session=None):
    sobj = SerialNumber(sno=sno, efield=efield)
    session.add(sobj)
    session.flush()
    return sobj


@with_db
def delete_serialno(sno=None, session=None):
    if sno is None:
        raise AttributeError("sno cannot be None")
    if not isinstance(sno, SerialNumber):
        sno = get_serialno_object(sno=sno, session=session)
    session.delete(sno)
    session.flush()


@with_db
def link_serialno(child=None, parent=None, association_type=None, session=None):
    if not isinstance(child, SerialNumber):
        child = get_serialno_object(sno=child, session=session)
    if not isinstance(parent, SerialNumber):
        parent = get_serialno_object(sno=parent, session=session)

    try:
        existing = session.query(SerialNumberAssociation).filter_by(child_id=child.id, parent_id=parent.id).one()
        session.delete(existing)
        session.flush()
    except NoResultFound:
        pass

    assoc_object = SerialNumberAssociation(child_id=child.id, child=child,
                                           parent_id=parent.id, parent=parent,
                                           association_type=association_type)
    session.add(assoc_object)
    session.flush()
    return assoc_object
