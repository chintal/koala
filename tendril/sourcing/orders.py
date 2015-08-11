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

import csv
import copy
import os

from tendril.gedaif import gsymlib
import tendril.inventory.guidelines
import tendril.sourcing.electronics


class CompositeOrderElem(object):
    def __init__(self, order, ident, rqty, shortage):
        self._order = order
        self._ident = ident
        self._rqty = rqty
        self._resqty = rqty - shortage
        self._shortage = shortage
        try:
            self._sources = tendril.sourcing.electronics.get_sourcing_information(self.ident, self.gl_compl_qty,
                                                                                avendors=self._order._allowed_vendors,
                                                                                allvendors=True
                                                                                )
            self._selsource = self._sources[0]
            for vsinfo in self._sources:
                if self.get_eff_acq_price(vsinfo) < self.get_eff_acq_price(self._selsource):
                    self._selsource = vsinfo
        except tendril.sourcing.electronics.SourcingException:
            self._sources = None
            self._selsource = None

    @staticmethod
    def get_eff_acq_price(source):
        return source[2] * source[5].unit_price.native_value

    @property
    def ident(self):
        return self._ident

    @property
    def in_gsymlib(self):
        if gsymlib.is_recognized(self.ident):
            return "YES"
        return None

    @property
    def rqty(self):
        return self._rqty

    @property
    def resqty(self):
        return self._resqty

    @property
    def shortage(self):
        return self._shortage

    @property
    def gl_compl_qty(self):
        return tendril.inventory.guidelines.electronics_qty.get_compliant_qty(self.ident, self.shortage)

    @property
    def sources(self):
        return self._sources

    @property
    def selsource(self):
        return self._selsource

    @property
    def sorted_other_sources(self):
        return sorted(self.other_sources, key=lambda x: x[5].extended_price(x[2]).native_value)

    @property
    def other_sources(self):
        if self._sources is not None:
            return [x for x in self._sources if x[0].name != self._selsource[0].name]
        else:
            return []

    def excess(self, vsinfo):
        return vsinfo[5].extended_price(vsinfo[2]).native_value - \
            self._selsource[5].extended_price(self._selsource[2]).native_value

    @property
    def is_sourceable(self):
        if self._sources is not None and len(self._sources) > 0:
            return True
        else:
            return False

    def order(self):
        vobj = self._selsource[0]
        vobj.add_to_order([self.ident] + list(self._selsource), self._order.orderref)

    def __repr__(self):
        return str((self.ident, self.is_sourceable, self.selsource, len(self.other_sources))) + os.linesep


class CompositeOrder(object):
    _columns = [("Component Details",
                 [("Ident", None),
                  ("In gsymlib", None)]),
                ("Requirement",
                 [("Required", "Qty"),
                  ("Reserved", "Qty"),
                  ("Shortage", "Qty")]),
                ("Guideline Compliant",
                 [("Buy Qty", "Qty")]),
                ("Order Details",
                 [("Vendor", None),
                  ("Vendor Part No", None),
                  ("Manufacturer", None),
                  ("Manufacturer Part No", None),
                  ("Description", None)]),
                ("Vendor Pricing",
                 [("Vendor Currency", None),
                  ("Next Break Qty", "Qty"),
                  ("NB Unit Price", "(VC)"),
                  ("NB Extended Price", "(VC)"),
                  ("Used Break Qty", "(VC)"),
                  ("UB Unit Price", "(VC)"),
                  ("UB Extended Price", "(VC)")]),
                ("Order Pricing",
                 [("Lower Break Unit Price", "INR"),
                  ("Unit Price", "INR"),
                  ("Effective Unit Price", "INR"),
                  ("Order Qty", "Qty"),
                  ("Excess Qty", "Qty"),
                  ("Effective Extended Price", "INR"),
                  ("Effective Excess Price", "INR"),
                  ("Excess Rationale", None)])
                ]

    def __init__(self, vendor_list=None, orderref=None):
        self._allowed_vendors = vendor_list
        self._orderref = orderref
        self._lines = []

    @property
    def orderref(self):
        return self._orderref

    def add(self, ident, rqty, shortage, orderref=None):
        if self._orderref is not None and self._orderref != orderref:
            logger.warning("Overwriting order reference to " +
                           orderref + " from " + self._orderref)
        self._orderref = orderref
        self._lines.append(CompositeOrderElem(self, ident, rqty, shortage))
        return self._lines[-1].is_sourceable

    def _get_headers(self, row):
        rval = []
        if row == 0:
            for section in self._columns:
                rval.append(section[0])
                rval.extend([None] * (len(section[1]) - 1))
            return rval
        else:
            for section in self._columns:
                for item in section[1]:
                    rval.append(item[row - 1])
            return rval

    def _render_vsinfo(self, vsinfo, row, basereq=None):
        vobj, vpno, oqty, nbprice, ubprice, effprice, urationale, olduprice = vsinfo
        if basereq is None:
            basereq = oqty

        headers = self._get_headers(1)
        row[headers.index("Vendor")] = vobj.name
        row[headers.index("Vendor Part No")] = vpno

        vpobj = vobj.get_vpart(vpno)

        row[headers.index("Manufacturer")] = vpobj.manufacturer
        row[headers.index("Manufacturer Part No")] = vpobj.mpartno
        row[headers.index("Description")] = vpobj.vpartdesc

        row[headers.index("Vendor Currency")] = vobj.currency.symbol
        row[headers.index("Order Qty")] = oqty
        row[headers.index("Excess Qty")] = oqty - basereq

        if nbprice is not None:
            row[headers.index("Next Break Qty")] = nbprice.moq
            row[headers.index("NB Unit Price")] = nbprice.unit_price.source_value
            row[headers.index("NB Extended Price")] = nbprice.extended_price(nbprice.moq).source_value

        if ubprice is not None:
            row[headers.index("Used Break Qty")] = ubprice.moq
            row[headers.index("UB Unit Price")] = ubprice.unit_price.source_value
            row[headers.index("UB Extended Price")] = ubprice.extended_price(oqty).source_value
            row[headers.index("Unit Price")] = "%.2f" % ubprice.unit_price.native_value

        if effprice is not None:
            row[headers.index("Effective Unit Price")] = "%.2f" % effprice.unit_price.native_value
            row[headers.index("Effective Extended Price")] = "%.2f" % effprice.extended_price(oqty).native_value
            row[headers.index("Effective Excess Price")] = "%.2f" % ((oqty - basereq) * effprice.unit_price.native_value)

        if olduprice is not None:
            row[headers.index("Lower Break Unit Price")] = "%.2f" % olduprice.unit_price.native_value

        row[headers.index("Excess Rationale")] = urationale
        return row

    def _render_line(self, line, writer, include_others):
        assert isinstance(line, CompositeOrderElem)
        headers = self._get_headers(1)
        row = [None] * len(self._get_headers(1))

        row[headers.index("In gsymlib")] = line.in_gsymlib
        row[headers.index("Ident")] = line.ident
        row[headers.index("Required")] = line.rqty
        row[headers.index("Reserved")] = line.resqty
        row[headers.index("Shortage")] = line.shortage
        row[headers.index("Buy Qty")] = line.gl_compl_qty

        if line.selsource is not None:
            row = self._render_vsinfo(line.selsource, row, basereq=line.shortage)
            row.append('<--')
        writer.writerow(row)

        if include_others is True:
            for vsinfo in line.other_sources:
                row = [None] * len(self._get_headers(1))
                row = self._render_vsinfo(vsinfo, row)
                writer.writerow(row)

    def dump_to_file(self, fname, include_others=True):
        with open(fname, 'w') as f:
            w = csv.writer(f)
            w.writerow(self._get_headers(0))
            w.writerow(self._get_headers(1))
            w.writerow(self._get_headers(2))

            for line in self._lines:
                self._render_line(line, w, include_others)

    def generate_orders(self, path):
        for line in self._lines:
            if line.is_sourceable is True:
                line.order()
        for vendor in self._allowed_vendors:
            vendor.finalize_order(path)

    def rebalance(self):
        logger.info("Attempting to Rebalance Order")
        shadowlines = copy.copy(self._lines)
        accepted_vendors = []
        # Remove Unsourceable
        rebalance_pass = 0
        logger.debug("Making Rebalance Pass " + str(rebalance_pass)
                     + ": Remaining Lines : " + str(len(shadowlines)))
        # For some unknown reason this doesn't catch all the unsourceable idents in the first pass
        for i in range(5):
            for line in shadowlines:
                if line.is_sourceable is False:
                    logger.debug("Accepting unsourceable line : " + line.ident + " p1." + str(i))
                    shadowlines.remove(line)
        passes = 10
        while passes > 0:
            passes -= 1
            rebalance_pass += 1
            logger.debug("Making Rebalance Pass " + str(rebalance_pass)
                         + ": Remaining Lines : " + str(len(shadowlines)))
            for line in shadowlines:
                try:
                    if line.selsource[0].name in accepted_vendors:
                        logger.debug("Accepting line sourced by standard means : " + line.ident)
                        shadowlines.remove(line)
                    else:
                        if not line.other_sources:
                            logger.info("Accepting Vendor : " + line.selsource[0].name +
                                        " : Unique Source for " + line.ident)
                            accepted_vendors.append(line.selsource[0].name)
                            logger.debug("Accepting uniquely sourced line : " + line.ident)
                            shadowlines.remove(line)
                        elif line.selsource[0].order_baseprice.native_value == 0:
                            logger.info("Accepting Vendor : " + line.selsource[0].name +
                                        " since Base Order Cost is 0")
                            accepted_vendors.append(line.selsource[0].name)
                            shadowlines.remove(line)
                except Exception:
                    print line
                    raise Exception

        candidate_vendors = {}

        while len(shadowlines) > 0:

            for line in shadowlines:
                if line.selsource[0].name not in candidate_vendors.keys():
                    candidate_vendors[line.selsource[0].name] = [line.selsource[0].order_baseprice, 0]
                vsinfo = line.sorted_other_sources[0]
                saving = line.excess(vsinfo)
                candidate_vendors[line.selsource[0].name][1] += saving

            if len(candidate_vendors) > 0:
                cvendors = sorted(candidate_vendors.keys(),
                                  key=lambda x: candidate_vendors[x][1] - candidate_vendors[x][0].native_value,
                                  reverse=True)
                if candidate_vendors[cvendors[0]][1] > candidate_vendors[cvendors[0]][0].native_value:
                    logger.info("Accepting Vendor " + cvendors[0]
                                + " for an estimated saving of "
                                + str(candidate_vendors[cvendors[0]][1] - candidate_vendors[cvendors[0]][0].native_value))
                    accepted_vendors.append(cvendors[0])
                else:
                    break

            passes = 10
            while passes > 0 and len(shadowlines) > 0:
                passes -= 1
                rebalance_pass += 1
                logger.debug("Making Rebalance Pass " + str(rebalance_pass)
                             + ": Remaining Lines : " + str(len(shadowlines)))
                for line in shadowlines:
                    try:
                        if line.selsource[0].name in accepted_vendors:
                            logger.debug("Accepting line sourced by standard means : " + line.ident)
                            shadowlines.remove(line)
                    except Exception:
                        print line
                        raise Exception

        # TODO Anything left which doesn't have an accepted alternate source should trigger vendor acceptance.

        # TODO Anything still left should be switched to accepted sources here.

        logger.info("Finished all Rebalance Passes " + str(rebalance_pass)
                    + ": Remaining Lines : " + str(len(shadowlines)))
        # if len(shadowlines) > 0:
        #     print "Unhandled Idents :"
        # for line in shadowlines:
        #     print line.ident, line.selsource[0].name, len(line.other_sources)
        # print "Accepted Vendors :"
        # for vendor in accepted_vendors:
        #     print vendor

    def collapse(self):
        pass
