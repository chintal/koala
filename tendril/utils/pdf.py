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
The PDF Utils Module (:mod:`tendril.utils.pdfutils`)
==================================================

This module contains small helper functions to handle PDF files. These
functions are independent of the rest of the software and can be reused
wherever needed.

"""

import PyPDF2

import os
import subprocess

import tendril.dox.wallet


def merge_pdf(pdflist, outfilepath, remove_sources=False):
    """
    Merges PDF files.
    Sources are PDF files whose paths are listed in ``pdflist`` and
    the combined PDF is written out to ``outfilepath``.


    :param pdflist: List of paths to PDF files to be merged.
    :param outfilepath: Path where output PDF file is to be written.
    :return: outfilepath
    """
    merger = PyPDF2.PdfFileMerger()
    for f in pdflist:
        if f is None:
            continue
        f = os.path.normpath(f)
        merger.append(PyPDF2.PdfFileReader(file(f, 'rb')))
    merger.write(outfilepath)
    if remove_sources is True:
        for f in pdflist:
            if not tendril.dox.wallet.is_in_wallet(f):
                os.remove(f)
    return outfilepath


def conv_ps2pdf(pspath, pdfpath):
    """
    Runs `ps2pdf` to convert a PS file specified in ``pspath`` to
    a PDF file writen out to ``pdfpath``.

    :param pspath: Path to PS file to be converted.
    :param pdfpath: Path of PDF file to be generated.
    """
    subprocess.call(['ps2pdf', pspath, pdfpath])
