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
The Filesystem Utils Module (:mod:`tendril.utils.fs`)
===================================================

This module provides utilities to deal with filesystems. For the most part,
this module basically proxies specific requests to various other third-party
or python libraries.

.. rubric:: Module Contents

.. autosummary::

    TEMPDIR
    fsutils_cleanup
    zipdir

    Crumb
    get_path_breadcrumbs

    get_folder_mtime
    get_file_mtime
    VersionedOutputFile

    import_


"""

from tendril.utils import log
logger = log.get_logger(__name__, log.INFO)

import imp
import tempfile
import zipfile
import atexit
import os
import glob
import string
from datetime import datetime
from collections import namedtuple


if tempfile.tempdir is None:
    tempfile.tempdir = tempfile.mkdtemp()


#: The path to the temporary directory which all application code can import,
#: and create whatever temporary files it needs within it.
#:
#: This directory will be removed by Tendril at clean application exit or
#: by the Operating System as per it's policies.
#:
#: Every execution of tendril in a separate process owns it's own temporary
#: directory.
#:
#: .. seealso:: :func:`fsutils_cleanup`
#:
TEMPDIR = tempfile.gettempdir()


def zipdir(path, zfpath):
    """
    Creates a zip file at ``zfpath`` containing all the files in ``path``.
    This function is simple wrapper around python's :mod:`zipfile` module.

    :param path: Path of the source folder, which is to be added to the zip file.
    :param zfpath: Path of the zip file to create.
    :return: The path of the created zip file.

    """
    zfile = zipfile.ZipFile(zfpath, 'w')
    for root, dirs, files in os.walk(path):
        for f in files:
            zfile.write(os.path.join(root, f), os.path.relpath(os.path.join(root, f), os.path.join(path, '..')))
    zfile.close()
    return zfpath


#: A named tuple definition for a Crumb of a Breadcrumb.
#: This can be used to construct breadcrumb navigation by application
#: code. While it resides in the :mod:`tendril.utils.fs` module, the same
#: type should be used for other forms of breadcrumbs as well. It is
#: placed here due to its proximity to :mod:`os.path`.
Crumb = namedtuple('Crumb', 'name path')


def get_path_breadcrumbs(path, base=None, rootst='Root'):
    """
    Given a certain filesystem ``path`` and an optional ``base``, this
    function returns a list of :class:`Crumb` objects, forming the breadcrumbs
    to that path from the base. The value of ``rootst`` is prepended to the
    list, providing a means to insert a title indicating the base of the
    breadcrumb list.

    :param path: The path to the target, compatible with :mod:`os.path`
    :type path: str
    :param base: The path of the base, compatible with :mod:`os.path`. Optional.
    :type base: str
    :param rootst: The string for the root breadcrumb.
    :type rootst: str
    :return: The breadcrumbs.
    :rtype: :class:`list` of :class:`Crumb`

    """
    if base is not None:
        path = os.path.relpath(path, base)
    crumbs = []
    while True:
        head, tail = os.path.split(path)
        if not tail:
            break
        crumbs = [Crumb(name=tail, path=path)] + crumbs
        path = head
    crumbs = [Crumb(name=rootst, path='')] + crumbs
    return crumbs


def get_folder_mtime(folder):
    """
    Given the path to a certain filesystem ``folder``, this function returns
    a :class:`datetime.datetime` instance representing the time of the latest
    change of any file contained within the folder.

    :param folder: The path to the ``folder``, compatible with :mod:`os.path`
    :type folder: str
    :return: The time of the latest change within the ``folder``
    :rtype: :class:`datetime.datetime`

    .. seealso:: :func:`get_file_mtime`

    """
    filelist = [os.path.join(folder, f) for f in os.listdir(folder)]
    last_change = None
    for f in filelist:
        fct = get_file_mtime(f)
        if last_change is None:
            last_change = fct
        elif fct is not None and last_change < fct:
            last_change = fct
    return last_change


def get_file_mtime(f):
    """
    Given the path to a certain filesystem ``file``, this function returns
    a :class:`datetime.datetime` instance representing the time of the latest
    change of that file.

    :param f: The path to the ``file``, compatible with :mod:`os.path`
    :type f: str
    :return: The time of the latest change within the ``folder``
    :rtype: :class:`datetime.datetime`

    .. seealso:: :func:`get_folder_mtime`

    """
    try:
        return datetime.fromtimestamp(os.path.getmtime(f))
    except OSError:
        return None


class VersionedOutputFile:
    """
    This is like a file object opened for output, but it makes
    versioned backups of anything it might otherwise overwrite.

    `http://code.activestate.com/recipes/52277-saving-backups-when-writing-files/`_
    """

    def __init__(self, pathname, numSavedVersions=3):
        """
        Create a new output file.

        :param pathname: The name of the file to [over]write.
        :param numSavedVersions: How many of the most recent versions of `pathname` to save.

        """

        self._pathname = pathname
        self._tmpPathname = "%s.~new~" % self._pathname
        self._numSavedVersions = numSavedVersions
        self._outf = open(self._tmpPathname, "wb")

    def __del__(self):
        self.close()

    def close(self):
        if self._outf:
            self._outf.close()
            self._replace_current_file()
            self._outf = None

    def as_file(self):
        """
        Return self's shadowed file object, since marshal is
        pretty insistent on working w. pure file objects.
        """
        return self._outf

    def __getattr__(self, attr):
        """
        Delegate most operations to self's open file object.
        """
        return getattr(self.__dict__['_outf'], attr)

    def _replace_current_file(self):
        """
        Replace the current contents of self's named file.
        """
        self._backup_current_file()
        os.rename(self._tmpPathname, self._pathname)

    def _backup_current_file(self):
        """
        Save a numbered backup of self's named file.
        """
        # If the file doesn't already exist, there's nothing to do.
        if os.path.isfile(self._pathname):
            new_name = self._versioned_name(self._current_revision() + 1)
            os.rename(self._pathname, new_name)

            # Maybe get rid of old versions.
            if (self._numSavedVersions is not None) and (self._numSavedVersions > 0):
                self._delete_old_revisions()

    def _versioned_name(self, revision):
        """
        Get self's pathname with a revision number appended.
        """
        return "%s.~%s~" % (self._pathname, revision)

    def _current_revision(self):
        """
        Get the revision number of self's largest existing backup.
        """
        revisions = [0] + self._revisions()
        return max(revisions)

    def _revisions(self):
        """
        Get the revision numbers of all of self's backups.
        """
        revisions = []
        backup_names = glob.glob("%s.~[0-9]*~" % self._pathname)
        for name in backup_names:
            try:
                revision = int(string.split(name, "~")[-2])
                revisions.append(revision)
            except ValueError:
                # Some ~[0-9]*~ extensions may not be wholly numeric.
                pass
        revisions.sort()
        return revisions

    def _delete_old_revisions(self):
        """
        Delete old versions of self's file, so that at most
        :attr:`_numSavedVersions` versions are retained.
        """
        revisions = self._revisions()
        revisions_to_delete = revisions[:-self._numSavedVersions]
        for revision in revisions_to_delete:
            pathname = self._versioned_name(revision)
            if os.path.isfile(pathname):
                os.remove(pathname)


def fsutils_cleanup():
    """
    Called when the python interpreter is shutting down. Cleans up all
    `tendril.utils.fs` related objects and other artifacts created by the
    module.

    Performs the following tasks:
        - Removes the :data:`TEMPDIR`

    """
    try:
        os.rmdir(tempfile.gettempdir())
    except OSError:
        pass


def import_(fpath):
    """
    Imports the file specified by the ``fpath`` parameter using the
    :mod:`imp` python module and returns the loaded module.

    :param fpath: Path of the python module to import.
    :return: Module object of the imported python module.
    """
    (path, name) = os.path.split(fpath)
    (name, ext) = os.path.splitext(name)
    (f, filename, data) = imp.find_module(name, [path])
    return imp.load_module(name, f, filename, data)


atexit.register(fsutils_cleanup)
