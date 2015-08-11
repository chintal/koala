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
Inventory Acquire Module documentation (:mod:`inventory.acquire`)
=================================================================
"""

from tendril.utils import log
logger = log.get_logger(__name__, log.DEBUG)

import os
import csv
import re
import datetime

from tendril.utils import libreoffice
from tendril.utils import fs
from tendril.utils import config

from tendril.gedaif import gsymlib
from tendril.entityhub import transforms


class InventoryReaderBase(object):
    def __init__(self, location, tfpath):
        self.location = location
        self._tfpath = tfpath
        self.tf = None
        if os.path.isfile(tfpath):
            self.tf = transforms.TransformFile(self._tfpath)
        else:
            logger.warning("Transform File missing : " + self._tfpath)


class InventoryDBReader(InventoryReaderBase):
    def __init__(self, location, tfpath):
        super(InventoryDBReader, self).__init__(location, tfpath)


class StockXlsReader(InventoryReaderBase):
    def __init__(self, xlf, sname, location, tfpath):
        """

            :type xlf: utils.ooutils.XLFile
            """
        super(StockXlsReader, self).__init__(location, tfpath)

        self.sheetname = sname
        assert isinstance(xlf, libreoffice.XLFile)
        self._xlf = xlf
        self.filepath = xlf.fpath
        self.qtydate = None
        self._csvpath = xlf.get_csv_path(sname)
        self._csvfile = open(self._csvpath, 'rb')
        self._csvreader = csv.reader(self._csvfile)
        self._colident = 0
        self._colqty = -1
        self._skip_to_header()
        self.row_gen = self._row_gen()
        self.tf_row_gen = self._tf_row_gen()

    def _skip_to_header(self):
        for row in self._csvreader:
            if row[0].strip() == 'Device':
                self._get_cols(row)
                break

    def _get_cols(self, row):
        for (index, item) in enumerate(row):
            result = self._is_balance(item)
            if result is not None:
                self._colqty = index
                self.qtydate = result

    @staticmethod
    def _is_balance(item):
        if 'Balance on' in item:
            match = re.search(r'\d{2}/\d{2}/\d{4}', item)
            try:
                date = datetime.datetime.strptime(match.group(), '%d/%m/%Y').date()
            except AttributeError:
                print "Tried to match " + item
                return None
            return date
        return None

    def _row_gen(self):
        for row in self._csvreader:
            if row[0].strip() == '':
                continue
            if row[0].strip() == 'END':
                continue
            try:
                qty = int(row[self._colqty])
            except ValueError:
                qty = float(row[self._colqty])
            yield (row[self._colident],
                   qty)
        self._csvfile.close()

    def _tf_row_gen(self):
        for row in self.row_gen:
            yield (self.tf.get_canonical_repr(row[0]),
                   row[1])
        self._csvfile.close()


def get_stockxlsreader(xlpath, sname, location, tfpath):
    xlf = libreoffice.get_xlf(xlpath)
    reader = StockXlsReader(xlf, sname, location, tfpath)
    return reader


def get_reader(elec_inven_data_idx):
    sdict = config.ELECTRONICS_INVENTORY_DATA[elec_inven_data_idx]
    reader = None
    if sdict['type'] == 'QuazarStockXLS':
        fpath = sdict['fpath']
        sname = sdict['sname']
        location = sdict['location']
        tfpath = sdict['tfpath']
        reader = get_stockxlsreader(fpath, sname, location, tfpath)

    if reader is not None:
        return reader
    else:
        logger.error("Could not find reader for: ELECTRONICS_INVENTORY_DATA."
                     + str(elec_inven_data_idx))


def gen_canonical_transform(elec_inven_data_idx, regen=True):
    sdict = config.ELECTRONICS_INVENTORY_DATA[elec_inven_data_idx]
    if sdict['type'] == 'QuazarStockXLS':
        fpath = sdict['fpath']
        sname = sdict['sname']
        location = sdict['location']
        tfpath = sdict['tfpath']

        rdr = get_stockxlsreader(fpath, sname, location, tfpath)

        outp = tfpath
        outf = fs.VersionedOutputFile(outp)
        outw = csv.writer(outf)
        outw.writerow(('Current', 'gEDA Current', 'Ideal', 'Status', 'In Symlib'))
        for line in rdr.row_gen:
            if regen and rdr.tf.has_contextual_repr(line[0]):
                if gsymlib.is_recognized(rdr.tf.get_canonical_repr(line[0])):
                    in_symlib = 'YES'
                else:
                    in_symlib = ''
                outw.writerow((line[0],
                               rdr.tf.get_canonical_repr(line[0]),
                               rdr.tf.get_ideal_repr(line[0]),
                               rdr.tf.get_status(line[0]),
                               in_symlib))
            else:
                if gsymlib.is_recognized(line[0]):
                    in_symlib = True
                else:
                    in_symlib = False
                outw.writerow((line[0], line[0], line[0], 'NEW', in_symlib))
        outf.close()


if __name__ == "__main__":
    pass
