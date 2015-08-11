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

import os
import yaml
import re
import csv
import codecs

import iec60063

import vendors
import customs

import tendril.conventions.electronics
from tendril.utils.types import currency
from tendril.utils.config import PRICELISTVENDORS_FOLDER
from tendril.utils.config import INSTANCE_ROOT


class VendorPricelist(vendors.VendorBase):
    def __init__(self, name, dname, pclass, mappath=None,
                 currency_code=None, currency_symbol=None, pricelistpath=None):
        if pricelistpath is None:
            pricelistpath = os.path.join(PRICELISTVENDORS_FOLDER, name + '-pricelist.yaml')
        with open(pricelistpath, 'r') as f:
            self._pricelist = yaml.load(f)
        if currency_code is None:
            currency_code = self._pricelist["currency"]["code"].strip()
        if currency_symbol is None:
            currency_symbol = self._pricelist["currency"]["symbol"].strip()
        self._currency = currency.CurrencyDefinition(currency_code, currency_symbol)
        super(VendorPricelist, self).__init__(name, dname, pclass, mappath,
                                              currency_code, currency_symbol)
        if 'vendorinfo' in self._pricelist:
            if "effectivefactor" in self._pricelist["vendorinfo"]:
                self.add_order_additional_cost_component("Unspecified",
                                                         self._pricelist["vendorinfo"]["effectivefactor"] * 100)
        try:
            self.add_order_baseprice_component("Shipping Cost", self._pricelist["vendorinfo"]["shippingcost"])
        except KeyError:
            pass
        if "prices" not in self._pricelist:
            try:
                pass
            except:
                logger.error("No prices found for " + self.name)
        if "pricegens" in self._pricelist:
            self._generate_insert_idents()
        if "pricecsv" in self._pricelist:
            self._load_pricecsv(self._pricelist["pricecsv"])

    def _load_pricecsv(self, fname):
        pricecsvpath = os.path.join(PRICELISTVENDORS_FOLDER, fname)
        with open(pricecsvpath, 'r') as f:
            reader = csv.reader(f)
            for line in reader:
                line = [elem.strip() for elem in line]
                if line[0] == '':
                    continue
                if line[0] == 'ident':
                    continue
                partdict = {'ident': line[0], 'vpno': line[1],
                            'unitp': float(line[2]), 'moq': int(line[3]),
                            'oqmultiple': int(line[4]), 'pkgqty': int(line[5])}
                try:
                    partdict['avail'] = int(line[6])
                except ValueError:
                    partdict['avail'] = None
                self._pricelist["prices"].append(partdict)

    def _generate_insert_idents(self):
        for pricegen in self._pricelist['pricegens']:
                if pricegen['vpno'] != 'ident':
                    logger.error("Unknown VPNO transform : " +
                                 pricegen['device'] + "" + pricegen['value'])
                idents = self._get_generator_idents(pricegen)
                for ident in idents:
                    partdict = pricegen.copy()
                    partdict['vpno'] = ident
                    partdict['ident'] = ident
                    self._pricelist["prices"].append(partdict)

    def _get_generator_idents(self, pricegen):
        return [tendril.conventions.electronics.ident_transform(pricegen['device'],
                                                              x,
                                                              pricegen['footprint'])
                for x in self._get_generator_values(pricegen)]

    @staticmethod
    def _get_generator_values(pricegen):
        """
        TODO This function should be parcelled out to conventions
        :param gendata:
        :return:
        """
        if pricegen['type'] == 'simple':
            return pricegen['values']
        values = []

        if pricegen['type'] == 'resistor':
            if 'resistances' in pricegen.keys():
                for resistance in pricegen['resistances']:
                    values.append(resistance)
            if 'generators' in pricegen.keys():
                for generator in pricegen['generators']:
                    if generator['std'] == 'iec60063':
                        rvalues = iec60063.gen_vals(generator['series'],
                                                    iec60063.res_ostrs,
                                                    start=generator['start'],
                                                    end=generator['end'])
                        for rvalue in rvalues:
                            values.append(tendril.conventions.electronics.construct_resistor(rvalue, generator['wattage']))
                    else:
                        raise ValueError
            if 'values' in pricegen.keys():
                if pricegen['values'][0].strip() != '':
                    values += pricegen['values']
            return values

        if pricegen['type'] == 'capacitor':
            if 'capacitances' in pricegen.keys():
                for capacitance in pricegen['capacitances']:
                        values.append(capacitance)
            if 'generators' in pricegen.keys():
                for generator in pricegen['generators']:
                    if generator['std'] == 'iec60063':
                        cvalues = iec60063.gen_vals(generator['series'],
                                                    iec60063.cap_ostrs,
                                                    start=generator['start'],
                                                    end=generator['end'])
                        for cvalue in cvalues:
                            values.append(tendril.conventions.electronics.construct_capacitor(cvalue, generator['voltage']))
                    else:
                        raise ValueError
            if 'values' in pricegen.keys():
                if pricegen['values'][0].strip() != '':
                    values += pricegen['values']
            return values

    def search_vpnos(self, ident):
        vplist = []
        for part in self._pricelist['prices']:
            if part['ident'] == ident:
                vplist.append(part['vpno'].strip())
        if len(vplist) > 0:
            return vplist, 'MANUAL'
        else:
            return vplist, 'UNDEF'

    def get_vpart(self, vpartno, ident=None):
        vp_dict = self._pl_get_vpart_dict(vpartno)
        if ident is not None:
            if vp_dict['ident'].strip() != ident:
                logger.warning('Specified Ident does not match Pricelist Defined Ident : '
                               + vp_dict['ident'].strip())
        return PricelistPart(vp_dict, ident, self)

    def _pl_get_vpart_dict(self, vpartno):
        for part in self._pricelist["prices"]:
            if part['vpno'].strip() == vpartno:
                return part

    def get_optimal_pricing(self, ident, rqty):
        candidate_names = self.get_vpnos(ident)

        candidates = [self.get_vpart(x) for x in candidate_names]
        if len(candidates) == 0:
            return self, None, None, None, None, None, None, None

        selcandidate = candidates[0]
        tcost, oqty, price = selcandidate.get_price_qty(rqty)
        if len(candidates) > 1:
            for candidate in candidates:
                ltcost, loqty, lprice = candidate.get_price_qty(rqty)
                if ltcost < tcost and (selcandidate.vqtyavail is not None and selcandidate.vqtyavail < oqty):
                    tcost = ltcost
                    selcandidate = candidate
                    oqty = loqty
                    price = lprice
        else:
            if selcandidate.vqtyavail is not None and selcandidate.vqtyavail < oqty:
                return self, None, None, None, None, None, None, None
        effprice = self.get_effective_price(price)
        return self, selcandidate.vpno, oqty, None, price, effprice, "Vendor MOQ/GL", None


class PricelistPart(vendors.VendorPartBase):
    def __init__(self, vp_dict, ident, vendor):
        self._vendor = vendor
        super(PricelistPart, self).__init__(ident, vendor)
        self.vpno = vp_dict['vpno'].strip()
        if 'pkgqty' in vp_dict.keys():
            self.pkgqty = vp_dict['pkgqty']
        if 'availqty' in vp_dict.keys():
            self._vqtyavail = vp_dict['availqty']
        else:
            self._vqtyavail = None
        self._get_prices(vp_dict)

    def _get_prices(self, vp_dict):
        rex = re.compile(ur'^unitp@(?P<moq>\d+)$')
        for k, v in vp_dict.iteritems():
            try:
                moq = rex.match(k).group(1)
                price = vendors.VendorPrice(int(moq), float(v),
                                            self._vendor.currency,
                                            vp_dict['oqmultiple'])
                self._prices.append(price)
            except AttributeError:
                pass
        if len(self._prices) == 0:
            price = vendors.VendorPrice(vp_dict['moq'], vp_dict['unitp'], self._vendor.currency,
                                        vp_dict['oqmultiple'])
            self._prices.append(price)

    def get_price_qty(self, qty):
        lcost = None
        lprice = None
        loqty = None
        for price in self._prices:
            tqty = 0
            while tqty < qty or tqty < price.moq:
                tqty += price.oqmultiple
            tcost = price.extended_price(tqty).native_value
            if lcost is None or tcost < lcost:
                lcost = tcost
                lprice = price
                loqty = tqty
        return lcost, loqty, lprice


class AnalogDevicesInvoice(customs.CustomsInvoice):
    def __init__(self, vendor=None, inv_yaml=None, working_folder=None):
        if vendor is None:
            vendor = VendorPricelist('analogdevices', 'Analog Devices Inc', 'electronics')
        if inv_yaml is None:
            inv_yaml = os.path.join(INSTANCE_ROOT, 'scratch', 'customs', 'inv_data.yaml')

        super(AnalogDevicesInvoice, self).__init__(vendor, inv_yaml, working_folder)

    def _acquire_lines(self):
        logger.info("Acquiring Lines")
        invoice_file = os.path.join(self._source_folder, self._data['invoice_file'])
        with open(invoice_file) as f:
            reader = csv.reader(f)
            header = None
            for line in reader:
                if line[0].startswith(codecs.BOM_UTF8):
                    line[0] = line[0][3:]
                if line[0] == 'Index':
                    header = line
                    break
            if header is None:
                raise ValueError
            for line in reader:
                if line[0] != '':
                    idx = line[header.index('Index')].strip()
                    qty = int(line[header.index('Quantity')].strip())
                    vpno = line[header.index('Part Number')].strip()
                    # mpno = line[header.index('Manufacturer Part Number')].strip()
                    desc = line[header.index('Description')].strip()
                    ident = line[header.index('Customer Reference')].strip()
                    boqty = line[header.index('Backorder')].strip()
                    try:
                        if int(boqty) > 0:
                            logger.warning("Apparant backorder. Crosscheck customs treatment for: "
                                           + idx + ' ' + ident)
                    except ValueError:
                        print line

                    unitp_str = line[header.index('Unit Price')].strip()
                    # extendedp_str = line[header.index('Extended Price')].strip()

                    unitp = currency.CurrencyValue(float(unitp_str), self._vendor.currency)
                    lineobj = customs.CustomsInvoiceLine(self, ident, vpno, unitp, qty, idx=idx, desc=desc)
                    self._lines.append(lineobj)
