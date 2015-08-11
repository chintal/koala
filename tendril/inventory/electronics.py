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
Electronics Inventory module documentation (:mod:`inventory.electronics`)
=========================================================================
"""

from tendril.utils import log
logger = log.get_logger(__name__, log.INFO)

import os
import csv

from tendril.utils.config import ELECTRONICS_INVENTORY_DATA

import acquire
from db.controller import get_inventorylocationcode


inventory_locations = []


class InventoryLine(object):
    def __init__(self, ident, qty=None, parent=None):
        self._ident = ident
        self._qty = qty
        self._parent = parent
        self._reservations = []

    @property
    def ident(self):
        return self._ident

    @property
    def avail_qty(self):
        return self._qty - self.reserved_qty

    @property
    def reserved_qty(self):
        reserved = 0
        for reservation in self._reservations:
            reserved += reservation[0]
        return reserved

    def reserve_qty(self, value, earmark):
        if value > self.avail_qty:
            raise ValueError
        logger.debug("Reserving " + self.ident + " in " + self._parent._dname +
                     " for " + earmark + " : " + str(value))
        self._reservations.append((value, earmark))

    @property
    def earmarks(self):
        em = []
        for reservation in self._reservations:
            em.append(reservation[1])
        return em

    def _reservation_gen(self):
        for reservation in self._reservations:
            yield reservation

    def get_reservation_gen(self):
        return self._reservation_gen()

    def __repr__(self):
        return self.ident + '\t' + str(self._qty) + '\t' + str(self.reserved_qty)


class InventoryLocation(object):
    def __init__(self, name, dname, reader):
        self._name = name
        self._dname = dname
        self._lines = []
        self._code = None

        self._reader = reader
        if reader is not None:
            self._load_from_reader()

    def _get_code(self):
        self._code = get_inventorylocationcode(self._dname)

    @property
    def name(self):
        return self._dname

    def _load_from_reader(self):
        for (ident, qty) in self._reader.tf_row_gen:
            self._lines.append(InventoryLine(ident, qty, self))

    def get_ident_qty(self, ident):
        avail_qty = 0
        is_here = False
        for line in self._lines:
            if line.ident == ident:
                is_here = True
                avail_qty += line.avail_qty
        if is_here:
            logger.debug("Found " + ident + " in " + self._dname + " : " + str(avail_qty))
            return avail_qty
        else:
            return None

    def get_reserve_qty(self, ident):
        reserve_qty = 0
        is_here = False
        for line in self._lines:
            if line.ident == ident:
                is_here = True
                reserve_qty += line.reserved_qty
        if is_here:
            return reserve_qty
        else:
            return None

    def reserve_ident_qty(self, ident, qty, earmark):
        for line in self._lines:
            if line.ident == ident:
                if line.avail_qty > qty:
                    line.reserve_qty(qty, earmark)
                    return 0
                elif line.avail_qty > 0:
                    qty = qty - line.avail_qty
                    line.reserve_qty(line.avail_qty, earmark)
        if qty > 0:
            raise ValueError("Unexpected Overrequisition : " + ident)
        return qty

    @property
    def earmarks(self):
        earmarks = []
        for line in self._lines:
            for em in line.earmarks:
                if em not in earmarks:
                    earmarks.append(em)
        return earmarks

    def _reservation_gen(self):
        for line in self._lines:
            if line.reserved_qty > 0:
                yield (line.ident, line.get_reservation_gen())

    def get_reservation_gen(self):
        return self._reservation_gen()


def init_inventory_locations():
    for idx, item in enumerate(ELECTRONICS_INVENTORY_DATA):
        logger.info("Acquiring Inventory Location : " + item['location'])
        reader = acquire.get_reader(idx)
        inventory_locations.append(InventoryLocation(item['sname'], item['location'], reader))


def get_total_availability(ident):
    total_avail = 0
    for location in inventory_locations:
        lqty = location.get_ident_qty(ident)
        if lqty is not None:
            total_avail += lqty
    return total_avail


def get_total_reservations(ident):
    total_reserve = 0
    for location in inventory_locations:
        lqty = location.get_reserve_qty(ident)
        if lqty is not None:
            total_reserve += lqty
    return total_reserve


def reserve_items(ident, qty, earmark, die_if_not=True):
    if qty <= 0:
        raise ValueError
    for location in inventory_locations:
        lqty = location.get_ident_qty(ident)
        if lqty is not None:
            if lqty > qty:
                location.reserve_ident_qty(ident, qty, earmark)
                return 0
            elif lqty > 0:
                location.reserve_ident_qty(ident, lqty, earmark)
                qty -= lqty
        if qty == 0:
            return 0
    if qty > 0:
        logger.warning('Partial Reservation of ' + ident +
                       ' for ' + earmark + ' : Short by ' + str(qty))
        if die_if_not is True:
            raise ValueError("Insufficient Qty. Call with die_if_not=True if handled downstream")
    return qty


def export_reservations(folderpath):
    earmarks = []
    for location in inventory_locations:
        for em in location.earmarks:
            if em not in earmarks:
                earmarks.append(em)
    for location in inventory_locations:
        dump_path = os.path.join(folderpath, 'reserve-' + location._dname + '.csv')
        with open(dump_path, 'wb') as f:
            w = csv.writer(f)
            header = ['Ident'] + earmarks + ['Total', 'Remaining']
            w.writerow(header)
            for ident, emgen in location.get_reservation_gen():
                row = [ident] + [0] * (len(earmarks) + 2)
                total = 0
                for reservation in emgen:
                    row[earmarks.index(reservation[1]) + 1] += reservation[0]
                    total += reservation[0]
                for idx, hdr in enumerate(earmarks):
                    if row[idx + 1] == 0:
                        row[idx + 1] = ''
                row[header.index('Total')] = total
                row[header.index('Remaining')] = get_total_availability(ident)
                w.writerow(row)
        logger.info("Exported " + location._dname + " Reservations to File : " + dump_path)


init_inventory_locations()
