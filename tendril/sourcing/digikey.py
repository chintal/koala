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
Digi-Key Sourcing Module documentation (:mod:`sourcing.digikey`)
================================================================
"""

from tendril.utils import log
logger = log.get_logger(__name__, log.DEFAULT)

import locale
import re
import os
import urllib
from decimal import Decimal
import traceback
import csv
import codecs

from bs4 import BeautifulSoup

import vendors
import customs
from tendril.utils import www
from tendril.utils.types import currency
import tendril.conventions.electronics

from tendril.utils.config import INSTANCE_ROOT

locale.setlocale(locale.LC_ALL, 'en_US.UTF-8')


class VendorDigiKey(vendors.VendorBase):
    def __init__(self, name, dname, pclass, mappath=None, currency_code=None, currency_symbol=None, ):
        self._devices = ['IC SMD',
                         'IC THRU',
                         'IC PLCC',
                         'FERRITE BEAD SMD',
                         'TRANSISTOR THRU',
                         'TRANSISTOR SMD',
                         'CONN DF13',
                         'CONN DF13 HOUS',
                         'CONN DF13 WIRE',
                         'CONN DF13 CRIMP',
                         'CONN MODULAR',
                         'DIODE SMD',
                         'DIODE THRU',
                         'VARISTOR',
                         'BRIDGE RECTIFIER',
                         'RES SMD',
                         'RES THRU',
                         'CAP CER SMD',
                         'CAP TANT SMD',
                         'TRANSFORMER SMD',
                         'INDUCTOR SMD',
                         'CRYSTAL AT'
                         ]
        self._ndevices = ['CONN INTERBOARD']
        self._searchpages_filters = {}
        super(VendorDigiKey, self).__init__(name, dname, pclass, mappath, currency_code, currency_symbol)
        self.add_order_baseprice_component("Shipping Cost", 40)
        self.add_order_additional_cost_component("Customs", 12.85)

    def get_vpart(self, vpartno, ident=None):
        if issubclass(DigiKeyElnPart, vendors.VendorElnPartBase):
            return DigiKeyElnPart(vpartno, ident, self)
        else:
            raise TypeError

    def search_vpnos(self, ident):
        device, value, footprint = tendril.conventions.electronics.parse_ident(ident)
        if device not in self._devices:
            return None, 'NODEVICE'
        try:
            if device.startswith('RES') or device.startswith('POT') or \
                    device.startswith('CAP') or device.startswith('CRYSTAL'):
                if tendril.conventions.electronics.check_for_std_val(ident) is False:
                    return self._get_search_vpnos(device, value, footprint)
                try:
                    return self._get_pas_vpnos(device, value, footprint)
                except NotImplementedError:
                    logger.warning(ident + ' :: DK Search for ' + device + ' Not Implemented')
                    return None, 'NOT_IMPL'
            if device in self._devices:
                return self._get_search_vpnos(device, value, footprint)
            else:
                return None, 'FILTER_NODEVICE'
        except Exception:
            logger.error(traceback.format_exc())
            logger.error('Fatal Error searching for : ' + ident)
            return None, None

    @staticmethod
    def _search_preprocess(device, value, footprint):
        # Hail Mary
        if footprint == 'TO220':
            footprint = 'TO-220'
        if footprint == 'TO92':
            footprint = 'TO-92'
        return device, value, footprint

    @staticmethod
    def _process_product_page(soup):
        beablock = soup.find('td', 'beablock-notice')
        if beablock is not None:
            if beablock.text == u'\nObsolete item; call Digi-Key for more information.\n':
                return False, None, 'OBSOLETE_NOTAVAIL'
        pdtable = soup.find('table', attrs={'class': 'product-details'})
        if pdtable is not None:
            pno_cell = pdtable.find('td', id='reportpartnumber')
            pmeta = pno_cell.find('meta')
            pno = pmeta.attrs['content'].split(':')[1].encode('ascii', 'replace')
            return True, [pno], 'EXACT_MATCH'
        else:
            return False, None, ''

    @staticmethod
    def _get_device_catstrings(device):
        if device.startswith('IC'):
            catstrings = ['Integrated Circuits (ICs)',
                          'Isolators']
            subcatstrings = None
        elif device.startswith('DIODE'):
            catstrings = ['Discrete Semiconductor Products']
            subcatstrings = ['Diodes, Rectifiers - Single']
        elif device.startswith('TRANSISTOR'):
            catstrings = ['Discrete Semiconductor Products']
            subcatstrings = ['FETs - Single',
                             'FETs - Arrays',
                             'Transistors (BJT) - Single']
        elif device.startswith('BRIDGE RECTIFIER'):
            catstrings = ['Discrete Semiconductor Products']
            subcatstrings = ['Bridge Rectifiers']
        else:
            return False, None, None
        return True, catstrings, subcatstrings

    def _process_index_page(self, soup, device):
        idxlist = soup.find('ul', id='productIndexList')
        if idxlist is None:
            return False, None, 'NO_RESULTS:0'
        # Handling categories needs to be much better
        indexes = idxlist.findAll('li', attrs={'class': 'catfilteritem'})
        result, catstrings, subcatstrings = self._get_device_catstrings(device)
        if result is False:
            return False, None, 'CATEGORY UNKNOWN'
        newurlpart = None
        for index in indexes:
            if not subcatstrings:
                catname = index.findAll('a')[0].text
                if catname in catstrings:
                    newurlpart = index.find('a').attrs['href']
            else:
                subcats = index.findAll('li')
                for subcat in subcats:
                    if subcat.find('a').text in subcatstrings:
                        newurlpart = subcat.find('a').attrs['href']
        if newurlpart is None:
            return False, None, 'CATEGORY NOT FOUND'
        else:
            return True, newurlpart, ''

    @staticmethod
    def _get_resultpage_row_pno(row):
        pno_cell = row.find('td', attrs={'class': "digikey-partnumber"})
        pmeta = pno_cell.find('meta')
        pno = pmeta.attrs['content'].split(':')[1].encode('ascii', 'replace')
        return pno

    @staticmethod
    def _get_resultpage_row_unitp(row):
        unitp_cell = row.find('td', attrs={'class': "unitprice"})
        unitp_string = unitp_cell.text.strip().encode('ascii', 'replace')
        unitp = None
        try:
            unitp = locale.atof(unitp_string)
        except ValueError:
            pass
        return unitp

    @staticmethod
    def _get_resultpage_row_package(row):
        try:
            package = row.find('td', attrs={'class': 'CLS 16'}).text
        except (TypeError, AttributeError):
            package = None
        return package

    @staticmethod
    def _get_resultpage_row_minqty(row):
        return row.find('td', attrs={'class': 'minQty'}).text

    @staticmethod
    def _get_resultpage_row_mfgpno(row):
        return row.find('td', attrs={'class': 'mfg-partnumber'}).text

    def _process_resultpage_row(self, row):
        pno = self._get_resultpage_row_pno(row)
        unitp = self._get_resultpage_row_unitp(row)
        package = self._get_resultpage_row_package(row)
        minqty = self._get_resultpage_row_minqty(row)
        mfgpno = self._get_resultpage_row_mfgpno(row)
        if 'Non-Stock' in minqty:
            ns = True
        else:
            ns = False
        return pno, mfgpno, package, ns, unitp

    def _get_resultpage_parts(self, soup):
        ptable = soup.find('table', id='productTable')
        if ptable is None:
            return False, None, 'NO_RESULTS:3'
        trs = ptable.find_all('tr')
        if trs is None:
            return False, None, 'NO_RESULTS:1'
        rows = trs[2:]
        parts = []
        for row in rows:
            pno, mfgpno, package, ns, unitp = self._process_resultpage_row(row)
            if unitp is not None:
                parts.append((pno, mfgpno, package, ns))
        return True, parts, ''

    @staticmethod
    def _find_exact_match_package(parts, value):
        for pno, mfgpno, package, ns in parts:
            if mfgpno == value:
                return True, package, 'EXACT_MATCH_FFP'
        return False, None, None

    @staticmethod
    def _find_consensus_package(parts):
        cpackage = parts[0][2]
        for pno, mfgpno, package, ns in parts:
            if package != cpackage:
                cpackage = None
        if cpackage is not None:
            return True, cpackage, 'CONSENSUS_FP_MATCH'
        return False, None, None

    @staticmethod
    def _filter_results_unfiltered(parts):
        pnos = []
        strategy = 'UNFILTERED'
        for pno, mfgpno, package, ns in parts:
            if not ns:
                pnos.append(pno)
        if len(pnos) == 0:
            strategy += '_ALLOW_NS'
            for pno, mfgpno, package, ns in parts:
                pnos.append(pno)
        return True, pnos, strategy

    @staticmethod
    def _filter_results_byfootprint(parts, footprint):
        pnos = []
        strategy = 'HAIL MARY'
        for pno, mfgpno, package, ns in parts:
            if footprint in package:
                if not ns:
                    pnos.append(pno)
        if len(pnos) == 0:
            strategy += ' ALLOW NS'
            for pno, mfgpno, package, ns in parts:
                if footprint in package:

                    pnos.append(pno)
        return True, pnos, strategy

    @staticmethod
    def _filter_results_bycpackage(parts, cpackage, strategy):
        pnos = []
        for pno, mfgpno, package, ns in parts:
            if package == cpackage:
                if not ns:
                    pnos.append(pno)
        if len(pnos) == 0:
            strategy += '_ALLOW_NS'
            for pno, mfgpno, package, ns in parts:
                if package == cpackage:
                    pnos.append(pno)
        return True, pnos, strategy

    def _filter_results(self, parts, value, footprint):
        if parts[0][2] is None or footprint is None:
            # No package, so no basis to filter
            result, pnos, strategy = self._filter_results_unfiltered(parts)
            return True, pnos, strategy

        # Find Exact Match Package
        result, cpackage, strategy = self._find_exact_match_package(parts, value)
        if result is False:
            # Did not find an exact match package. Check for consensus package instead.
            result, cpackage, strategy = self._find_consensus_package(parts)
            if result is False:
                # No exact match, no consensus on package
                result, pnos, strategy = self._filter_results_byfootprint(parts, footprint)
                return True, pnos, strategy

        # cpackage exists
        result, pnos, strategy = self._filter_results_bycpackage(parts, cpackage, strategy)

        if len(pnos) == 0:
            pnos = None

        return True, pnos, strategy

    def _process_results_page(self, soup, value, footprint):
        result, parts, strategy = self._get_resultpage_parts(soup)
        if result is False:
            return False, None, strategy
        if parts is None:
            raise Exception
        if len(parts) == 0:
            return False, None, 'NO_RESULTS:2'
        result, pnos, strategy = self._filter_results(parts, value, footprint)
        return result, pnos, strategy

    def _get_search_vpnos(self, device, value, footprint):
        if value.strip() == '':
            return None, 'NOVALUE'
        device, value, footprint = self._search_preprocess(device, value, footprint)
        url = 'http://www.digikey.com/product-search/en?k=' + urllib.quote_plus(value) + \
              '&mnonly=0&newproducts=0&ColumnSort=0&page=1&stock=0&pbfree=0&rohs=0&quantity=&ptm=0&fid=0&pageSize=500'
        soup = www.get_soup(url)
        if soup is None:
            return None, 'URL_FAIL'
        ptable = soup.find('table', id='productTable')
        if ptable is None:
            # check for single product page
            result, pnos, strategy = self._process_product_page(soup)
            if result is True:
                return pnos, strategy

            # check for index page and get a new soup
            result, newurlpart, strategy = self._process_index_page(soup, device)
            if result is False:
                return None, strategy
            else:
                newurl = 'http://www.digikey.com' + newurlpart
                soup = www.get_soup(newurl)
                if soup is None:
                    return None, 'NEWURL_FAIL'

        result, pnos, strategy = self._process_results_page(soup, value, footprint)
        if result is False:
            return None, strategy
        return pnos, strategy

    @staticmethod
    def _tf_resistance_to_canonical(rstr):
        rstr = rstr.encode('ascii', 'replace')
        rex = re.compile(r'^(?P<num>\d+(.\d+)*)(?P<order>[kKMGT])*$')
        try:
            rparts = rex.search(rstr).groupdict()
        except AttributeError:
            print rstr
            raise AttributeError

        rval = Decimal(rparts['num'])
        if rparts['order'] is None:
            do = 0
            if rval > 1000:
                raise ValueError
            while 1 > rval > 0:
                rval *= 1000
                do += 1
            if do == 0:
                ostr = 'E'
            elif do == 1:
                ostr = 'm'
            elif do == 2:
                ostr = 'u'
            else:
                raise ValueError
        else:
            if rparts['order'] in ['K', 'k']:
                ostr = 'K'
            elif rparts['order'] == 'M':
                ostr = 'M'
            elif rparts['order'] == 'G':
                ostr = 'G'
            elif rparts['order'] == 'T':
                ostr = 'T'
            else:
                raise ValueError(str(rparts))
        vfmt = lambda d: str(d.quantize(Decimal(1)) if d == d.to_integral() else d.normalize())
        return vfmt(rval) + ostr

    @staticmethod
    def _tf_tolerance_to_canonical(tstr):
        tstr = www.strencode(tstr)
        return tstr

    @staticmethod
    def _tf_capacitance_to_canonical(cstr):
        cstr = www.strencode(cstr)
        if cstr == '-':
            return
        if cstr == '*':
            return
        rex = re.compile(r'^(?P<num>\d+(.\d+)*)(?P<order>[pum]F)$')

        try:
            cparts = rex.search(cstr).groupdict()
        except AttributeError:
            raise AttributeError(cstr)

        cval = Decimal(cparts['num'])

        ostr = cparts['order']
        ostrs = ['fF', 'pF', 'nF', 'uF', 'mF']
        oindex = ostrs.index(ostr)

        if cparts['order'] is None:
            raise ValueError
        if cval >= 1000:
            po = 0
            while cval >= 1000:
                cval /= 1000
                po += 1
            if po > 0:
                for i in range(po):
                    oindex += 1
        else:
            do = 0
            while 0 < cval < 1:
                cval *= 1000
                do += 1
            if do > 0:
                for i in range(do):
                    oindex -= 1

        vfmt = lambda d: str(d.quantize(Decimal(1)) if d == d.to_integral() else d.normalize())
        return vfmt(cval) + ostrs[oindex]

    @staticmethod
    def _tf_package_tant_smd(footprint):
        if footprint == 'TANT-B':
            footprint = 'B'
        if footprint == 'TANT-C':
            footprint = 'C'
        if footprint == 'TANT-D':
            footprint = 'D'
        return footprint

    @staticmethod
    def _tf_package_crystal_at(footprint):
        if footprint == 'HC49':
            footprint = ['HC-49S', 'HC49/U', 'HC49/US']
        return footprint

    def _get_searchpage_filters(self, soup):
        filters = {}
        try:
            filtertable = soup.find('table', attrs={'class': 'filters-group'})
            headers = filtertable.find('tr')
            headers = [header.text.encode('ascii', 'replace') for header in headers.findAll('th')]
            fvaluerow = filtertable.findAll('tr')[1]
            fvaluecells = fvaluerow.findAll('td')
            fvalueselects = [cell.find('select') for cell in fvaluecells]
            for idx, header in enumerate(headers):
                optionsoup = fvalueselects[idx].findAll('option')
                options = [(www.strencode(o.text).rstrip('\n'), o.attrs['value']) for o in optionsoup]
                fname = fvalueselects[idx].attrs['name'].encode('ascii', 'replace')
                if header == 'Resistance (Ohms)':
                    options = [(self._tf_resistance_to_canonical(option[0]), option[1]) for option in options]
                elif header == 'Capacitance':
                    options = [(self._tf_capacitance_to_canonical(option[0]), option[1]) for option in options]
                elif header == 'Tolerance':
                    options = [(self._tf_tolerance_to_canonical(option[0]), option[1]) for option in options]
                filters[header] = (fname, options)
        except Exception:
            logger.error(traceback.format_exc())
            logger.error('idx :' + str(idx))
            return False, None
        return True, filters

    @staticmethod
    def _get_default_urlparams():
        params = [('stock', '0'), ('mnonly', '0'), ('newproducts', '0'), ('ColumnSort', '0'), ('page', '1'),
                  ('quantity', '0'), ('ptm', '0'), ('fid', '0'), ('pagesize', '500')]
        return params

    @staticmethod
    def _get_searchurl_res_smd():
        return 'http://www.digikey.com/product-search/en/resistors/chip-resistor-surface-mount/'

    @staticmethod
    def _get_searchurl_res_thru():
        return 'http://www.digikey.com/product-search/en/resistors/through-hole-resistors/'

    @staticmethod
    def _get_searchurl_cap_cer_smd():
        return 'http://www.digikey.com/product-search/en/capacitors/ceramic-capacitors/'

    @staticmethod
    def _get_searchurl_cap_tant_smd():
        return 'http://www.digikey.com/product-search/en/capacitors/tantalum-capacitors/'

    @staticmethod
    def _get_searchurl_crystal():
        return 'http://www.digikey.com/product-search/en/crystals-and-oscillators/crystals/'

    def _get_searchurl_filters(self, searchurl):
        if searchurl in self._searchpages_filters.keys():
            return self._searchpages_filters[searchurl]
        else:
            searchsoup = www.get_soup(searchurl)
            result, filters = self._get_searchpage_filters(searchsoup)
            if result is True:
                self._searchpages_filters[searchurl] = filters
            else:
                raise AttributeError
        return filters

    def _get_pas_vpnos(self, device, value, footprint):
        packagetf = None
        package_header = 'Package / Case'
        package_filter_type = 'contains'
        extraparams = None
        if device == "RES SMD":
            filters = self._get_searchurl_filters(self._get_searchurl_res_smd())
            searchurlbase = self._get_searchurl_res_smd()
            devtype = 'resistor'
        elif device == "RES THRU":
            filters = self._get_searchurl_filters(self._get_searchurl_res_thru())
            searchurlbase = self._get_searchurl_res_thru()
            extraparams = (('Tolerance', '+/-1%'),)
            package_filter_type = None
            devtype = 'resistor'
        elif device == "RES POWER":
            devtype = 'resistor'
            raise NotImplementedError
        elif device == "RES ARRAY THRU":
            devtype = 'resistor'
            raise NotImplementedError
        elif device == "RES SMD THRU":
            devtype = 'resistor'
            raise NotImplementedError
        elif device == "POT TRIM":
            devtype = 'resistor'
            raise NotImplementedError
        elif device == "CAP CER SMD":
            filters = self._get_searchurl_filters(self._get_searchurl_cap_cer_smd())
            searchurlbase = self._get_searchurl_cap_cer_smd()
            devtype = 'capacitor'
        elif device == "CAP TANT SMD":
            filters = self._get_searchurl_filters(self._get_searchurl_cap_tant_smd())
            packagetf = self._tf_package_tant_smd
            searchurlbase = self._get_searchurl_cap_tant_smd()
            package_header = 'Manufacturer Size Code'
            package_filter_type = 'equals'
            devtype = 'capacitor'
        elif device == "CAP CER THRU":
            devtype = 'capacitor'
            raise NotImplementedError
        elif device == "CAP ELEC THRU":
            devtype = 'capacitor'
            raise NotImplementedError
        elif device == "CAP ELEC THRU":
            devtype = 'capacitor'
            raise NotImplementedError
        elif device == "CAP POLY THRU":
            devtype = 'capacitor'
            raise NotImplementedError
        elif device == "CAP PAPER THRU":
            devtype = 'capacitor'
            raise NotImplementedError
        elif device == "CRYSTAL AT":
            filters = self._get_searchurl_filters(self._get_searchurl_crystal())
            packagetf = self._tf_package_crystal_at
            package_filter_type = 'inlist'
            searchurlbase = self._get_searchurl_crystal()
            extraparams = (('Mounting Type', 'Through Hole'),
                           ('Operating Mode', 'Fundamental'))
            devtype = 'crystal'
        else:
            raise ValueError

        if devtype == 'resistor':
            loptions = (('resistance', "Resistance (Ohms)", 'equals'),
                        ('wattage', "Power (Watts)", 'contains'))
            lvalues = tendril.conventions.electronics.parse_resistor(value)
        elif devtype == 'capacitor':
            loptions = (('capacitance', "Capacitance", 'equals'),
                        ('voltage', "Voltage - Rated", 'equals'))
            lvalues = tendril.conventions.electronics.parse_capacitor(value)
        elif devtype == 'crystal':
            loptions = (('frequency', "Frequency", 'equals'),)
            lvalues = [tendril.conventions.electronics.parse_crystal(value)]
        else:
            raise ValueError

        params = self._get_default_urlparams()

        for lidx, loption in enumerate(loptions):
            if lvalues[lidx] is None:
                continue
            dkopcode = None

            for option in filters[loption[1]][1]:
                if loption[2] == 'equals':
                    if option[0] == lvalues[lidx]:
                        dkopcode = option[1]
                elif loption[2] == 'contains':
                    if lvalues[lidx] in option[0]:
                        dkopcode = option[1]
            dkfiltcode = filters[loption[1]][0]
            if dkopcode is None:
                raise ValueError(loption[0] + ' ' + lvalues[lidx])
            params.append((dkfiltcode, dkopcode))

        if packagetf is not None:
            footprint = packagetf(footprint)
        if package_filter_type is not None:
            pkgopcode = None
            for option in filters[package_header][1]:
                if package_filter_type == 'contains':
                    if footprint in option[0]:
                        pkgopcode = option[1]
                elif package_filter_type == 'equals':
                    if footprint == option[0]:
                        pkgopcode = option[1]
                elif package_filter_type == 'inlist':
                    if option[0] in footprint:
                        try:
                            pkgopcode.append(option[1])
                        except AttributeError:
                            pkgopcode = [option[1]]
            if pkgopcode is None:
                raise ValueError(footprint)
            if isinstance(pkgopcode, list):
                for opt in pkgopcode:
                    params.append((filters[package_header][0], opt))
            else:
                params.append((filters[package_header][0], pkgopcode))

        if extraparams is not None:
            for param in extraparams:
                opcode = None
                for option in filters[param[0]][1]:
                    if option[0] == param[1]:
                        opcode = option[1]
                if opcode is None:
                    for option in filters[param[0]][1]:
                        print option[0].decode('unicode-escape')
                    raise ValueError("Param not valid: " + str(param))
                params.append((filters[param[0]][0], opcode))

        searchurl = searchurlbase + '?' + urllib.urlencode(params)

        soup = www.get_soup(searchurl)
        # TODO extract common parts with _get_search_vpnos
        if soup is None:
            return None, 'URL_FAIL'

        ptable = soup.find('table', id='productTable')
        if ptable is None:
            # check for single product page
            result, pnos, strategy = self._process_product_page(soup)
            if result is True:
                return pnos, strategy
            else:
                return None, strategy

        result, pnos, strategy = self._process_results_page(soup, None, None)
        if result is False:
            return None, strategy
        return pnos, strategy


class DigiKeyElnPart(vendors.VendorElnPartBase):
    def __init__(self, dkpartno, ident=None, vendor=None):
        """

        :type vendor: VendorDigiKey
        """
        if vendor is None:
            vendor = VendorDigiKey('digikey', 'transient', 'electronics')
            vendor.currency = currency.CurrencyDefinition('USD', 'US$')
        super(DigiKeyElnPart, self).__init__(ident, vendor)
        if dkpartno is not None:
            self.vpno = dkpartno
        else:
            logger.error("Not enough information to create a Digikey Part")
        self._get_data()

    def _get_data(self):
        url = ('http://search.digikey.com/scripts/DkSearch/dksus.dll?Detail?name='
               + urllib.quote_plus(self.vpno))
        page = www.urlopen(url)
        if page is None:
            logger.error("Unable to open DigiKey product page : " + self.vpno)
            return
        soup = BeautifulSoup(page)

        for price in self._get_prices(soup):
            self.add_price(price)
        try:
            self.mpartno = self._get_mpartno(soup)
            self.manufacturer = self._get_manufacturer(soup)
            self.package = self._get_package(soup)
            self.datasheet = self._get_datasheet_link(soup)
            self.vqtyavail = self._get_avail_qty(soup)
            self.vpartdesc = self._get_description(soup)
        except AttributeError:
            logger.error("Failed to acquire part information : " + self.vpno + url)
            # TODO raise AttributeError

    def _get_prices(self, soup):
        pricingtable = soup.find('table', id='pricing')
        prices = []
        try:
            for row in pricingtable.findAll('tr'):
                cells = row.findAll('td')
                if len(cells) == 3:
                    cells = [cell.text.strip() for cell in cells]
                    try:
                        moq = locale.atoi(cells[0])
                    except ValueError:
                        moq = 0
                        logger.error(cells[0] + " found while acquiring moq for " + self.vpno)
                    try:
                        price = locale.atof(cells[1])
                    except ValueError:
                        price = 0
                        logger.error(cells[1] + " found while acquiring price for " + self.vpno)
                    prices.append(vendors.VendorPrice(moq,
                                                      price,
                                                      self._vendor.currency))
        except AttributeError:
            logger.error("Pricing table not found or other error for " + self.vpno)
        return prices

    @staticmethod
    def _get_mpartno(soup):
        mpart = soup.find('h1', attrs={'class': "seohtag",
                                       'itemprop': "model"})
        return mpart.text.strip().encode('ascii', 'replace')

    @staticmethod
    def _get_manufacturer(soup):
        mfrer = soup.find('h2', attrs={'class': "seohtag",
                                       'itemprop': "manufacturer"})
        return mfrer.text.strip().encode('ascii', 'replace')

    @staticmethod
    def _get_package(soup):
        n = soup.findAll('th', text=re.compile('Package / Case'))
        try:
            package_cell = n[0].find_next_sibling()
            package = package_cell.text.strip().encode('ascii', 'replace')
        except IndexError:
            package = ''
        return package

    @staticmethod
    def _get_datasheet_link(soup):
        n = soup.findAll('th', text=re.compile('Datasheets'))
        try:
            datasheet_cell = n[0].find_next_sibling()
        except IndexError:
            return None
        datasheet_link = datasheet_cell.find_all('a')[0].attrs['href']
        return datasheet_link.strip().encode('ascii', 'replace')

    @staticmethod
    def _get_avail_qty(soup):
        n = soup.find('td', id='quantityavailable')
        try:
            qtytext = n.text.strip().encode('ascii', 'replace')
            rex = re.compile(r'^Digi-Key Stock: (?P<qty>\d+(,*\d+)*)')
            qtytext = rex.search(qtytext).groupdict()['qty'].replace(',', '')
            return int(qtytext)
        except:
            rex2 = re.compile(r'^Value Added Item')
            if rex2.match(n.text.strip().encode('ascii', 'replace')):
                return -2
            return -1

    @staticmethod
    def _get_description(soup):
        try:
            desc_cell = soup.find('td', attrs={'itemprop': 'description'})
            return desc_cell.text.strip().encode('ascii', 'replace')
        except:
            return ''


class DigiKeyInvoice(customs.CustomsInvoice):
    def __init__(self, vendor=None, inv_yaml=None, working_folder=None):
        if vendor is None:
            vendor = VendorDigiKey('digikey', 'DIGIKEY', 'electronics',
                                   currency_code='USD', currency_symbol='US$')
        if inv_yaml is None:
            inv_yaml = os.path.join(INSTANCE_ROOT, 'scratch', 'customs', 'inv_data.yaml')

        super(DigiKeyInvoice, self).__init__(vendor, inv_yaml, working_folder)

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
