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

import yaml
import os

import vendors
from tendril.gedaif import gsymlib
from tendril.utils.types import currency
from tendril.utils.config import CUSTOMSDEFAULTS_FOLDER


class CustomsSection(object):
    def __init__(self, code, hsdict):
        self._code = code
        if 'name' in hsdict.keys():
            self._name = hsdict['name']
        else:
            self._name = None
        if 'idents' in hsdict.keys():
            self._idents = hsdict['idents']
        else:
            self._idents = None
        if 'folders' in hsdict.keys():
            self._folders = hsdict['folders']
        else:
            self._folders = None
        if 'desc' in hsdict.keys():
            self._desc = hsdict['desc']
        else:
            self._desc = None
        self.bcd = None
        self.bcd_notif = None
        self.cvd = None
        self.cvd_notif = None
        self.acvd = None
        self.acvd_notif = None
        self.cec = None
        self.cec_notif = None
        self.cshec = None
        self.cshec_notif = None
        self.cvdec = None
        self.cvdec_notif = None
        self.cvdshec = None
        self.cvdshec_notif = None

        if 'duties' in hsdict.keys():
            self._load_duties(hsdict['duties'])

    def _load_duties(self, dutiesdict):
        self.bcd = dutiesdict['bcd']['rate']
        self.bcd_notif = dutiesdict['bcd']['notification']
        self.cvd = dutiesdict['cvd']['rate']
        self.cvd_notif = dutiesdict['cvd']['notification']
        self.acvd = dutiesdict['acvd']['rate']
        self.acvd_notif = dutiesdict['acvd']['notification']
        self.cec = dutiesdict['cec']['rate']
        self.cec_notif = dutiesdict['cec']['notification']
        self.cshec = dutiesdict['cshec']['rate']
        self.cshec_notif = dutiesdict['cshec']['notification']
        self.cvdec = dutiesdict['cvdec']['rate']
        self.cvdec_notif = dutiesdict['cvdec']['notification']
        self.cvdshec = dutiesdict['cvdshec']['rate']
        self.cvdshec_notif = dutiesdict['cvdshec']['notification']

    @property
    def code(self):
        return self._code

    @property
    def name(self):
        return self._name

    @property
    def desc(self):
        return self._desc

    @property
    def idents(self):
        return self._idents

    @property
    def folders(self):
        return self._folders

    def __repr__(self):
        return "{0:<15} {1}".format(self._code, self.name)


class CustomsClassifier(object):
    def __init__(self):
        self._sections = []
        self._load_sections()

    def _load_sections(self):
        hs_codes_file = os.path.join(CUSTOMSDEFAULTS_FOLDER, 'hs_codes.yaml')
        with open(hs_codes_file, 'r') as f:
            data = yaml.load(f)
            for section, sectiondict in data['sections'].iteritems():
                self._sections.append(CustomsSection(section, sectiondict))

    def hs_from_ident(self, ident):
        for section in self._sections:
            if section.idents is not None:
                for sign in section.idents:
                    if sign in ident:
                        return section
        rsign = ''
        rsec = None
        for section in self._sections:
            if section.folders is not None:
                for sign in section.folders:
                    if sign in gsymlib.get_symbol_folder(ident, True):
                        if rsign in sign:
                            rsec = section
                            rsign = sign
        return rsec

hs_classifier = CustomsClassifier()


class CustomsInvoice(vendors.VendorInvoice):
    def __init__(self, vendor, inv_yaml, working_folder=None):
        vendor_defaults_file = os.path.join(CUSTOMSDEFAULTS_FOLDER, vendor._name + '.yaml')
        self._data = {}
        if os.path.exists(vendor_defaults_file):
            with open(vendor_defaults_file, 'r') as f:
                vendor_defaults = yaml.load(f)
                self._data = vendor_defaults.copy()
        else:
            logger.warning("Vendor Customs Defaults File Not Found : " + vendor_defaults_file)
        self._source_folder = os.path.split(inv_yaml)[0]
        if working_folder is None:
            self._working_folder = self._source_folder
        else:
            self._working_folder = working_folder
        with open(inv_yaml, 'r') as f:
            inv_data = yaml.load(f)
            self._data.update(inv_data)
        self._linetype = CustomsInvoiceLine
        vendor.currency = currency.CurrencyDefinition(vendor.currency.code,
                                                      vendor.currency.symbol,
                                                      exchval=self._data['exchrate'])
        super(CustomsInvoice, self).__init__(vendor, self._data['invoice_no'], self._data['invoice_date'])

        self.freight = 0
        self.insurance_pc = 0
        self._includes_freight = False
        self._added_insurance = False
        self._process_other_costs()
        hs_codes_file = os.path.join(CUSTOMSDEFAULTS_FOLDER, 'hs_codes.yaml')
        with open(hs_codes_file, 'r') as f:
            self._hs_codes = yaml.load(f)
        self._sections = []

    @property
    def given_data(self):
        return self._data

    def _process_other_costs(self):
        for k, v in self._data['costs_not_included'].iteritems():
            if v is False:
                self._data['costs_not_included'][k] = 'None'
            elif v == 'INCL':
                self._data['costs_not_included'][k] = 'None, included in Invoice'
            elif v == 'LISTED':
                self._data['costs_not_included'][k] = 'Listed in Invoice'
            else:
                logger.warning("Unrecognized Other Costs definition for " + k + " : " + v)

        if self._data['costs_not_included']['FREIGHT'] == 'None, included in Invoice':
            self.freight = currency.CurrencyValue(float(self._data['shipping_cost_incl']),
                                                  self._vendor.currency)
            self._data['costs_not_included']['FREIGHT'] += " ({0})".format(self.freight.source_string)
            self._includes_freight = True
        if self._data['costs_not_included']['FREIGHT'] == 'Listed in Invoice':
            self.freight = currency.CurrencyValue(float(self._data['shipping_cost_listed']),
                                                  self._vendor.currency)
            self._data['costs_not_included']['FREIGHT'] = "{0} (as listed in the invoice)".format(self.freight.source_string)
            self._includes_freight = True

        if 'insurance_pc' in self._data.keys():
            self.insurance_pc = float(self._data['insurance_pc'])
            if self.insurance_pc > 0:
                self._added_insurance = True
                self._data['costs_not_included']['INSURANCE'] = "{0} (@{1}% {2})".format(self.insurance.source_string, self.insurance_pc, self._data['insurance_note'])

        if 'handling_pc' in self._data.keys():
            self.handling_pc = float(self._data['handling_pc'])
            if self.handling_pc > 0:
                self._added_handling = True
                self._data['costs_not_included']['LANDING'] = "{0} (@{1}% {2})".format(self.landing.source_string, self.handling_pc, self._data['handling_note'])

    @property
    def insurance(self):
        if self.insurance_pc is not None:
            return self.extendedtotal * self.insurance_pc / 100
        else:
            return self.extendedtotal * 0

    @property
    def includes_freight(self):
        return self._includes_freight

    @property
    def landing(self):
        return self.cif * self.handling_pc / 100

    @property
    def cif(self):
        return self.extendedtotal + self.freight + self.insurance

    @property
    def added_insurance(self):
        try:
            return self._added_insurance
        except AttributeError:
            return False

    @property
    def added_handling(self):
        try:
            return self._added_handling
        except AttributeError:
            return False

    @property
    def source_folder(self):
        return self._source_folder

    @property
    def working_folder(self):
        return self._working_folder

    @property
    def source_files(self):
        rval = [(os.path.join(self._source_folder, 'inv_data.yaml'), 'INVOICE-DATA-YAML'),
                (os.path.join(self._source_folder, self._data['invoice_file']), 'INVOICE-FILE-CSV')]
        return rval

    @property
    def idxs(self):
        return [x.idx for x in self._lines]

    def _acquire_lines(self):
        raise NotImplementedError

    @property
    def hssections(self):
        rval = []
        for line in self._lines:
            if line.hs_section is None:
                continue
            if line.hs_section not in rval:
                rval.append(line.hs_section)
        return sorted(rval, key=lambda x: x.code)

    def getsection_lines(self, hssection):
        rval = []
        for line in self._lines:
            if line.hs_section == hssection:
                rval.append(line)
        return rval

    def getsection_idxs(self, hssection):
        rval = []
        for line in self.getsection_lines(hssection):
            rval.append(line.idx)
        return rval

    def getsection_qty(self, hssection):
        rval = 0
        for line in self.getsection_lines(hssection):
            rval += line.qty
        return rval

    def getsection_assessabletotal(self, hssection):
        rval = 0
        for line in self.getsection_lines(hssection):
            rval += line.assessableprice
        return rval

    @property
    def unclassified(self):
        rval = []
        for line in self._lines:
            if line.hs_section is None:
                rval.append(line)
        return rval

    @property
    def assessabletotal(self):
        return sum([x.assessableprice for x in self._lines])

    @property
    def bcd(self):
        return sum([x.bcd.value for x in self.lines])

    @property
    def cvd(self):
        return sum([x.cvd.value for x in self.lines])

    @property
    def cec(self):
        return sum([x.cec.value for x in self.lines])

    @property
    def cshec(self):
        return sum([x.cshec.value for x in self.lines])

    @property
    def cvdec(self):
        return sum([x.cvdec.value for x in self.lines])

    @property
    def cvdshec(self):
        return sum([x.cvdshec.value for x in self.lines])

    @property
    def acvd(self):
        return sum([x.acvd.value for x in self.lines])

    @property
    def dutypayable(self):
        return self.bcd + self.cvd + self.cec + self.cshec + self.cvdec + self.cvdshec + self.acvd

    @property
    def effectiverate_cif(self):
        return (self.dutypayable / self.assessabletotal) * 100

    @property
    def effectiverate_fob(self):
        return (self.dutypayable / self.extendedtotal) * 100


class DutyComponent(object):
    def __init__(self, title, rate, notification, value):
        self.title = title
        self.rate = rate
        self.notification = notification
        self.value = value

    def __repr__(self):
        return "{0:>50} (@{1:>5}%) : {2:>13}   Notification : {3}".format(self.title, self.rate, self.value.native_string, self.notification)


class CustomsInvoiceLine(vendors.VendorInvoiceLine):
    def __init__(self, invoice, ident, vpno, unitp, qty, idx=None, desc=None):
        if idx is None:
            idx = max(invoice.idxs) + 1
        super(CustomsInvoiceLine, self).__init__(invoice, ident, vpno, unitp, qty, desc=desc)
        if idx in invoice.idxs:
            raise ValueError
        self._idx = idx

    @property
    def dutypayable(self):
        return self.bcd.value + self.cvd.value + self.cec.value + self.cshec.value + \
            self.cvdec.value + self.cvdshec.value + self.acvd.value

    @property
    def idx(self):
        return self._idx

    @property
    def hs_section(self):
        try:
            hs_section = hs_classifier.hs_from_ident(self.ident)
        except ValueError:
            hs_section = None

        if hs_section is None:
            logger.warning("Could not classify : " + self.ident)
        return hs_section

    @property
    def bcd(self):
        return DutyComponent("BCD", self.hs_section.bcd, self.hs_section.bcd_notif,
                             self.assessableprice * self.hs_section.bcd / 100.0)

    @property
    def cvd(self):
        return DutyComponent("CVD", self.hs_section.cvd, self.hs_section.cvd_notif,
                             (self.assessableprice + self.bcd.value) * self.hs_section.cvd / 100.0)

    @property
    def cec(self):
        return DutyComponent("C EC", self.hs_section.cec, self.hs_section.cec_notif,
                             (self.bcd.value + self.cvd.value + self.cvdec.value + self.cvdshec.value) * self.hs_section.cec / 100.0)

    @property
    def cshec(self):
        return DutyComponent("C SHEC", self.hs_section.cshec,
                             self.hs_section.cshec_notif,
                             (self.bcd.value + self.cvd.value + self.cvdec.value + self.cvdshec.value) * self.hs_section.cshec / 100.0)

    @property
    def cvdec(self):
        return DutyComponent("CVD EC", self.hs_section.cvdec, self.hs_section.cvdec_notif,
                             self.cvd.value * self.hs_section.cvdec / 100.0)

    @property
    def cvdshec(self):
        return DutyComponent("CVD SHEC", self.hs_section.cvdshec,
                             self.hs_section.cvdshec_notif,
                             self.cvd.value * self.hs_section.cvdshec / 100.0)

    @property
    def acvd(self):
        return DutyComponent("SAD", self.hs_section.acvd,
                             self.hs_section.acvd_notif,
                             (self.assessableprice + self.bcd.value + self.cvd.value + self.cec.value + self.cshec.value + self.cvdec.value + self.cvdshec.value) * self.hs_section.acvd / 100.0)

    @property
    def invoice_fraction(self):
        return self.extendedprice / self._invoice.extendedtotal

    @property
    def freight(self):
        if self._invoice.freight is None:
            return 0
        return self._invoice.freight * self.invoice_fraction

    @property
    def insurance(self):
        if self._invoice.insurance_pc is None:
            return 0
        return self.extendedprice * (self._invoice.insurance_pc / 100.0)

    @property
    def cifprice(self):
        return self.extendedprice + self.freight + self.insurance

    @property
    def handling(self):
        if self._invoice.handling_pc is None:
            return 0
        return self.cifprice * (self._invoice.handling_pc / 100.0)

    @property
    def assessableprice(self):
        rval = self.extendedprice
        rval += self.freight
        rval += self.insurance
        rval += self.handling
        return rval

    def print_duties(self):
        print "{0:>60} : {2:>13}  {3:>13}".format("Extended Value", '', self.extendedprice.native_string, self.extendedprice.source_string)
        print "{0:>60} : {2:>13}".format("Freight Value", '', self.freight, '')
        print "{0:>60} : {2:>13}".format("Insurance Value", '', self.insurance, '')
        print "{0:>60} : {2:>13}".format("Handling Value", '', self.handling, '')
        print "{0:>60} : {2:>13}".format("Assessable Value", '', self.assessableprice, '')
        print self.bcd
        print self.cvd
        print self.cec
        print self.cshec
        print self.cvdec
        print self.cvdshec
        print self.acvd

    def __repr__(self):
        if self.hs_section is not None:
            return "{0:<3} {1:<40} {2:<35} {3:>10} {4:>15}".format(self.idx, self._ident, self._desc, self.hs_section.code, self.hs_section.name)
        else:
            return "{0:<3} {1:<40} {2:<35} {3:>10} {4:>15}".format(self.idx, self._ident, self._desc, '----------', 'Unclassified')
