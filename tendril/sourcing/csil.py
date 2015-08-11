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
CSIL Sourcing Module documentation (:mod:`sourcing.csil`)
=========================================================
"""

from tendril.utils import log
logger = log.get_logger(__name__, log.INFO)

import time
import locale
import os
import yaml
from collections import OrderedDict

import splinter

from selenium.webdriver.remote.remote_connection import LOGGER
LOGGER.setLevel(log.WARNING)
import selenium.common.exceptions


import vendors

from tendril.utils import fs
from tendril.utils.types import currency
from tendril.utils.progressbar.progressbar import ProgressBar

# from utils.config import NETWORK_PROXY_IP
# from utils.config import NETWORK_PROXY_PORT

from tendril.utils.config import VENDORS_DATA

from tendril.gedaif import projfile
from tendril.entityhub import projects
from tendril.dox import purchaseorder

user = None
pw = None


def get_credentials():
    global user
    global pw
    for vendor in VENDORS_DATA:
        if vendor['name'] == 'csil':
            user = vendor['user']
            pw = vendor['pw']

get_credentials()


locale.setlocale(locale.LC_ALL, 'en_US.UTF-8')

exparams = {
    'pcbname': 'QASC-',
    'layers': 2,
    'dX': '109',
    'dY': '151',
    'qty': range(70),
    'time': 10,      # 5, 7, 10, 12, 15, 18, 21, 25, 30
    'finish': 'Au',  # HAL, Sn, Au, PBFREE, H, NP, I, OC
}


def get_csil_prices(params=exparams, rval=None):
    if rval is None:
        rval = {}
    delivery_codes = {
        3: '3#333',
        5: '5#334',
        7: '7#529',
        10: '10#1452',
        12: '12#7271',
        15: '15#1453',
        18: '18#7272',
        21: '21#7273'
    }

    delivery_times = sorted(delivery_codes.keys())

    layers_codes = {
        1: '2180',
        2: '2181',
        4: '2183',
        6: '2184',
    }

    # proxyIP = NETWORK_PROXY_IP
    # proxyPort = int(NETWORK_PROXY_PORT)

    # proxy_settings = {'network.proxy.type': 1,
    #                   'network.proxy.http': proxyIP,
    #                   'network.proxy.http_port': proxyPort,
    #                   'network.proxy.ssl': proxyIP,
    #                   'network.proxy.ssl_port': proxyPort,
    #                   'network.proxy.socks': proxyIP,
    #                   'network.proxy.socks_port':proxyPort,
    #                   'network.proxy.ftp': proxyIP,
    #                   'network.proxy.ftp_port':proxyPort
    #                   }

    # browser = splinter.Browser('firefox', profile_preferences=proxy_settings)
    browser = splinter.Browser('firefox')
    url = 'http://www.pcbpower.com:8080'
    browser.visit(url)
    values = {
        'ctl00$ContentPlaceHolder1$txtUserName': user,
        'ctl00$ContentPlaceHolder1$txtPassword': pw
    }
    browser.fill_form(values)
    button = browser.find_by_name('ctl00$ContentPlaceHolder1$btnlogin')
    button.click()
    link = browser.find_by_id('ctl00_aPlaceOrder')
    link.click()

    values = OrderedDict()
    values['ctl00$ContentPlaceHolder1$txtPCBName'] = params['pcbname']
    values['ctl00$ContentPlaceHolder1$ddlLayers'] = layers_codes[params['layers']]
    values['ctl00$ContentPlaceHolder1$txtDimX'] = params['dX']
    values['ctl00$ContentPlaceHolder1$txtDimY'] = params['dY']
    if 'qty' in params.keys():
        values['ctl00$ContentPlaceHolder1$txtQuantity'] = str(params['qty'][1])
    else:
        values['ctl00$ContentPlaceHolder1$txtQuantity'] = '1'
    values['ctl00$ContentPlaceHolder1$DDLsurfacefinish'] = params['finish']
    if 'time' in params.keys():
        values['ctl00$ContentPlaceHolder1$ddlDelTerms'] = delivery_codes[params['time']]
    else:
        values['ctl00$ContentPlaceHolder1$ddlDelTerms'] = delivery_codes[5]

    if not browser.is_element_present_by_id('shortNotiText', wait_time=100):
        raise Exception
    ready = False
    timeout = 10
    while not ready and timeout:
        el = browser.find_by_id('shortNotiText')
        if el[0].text == u"We're online":
            ready = True
        timeout -= 1
        time.sleep(1)
    time.sleep(5)
    browser.fill_form(values)

    browser.fill_form(values)

    try:
        oldt = browser.find_by_id('ctl00_ContentPlaceHolder1_lblUnitPrc').text
    except AttributeError:
        oldt = ''
    # qty = str(params['qty'][1])
    # oldv = qty
    time.sleep(2)
    button = browser.find_by_id('ctl00_ContentPlaceHolder1_btnCalculate')

    button.click()
    time.sleep(2)
    button = browser.find_by_id('ctl00_ContentPlaceHolder1_btnCalculate')

    button.click()

    try:
        newt = browser.find_by_id('ctl00_ContentPlaceHolder1_lblUnitPrc').text
    except AttributeError:
        newt = ''
    try:
        newtt = browser.find_by_id('ctl00_ContentPlaceHolder1_lblTotalPrice').text
    except AttributeError:
        newtt = ''
    while oldt == newt:
        try:
            newt = browser.find_by_id('ctl00_ContentPlaceHolder1_lblUnitPrc').text
        except AttributeError:
            newt = ''
        try:
            newtt = browser.find_by_id('ctl00_ContentPlaceHolder1_lblTotalPrice').text
        except AttributeError:
            newtt = ''
        time.sleep(0.5)
    oldt = newt
    oldtt = newtt
    pb = ProgressBar('red', block='#', empty='.')
    for qty in params['qty'][2:]:
        lined = {}
        while browser.find_by_name('ctl00$ContentPlaceHolder1$txtQuantity')[0].value != '':
            browser.type('ctl00$ContentPlaceHolder1$txtQuantity', '\b')
            time.sleep(0.1)
        browser.type('ctl00$ContentPlaceHolder1$txtQuantity', str(qty))
        time.sleep(0.1)
        browser.type('ctl00$ContentPlaceHolder1$txtQuantity', '\t')
        if qty > 4:
            loi = [10]
        else:
            loi = [10]
        percentage = (float(qty) / max(params['qty'])) * 100.00
        pb.render(int(percentage),
                  "\n{0:>7.4f}% {1:<40} Qty: {2:<10} DTS: {3:<4}\nGenerating PCB Pricing".format(
                      percentage, params['pcbname'], qty, loi)
                  )
        for dt_s in loi:
            dt_idx = delivery_times.index(dt_s)
            dts = delivery_times[dt_idx:dt_idx + 3]
            browser.select('ctl00$ContentPlaceHolder1$ddlDelTerms', delivery_codes[dt_s])
            time.sleep(1)
            while True:
                try:
                    try:
                        newt = browser.find_by_id('ctl00_ContentPlaceHolder1_lblUnitPrc').text
                    except AttributeError:
                        newt = ''
                    try:
                        # newt1 = ''
                        # newt2 = ''
                        newt1 = browser.find_by_id('ctl00_ContentPlaceHolder1_lblnextunitprc1').text
                        newt2 = browser.find_by_id('ctl00_ContentPlaceHolder1_lblnextunitprc2').text
                    except AttributeError:
                        newt1 = ''
                        newt2 = ''
                    break
                except selenium.common.exceptions.StaleElementReferenceException:
                    logger.warning("Selenium Exception Caught. Retrying")
                    continue

            timeout = 25
            while oldt == newt and oldtt == newtt and newt is not '' and timeout > 0:
                timeout -= 1
                time.sleep(1)
                while True:
                    try:
                        try:
                            newt = browser.find_by_id('ctl00_ContentPlaceHolder1_lblUnitPrc').text
                        except AttributeError:
                            newt = ''
                        try:
                            # newt1 = ''
                            # newt2 = ''
                            newt1 = browser.find_by_id('ctl00_ContentPlaceHolder1_lblnextunitprc1').text
                            newt2 = browser.find_by_id('ctl00_ContentPlaceHolder1_lblnextunitprc2').text
                        except AttributeError:
                            newt1 = ''
                            newt2 = ''
                        break
                    except selenium.common.exceptions.StaleElementReferenceException:
                        logger.warning("Selenium Exception Caught. Retrying")
                        continue
                try:
                    newtt = browser.find_by_id('ctl00_ContentPlaceHolder1_lblTotalPrice').text
                except AttributeError:
                    newtt = ''
            try:
                lined[dts[0]] = locale.atof(newt)
                if newt1 != '':
                    lined[dts[1]] = locale.atof(newt1)
                if newt2 != '':
                    lined[dts[2]] = locale.atof(newt2)
            except ValueError:
                logger.warning("Caught Exception at CSIL Website. Retrying.")
                browser.quit()
                return get_csil_prices(params, rval)
            oldt = newt
            oldtt = newtt
        params['qty'].remove(qty)
        # print lined
        rval[qty] = lined
    browser.quit()
    return rval


class VendorCSIL(vendors.VendorBase):
    def __init__(self, name, dname, pclass, mappath=None,
                 currency_code=None, currency_symbol=None,
                 username=None, password=None):
        self._username = username
        self._password = password
        self._devices = ['PCB']
        super(VendorCSIL, self).__init__(name, dname, pclass, mappath, currency_code, currency_symbol)
        self.add_order_additional_cost_component("Excise (12.5\%)", 12.5)
        self.add_order_additional_cost_component("CST (5\%)", 5.625)

    def search_vpnos(self, ident):
        pass

    def get_vpart(self, vpartno, ident=None):
        return CSILPart(vpartno, ident, self)

    def get_optimal_pricing(self, ident, rqty):
        # return super(VendorCSIL, self).get_optimal_pricing(ident, rqty)
        candidate_names = self.get_vpnos(ident)
        candidates = [self.get_vpart(x) for x in candidate_names]

        if len(candidates) == 0:
            return self, None, None, None, None, None

        candidate = candidates[0]
        if len(candidate._prices) == 0:
            return self, None, None, None, None, None
        ubprice, nbprice, urationale, olduprice = candidate.get_price(rqty)
        oqty = ubprice.moq
        effprice = self.get_effective_price(ubprice)
        return self, candidate.vpno, oqty, nbprice, ubprice, effprice, urationale, olduprice

    def _generate_purchase_order(self, path):
        stagebase = super(VendorCSIL, self)._generate_purchase_order(path)
        if stagebase is not None:
            stagebase = {}
        for line in self._order.lines:
            stage = stagebase
            stage['intref'] = self._order.orderref
            stage['username'] = user
            stage['name'] = line[2]
            stage['qty'] = line[3]
            stage['unitp'] = line[5].unit_price.source_value
            totalv = line[5].extended_price(line[3]).source_value
            stage['totalp'] = totalv
            addl_costs = self.get_additional_costs(line[5].extended_price(line[3]))
            stage['addl_costs'] = [{'desc': x[0], 'cost': x[1]} for x in addl_costs]
            for desc, cost in addl_costs:
                totalv += cost
            stage['total'] = totalv
            vpart = self.get_vpart(line[2])
            stage['description'] = "\\\\".join(vpart.descriptors)
            purchaseorder.render_po(stage,
                                    self._name,
                                    os.path.join(path, self._name + '-PO-' + line[2] + '.pdf'))


class CSILPart(vendors.VendorPartBase):
    def __init__(self, vpartno, ident, vendor):
        if vendor is None:
            vendor = VendorCSIL('csil', 'transient', 'electronics_pcb')
            vendor.currency = currency.CurrencyDefinition('INR', 'INR')
        self._vendor = vendor
        if ident is None:
            ident = self._vendor.map.get_canonical(vpartno)
        super(CSILPart, self).__init__(ident, vendor)
        if vpartno is not None:
            self.vpno = vpartno
        else:
            logger.error("Not enough information to create a CSIL Part")
        self._pcbname = vpartno
        if self._pcbname not in projects.pcbs.keys():
            raise ValueError("Unrecognized PCB")
        self._projectfolder = projects.pcbs[self._pcbname]
        self._load_prices()
        self._descriptors = []
        self._load_descriptors()
        self._manufacturer = self._vendor.name
        self._vqtyavail = None

    def _load_descriptors(self):
        gpf = projfile.GedaProjectFile(self._projectfolder)
        pricingfp = os.path.join(gpf.configsfile.projectfolder, 'pcb', 'sourcing.yaml')
        if not os.path.exists(pricingfp):
            logger.debug("PCB does not have sourcing file. Not loading prices : " + self._pcbname)
            return None
        with open(pricingfp, 'r') as f:
            data = yaml.load(f)
        self._descriptors.append(str(data['params']['dX']) + 'mm x ' + str(data['params']['dY']) + 'mm')
        if data["params"]["layers"] == 2:
            self._descriptors.append("Double Layer")
        elif data["params"]["layers"] == 4:
            self._descriptors.append("ML4")
        # HAL, Sn, Au, PBFREE, H, NP, I, OC
        if data["params"]["finish"] == 'Au':
            self._descriptors.append("Immersion Gold/ENIG finish")
        elif data["params"]["finish"] == 'Sn':
            self._descriptors.append("Immersion Tin finish")
        elif data["params"]["finish"] == 'PBFREE':
            self._descriptors.append("Any Lead Free finish")
        elif data["params"]["finish"] == 'H':
            self._descriptors.append("Lead F ree HAL finish")
        elif data["params"]["finish"] == 'NP':
            self._descriptors.append("No Copper finish")
        elif data["params"]["finish"] == 'I':
            self._descriptors.append("OSP finish")
        elif data["params"]["finish"] == 'OC':
            self._descriptors.append("Only Copper finish")
        else:
            self._descriptors.append("UNKNOWN FINISH: " + data["params"]["finish"])
        self._descriptors.append("10 Working Days")

    def _load_prices(self):
        gpf = projfile.GedaProjectFile(self._projectfolder)
        pricingfp = os.path.join(gpf.configsfile.projectfolder, 'pcb', 'sourcing.yaml')
        if not os.path.exists(pricingfp):
            logger.debug("PCB does not have sourcing file. Not loading prices : " + self._pcbname)
            return None
        with open(pricingfp, 'r') as f:
            data = yaml.load(f)
        for qty, prices in data['pricing'].iteritems():
            if 10 not in prices.keys():
                logger.warning("Default Delivery Time not in prices. Quantity pricing not imported : " +
                               str([qty, self._pcbname]))
            else:
                price = vendors.VendorPrice(qty, prices[10], self._vendor.currency)
                self._prices.append(price)

    @property
    def descriptors(self):
        return self._descriptors

    def get_price(self, qty):
        possible_prices = []
        base_price, next_base_price = super(CSILPart, self).get_price(qty)
        for price in self._prices:
            if price.moq > qty and \
                    price.extended_price(price.moq).native_value < base_price.extended_price(qty).native_value:
                possible_prices.append(price)
        if len(possible_prices) == 0:
            return base_price, next_base_price, "GUIDELINE", None
        else:
            mintot = base_price.extended_price(qty).native_value
            selprice = base_price
            rationale = "GUIDELINE"
            for price in possible_prices:
                if price.extended_price(price.moq).native_value < mintot:
                    selprice = price
                    mintot = price.extended_price(price.moq).native_value
                    rationale = "TC Reduction"
            return selprice, super(CSILPart, self).get_price(selprice.moq + 1)[0], rationale, base_price


def flush_pcb_pricing(projfolder):
    gpf = projfile.GedaProjectFile(projfolder)
    pricingfp = os.path.join(gpf.configsfile.projectfolder, 'pcb', 'sourcing.yaml')
    if os.path.exists(pricingfp):
        os.remove(pricingfp)


def generate_pcb_pricing(projfolder, noregen=True, forceregen=False):
    gpf = projfile.GedaProjectFile(projfolder)

    try:
        pcbparams = gpf.configsfile.configdata['pcbdetails']['params']
    except KeyError:
        logger.warning('Geda project does not seem have pcb details. Not generating PCB pricing information : ' + projfolder)
        return None

    pricingfp = os.path.join(gpf.configsfile.projectfolder, 'pcb', 'sourcing.yaml')

    if noregen is True:
        if forceregen is False:
            pcb_mtime = fs.get_file_mtime(os.path.join(gpf.configsfile.projectfolder, 'pcb', gpf.pcbfile + '.pcb'))
            outf_mtime = fs.get_file_mtime(pricingfp)
            if outf_mtime is not None and outf_mtime > pcb_mtime:
                logger.info('Skipping up-to-date ' + pricingfp)
                return pricingfp
    logger.info('Generating PCB Pricing for ' + pricingfp)
    if pcbparams['layers'] == 4:
        pcbparams['qty'] = range(80)
    else:
        pcbparams['qty'] = range(260)
    sourcingdata = get_csil_prices(pcbparams)
    dumpdata = {'params': pcbparams,
                'pricing': sourcingdata}
    with open(pricingfp, 'w') as pricingf:
        pricingf.write(yaml.dump(dumpdata))

    return pricingfp
