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
Docstring for controller
"""

from tendril.utils import log
logger = log.get_logger(__name__, log.DEFAULT)

from sqlalchemy.orm.exc import NoResultFound
from tendril.utils.db import with_db
from tendril.entityhub.db.model import SerialNumber
from tendril.entityhub import serialnos

from model import DocStoreDocument


@with_db
def get_sno_documents(serialno=None, session=None):
    if not isinstance(serialno, SerialNumber):
        serialno = serialnos.get_serialno_object(sno=serialno, session=session)
    return session.query(DocStoreDocument).filter_by(serialno=serialno).all()


@with_db
def register_document(serialno=None, docpath=None, doctype=None, efield=None, session=None):
    if serialno is None:
        raise AttributeError("serialno cannot be None")
    if docpath is None:
        raise AttributeError('docpath cannot be None')
    if doctype is None:
        raise AttributeError('doctype cannot be None')

    if not isinstance(serialno, SerialNumber):
        serialno = serialnos.get_serialno_object(sno=serialno, session=session)

    dobj = DocStoreDocument(docpath=docpath, doctype=doctype, efield=efield,
                            serialno_id=serialno.id, serialno=serialno)
    session.add(dobj)
    session.flush()


@with_db
def deregister_document(docpath=None, session=None):
    if docpath is None:
        raise AttributeError('docpath cannot be None')
    if not isinstance(docpath, DocStoreDocument):
        docpath = session.query(DocStoreDocument).filter_by(docpath=docpath).one()
    session.delete(docpath)
    session.flush()
