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
The LibreOffice Utils Module (:mod:`tendril.utils.libreoffice`)
===============================================================

This module provides utilities to deal with LibreOffice files. Functionality is
implemented lazily, so this doesn't really do much.

Presently, whatever it does do, it does by relying on external python code,
executed in a shell by :mod:`subprocess`. This is required since the default
LibreOffice install I have only supports a python 3 API.

For details about how it actually works, look at the documentation of the
:mod:`sofficehelpers` package. The scripts used from that package are :

- :mod:`sofficehelpers.ssconverter` for converting spreadsheets to CSV files.

.. todo:: Publish the :mod:`sofficehelpers` package somewhere, or find a
          pre-existing alternative. If there is a functionally sufficient
          alternative, it will probably be better.

"""

from tendril.utils.fs import TEMPDIR

import shutil
import os
import subprocess
import atexit


#: A list of all files currently open which the module is responsible for.
open_files = []


class XLFile(object):
    """
    This class allows reading data from LibreOffice supported Spreadsheet files,
    by converting each sheet into a CSV file, which can then be read by
    application code. Note that this is a one way conversion only. The original
    spreadsheet file is not written to.

    When the object is instantiated, a copy of the file is made in the temporary
    folder by :func:`_make_copy`, which is then converted into one CSV file per
    sheet in the original spreadsheet file by :func:`_make_csv_files`. It then
    adds itself to the modules :data:`open_files` list.

    :param filepath: The path of the spreadsheet to be opened.
    :ivar fpath: The path to the original spreadsheet file.
    :ivar fname: The file name of the original spreadsheet file.
    :ivar _csv_list: The list of CSV files generated from the spreadsheet, one per sheet.

    """
    def __init__(self, filepath):
        self.fpath = filepath
        self.fname = os.path.split(filepath)[1]
        self._csv_list = []
        self._tfpath = self._make_copy()
        self._make_csv_files()

        open_files.append(self)

    def get_csv_path(self, sheetname):
        """
        Gets the path to the CSV file that was created at object initialization
        corresponding to the sheetname provided.

        :param sheetname: Name of the Spreadsheet Sheet.
        """
        for (sname, spath) in self._csv_list:
            if sname == sheetname:
                return spath
        return None

    def _make_copy(self):
        """
        Makes a copy of the original file in the temporary directory
        """
        tfpath = os.path.join(TEMPDIR, self.fname)
        shutil.copyfile(self.fpath, tfpath)
        return tfpath

    def _make_csv_files(self):
        """
        Converts a SpreadSheet file supported by LibreOffice into a set of CSV
        files, one per sheet, using the :mod:`sofficehelpers.ssconverter` script.
        The output is parsed by :func:`_parse_sscout`.
        """
        fname = os.path.splitext(self.fname)[0]
        csvpath = os.path.join(TEMPDIR, fname + '-%s.csv')
        cstrl = ["ssconverter", self._tfpath, csvpath]
        self._csv_list = self._parse_sscout(subprocess.check_output(cstrl))

    def _parse_sscout(self, string):
        """
        Parses the output of the :mod:`sofficehelpers.ssconverter` script,
        extracting the Sheet names and corresponding CSV file names from the
        output.
        """
        fname = os.path.splitext(self.fname)[0]
        rlist = [x.strip() for x in string.split('\n')[1:-1]]
        rlist = [(os.path.split(x)[1][len(fname) + 1:-4], x) for x in rlist]
        return rlist

    def close(self):
        """
        Closes the object and removes it from the :data:`open_files` list.
        Also runs :func:`_clean` to remove all the files it created.
        """
        self._clean()
        open_files.remove(self)

    def _clean(self):
        """
        Removes all temporary files created during the object instantiation.
        """
        os.remove(self._tfpath)
        for (s, csvpath) in self._csv_list:
            os.remove(csvpath)


def get_xlf(fpath):
    """
    Gets the :class:`XLFile` object for the spreadsheet at ``fpath``,
    `opening` the file and creating the object if it does not already
    exist.

    :param fpath: Path of the spreadsheet file to open.
    :return: The opened :class:`XLFile` instance.
    """
    """
    :param fpath:
    :return:
    """
    for f in open_files:
        if f.fpath == fpath:
            return f
    f = XLFile(fpath)
    return f


def ooutils_cleanup():
    """
    Called when the python interpreter is shutting down. Cleans up all
    `tendril.utils.libreoffice` related objects and other artifacts created
    by the module.

    Performs the following tasks:
        - Closes all :data:`open_files`

    """
    for f in open_files:
        f.close()

atexit.register(ooutils_cleanup)
