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

import os
import shutil
import glob

from tendril.utils.db import with_db

from tendril.entityhub import serialnos
from tendril.utils.config import DOCSTORE_ROOT
from tendril.utils.config import INSTANCE_ROOT

from db import controller


@with_db
def list_sno_documents(serialno=None, session=None):
    if serialno is None:
        raise AttributeError("sno cannot be None")
    results = controller.get_sno_documents(serialno=serialno, session=session)
    print ("Documents for Serial No. : " + serialno)
    for result in results:
        print result


@with_db
def copy_docs_to_workspace(serialno=None, workspace=None, clearws=False, setwsno=True, iagree=False, session=None):
    if serialno is None:
        raise AttributeError('serialno cannot be None')
    if workspace is None:
        workspace = os.path.join(INSTANCE_ROOT, 'scratch', 'workspace')
    elif workspace.startswith('/'):
        workspace = workspace
        if clearws is True and iagree is False:
            raise StandardError('Workspace defined outside the Instance Scratch Area, and clearws is set to True. '
                                'All files within the provided path will be removed. '
                                'Set the iagree argument to True to accept responsibility for what you\'re doing.')
    else:
        workspace = os.path.join(INSTANCE_ROOT, 'scratch', workspace)
    if clearws is True:
        glb = os.path.join(workspace, '*')
        rf = glob.glob(glb)
        for f in rf:
            # This recursively nukes any folders that may be there. This is,
            # again, not overly safe. Consider not doing it.
            if os.path.isdir(f):
                shutil.rmtree(f)
            os.remove(f)
    if setwsno is True:
        with open(os.path.join(workspace, 'wsno'), 'w') as f:
            f.write(serialno)
    for doc in controller.get_sno_documents(serialno=serialno, session=session):
        docname = os.path.split(doc.docpath)[1]
        if docname.startswith(serialno):
            if not os.path.splitext(docname)[0] == serialno:
                docname = docname[len(serialno) + 1:]
        shutil.copy(os.path.join(DOCSTORE_ROOT, doc.docpath),
                    os.path.join(workspace, docname))


@with_db
def delete_document(docpath, session=None):
    deregister_document(docpath=docpath, session=session)
    os.remove(os.path.join(DOCSTORE_ROOT, docpath))


@with_db
def deregister_document(docpath=None, session=None):
    if docpath is None:
        raise AttributeError('docpath cannot be None')
    controller.deregister_document(docpath=docpath, session=session)


def insert_document(sno, docpath, series):
    fname = os.path.split(docpath)[1]
    if not fname.startswith(sno) and not os.path.splitext(fname)[0].endswith(sno):
        fname = sno + '-' + fname
    if series is None:
        series = serialnos.get_series(sno)
    storepath = os.path.join(DOCSTORE_ROOT, series.replace('/', os.path.sep), fname)
    if not os.path.exists(os.path.dirname(storepath)):
        os.makedirs(os.path.dirname(storepath))
    shutil.copyfile(docpath, storepath)
    return storepath


@with_db
def register_document(serialno=None, docpath=None, doctype=None, efield=None, series=None, session=None):
    if serialno is None:
        raise AttributeError("serialno cannot be None")
    if docpath is None:
        raise AttributeError('docpath cannot be None')
    if doctype is None:
        raise AttributeError('doctype cannot be None')

    logger.info("Registering document for sno " + str(serialno) + " : " + str(docpath))
    # WARNING : This writes the file before actually checking that all is ok. This
    #           may not be a very safe approach.
    storepath = insert_document(serialno, docpath, series)
    storepath = os.path.relpath(storepath, DOCSTORE_ROOT)
    controller.register_document(serialno=serialno, docpath=storepath, doctype=doctype,
                                 efield=efield, session=session)


# def clean_docindex():
#     pass
#
#
# def clean_docstore():
#     pass
