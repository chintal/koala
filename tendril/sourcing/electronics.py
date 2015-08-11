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
Electronics Sourcing module documentation (:mod:`sourcing.electronics`)
=======================================================================
"""

from tendril.utils import log
logger = log.get_logger(__name__, log.INFO)

import vendors
import orders

import digikey
import csil
import pricelist

from tendril.entityhub import projects
from tendril.gedaif import gsymlib
import tendril.gedaif.conffile

from tendril.utils.types import currency
from tendril.utils import fs
from tendril.utils import config
from tendril.utils.progressbar.progressbar import ProgressBar

import tendril.entityhub.maps

import os
import csv


def gen_vendor_mapfile(vendor_obj):
    """

    :type vendor_obj: sourcing.vendors.VendorBase
    """
    if isinstance(vendor_obj, int):
        vendor_obj = vendor_list[vendor_obj]
    if 'electronics' == vendor_obj.pclass:
        logger.info('Generating electronics mapfile for ' + vendor_obj.name)
        symlib = gsymlib.gen_symlib()
        symlib.sort(key=lambda x: x.ident)
        pb = ProgressBar('red', block='#', empty='.')

        outp = vendor_obj.mappath
        outf = fs.VersionedOutputFile(outp)
        outw = csv.writer(outf)
        outw.writerow(('Canonical', 'Strategy', 'Lparts'))

        nsymbols = len(symlib)
        counter = 0

        for status in ['Active', 'Experimental', 'Deprecated', 'Virtual', 'Generator']:
            for symbol in symlib:
                if symbol.status == status and symbol.ident.strip() != "":
                    vpnos, strategy = vendor_obj.search_vpnos(symbol.ident)
                    if vpnos is not None:
                        vpnos = [('@AG@' + vpno) for vpno in vpnos]
                    else:
                        # TODO Fix this error (hack around progressbar issue)
                        if strategy not in ['NODEVICE', 'NOVALUE']:
                            logger.warning("Could not find matches for : " + symbol.ident +
                                           '::' + str(strategy) + '\n\n\n')
                        vpnos = []
                    try:
                        outw.writerow([symbol.ident.strip(), strategy.strip()] + vpnos)
                    except AttributeError:
                        print symbol.ident, strategy
                        raise AttributeError
                    counter += 1
                    percentage = counter * 100.00 / nsymbols
                    pb.render(int(percentage), "\n%f%% %s\nGenerating Map File" % (percentage, symbol.ident))
        outf.close()
        logger.info("Written Electronics Vendor Map to File : " + vendor_obj.name)
    elif 'electronics_pcb' == vendor_obj.pclass:
        logger.info('Generating PCB mapfile for ' + vendor_obj.name)

        pcblib = projects.pcbs
        pb = ProgressBar('red', block='#', empty='.')

        outp = vendor_obj.mappath
        outf = fs.VersionedOutputFile(outp)
        outw = csv.writer(outf)
        outw.writerow(('Canonical', 'Strategy', 'Lparts'))

        nsymbols = len(pcblib)
        counter = 0

        for pcb, folder in pcblib.iteritems():
            # conf = gedaif.conffile.ConfigsFile(folder)
            # dstatus = None
            # try:
            #     dstatus = conf.configdata['pcbdetails']['status']
            # except KeyError:
            #     logger.warning('PCB missing pcbdetails : ' + pcb)

            vpnos, strategy = [[pcb], 'CUSTOM']
            outw.writerow(['PCB ' + pcb.strip(), strategy.strip()] + vpnos)
            counter += 1
            percentage = counter * 100.00 / nsymbols
            pb.render(int(percentage), "\n%f%% %s\nGenerating Map File" % (percentage, pcb))
        outf.close()
        logger.info("Written PCB Vendor Map to File : " + vendor_obj.name)
    else:
        logger.warning('Vendor pclass is not recognized. Not generating map.')
        return
    vendor_obj.map = vendor_obj.mappath

vendor_list = []


def init_vendors():
    global vendor_list
    for vendor in config.VENDORS_DATA:
        logger.debug("Adding Vendor : " + vendor['name'])
        if 'electronics' in vendor['pclass']:
            vendor_obj = None
            mappath = vendor['mapfile-base'] + '-electronics.csv'
            # TODO Fix This.
            if vendor['name'] == 'digikey':
                vendor_obj = digikey.VendorDigiKey(vendor['name'],
                                                   vendor['dname'],
                                                   'electronics',
                                                   mappath,
                                                   'USD',
                                                   'US$'
                                                   )
                logger.info("Created DK Vendor Object : " + vendor['dname'])
            if vendor['type'] == 'pricelist':
                vendor_obj = pricelist.VendorPricelist(vendor['name'],
                                                       vendor['dname'],
                                                       'electronics',
                                                       mappath)
                logger.info("Created Pricelist Vendor Object : " + vendor['dname'])
            if vendor_obj:
                vendor_list.append(vendor_obj)
            else:
                logger.error('Vendor Handlers not found for vendor : ' + vendor['name'])
        if 'electronics_pcb' in vendor['pclass']:
            vendor_obj = None
            mappath = vendor['mapfile-base'] + '-electronics-pcb.csv'
            if vendor['name'] == 'csil':
                vendor_obj = csil.VendorCSIL(vendor['name'],
                                             vendor['dname'],
                                             'electronics_pcb',
                                             mappath,
                                             'INR',
                                             username=vendor['user'],
                                             password=vendor['pw']
                                             )
                logger.info("Created CSIL Vendor Object : " + vendor['dname'])
            if vendor_obj:
                vendor_list.append(vendor_obj)
            else:
                logger.error('Vendor Handlers not found for vendor : ' + vendor['name'])


def export_vendor_map_audit(vendor_obj):
    """

    :type vendor_obj: sourcing.vendors.VendorBase
    """
    if isinstance(vendor_obj, int):
        vendor_obj = vendor_list[vendor_obj]
    mapobj = vendor_obj.map
    assert isinstance(mapobj, tendril.entityhub.maps.MapFile)

    outp = os.path.join(config.vendor_map_audit_folder, vendor_obj.name + '-electronics-audit.csv')
    outf = fs.VersionedOutputFile(outp)
    outw = csv.writer(outf)
    pb = ProgressBar('red', block='#', empty='.')
    idents = mapobj.get_idents()
    nidents = len(idents)
    idents.sort()
    for iidx, ident in enumerate(idents):
        nvpnos = len(idents)

        for pidx, vpno in enumerate(mapobj.get_all_partnos(ident)):
            vp = vendor_obj.get_vpart(vpno, ident)
            try:
                assert isinstance(vp, vendors.VendorElnPartBase)
                outw.writerow([vp.ident, vp.vpno, vp.mpartno, vp.package, vp.vpartdesc,
                               vp.manufacturer, vp.vqtyavail, vp.abs_moq])
            except AssertionError:
                outw.writerow([vp.ident, vp.vpno, vp.mpartno, None, vp.vpartdesc,
                               vp.manufacturer, vp.vqtyavail, vp.abs_moq])

            percentage = (iidx + (1.00 * pidx / nvpnos)) * 100.00 / nidents
            pb.render(int(percentage), "\n%f%% %s;%s\nGenerating Vendor Map Audit" % (percentage, ident, vpno))

    outf.close()
    logger.info("Written Vendor Map Audit to File : " + vendor_obj.name)

init_vendors()


class SourcingException(Exception):
    pass


def get_eff_acq_price(vsinfo):
    return vsinfo[2] * vsinfo[5].unit_price.native_value


def get_sourcing_information(ident, qty, avendors=vendor_list, allvendors=False):
    # vobj, vpno, oqty, nbprice, ubprice, effprice
    sources = []
    ident = ident.strip()
    for vendor in avendors:
        vsinfo = vendor.get_optimal_pricing(ident, qty)
        if vsinfo[1] is not None:
            sources.append(vsinfo)

    if len(sources) == 0:
        raise SourcingException

    if allvendors is False:
        selsource = sources[0]
        for vsinfo in sources:
            if get_eff_acq_price(vsinfo) < get_eff_acq_price(selsource):
                selsource = vsinfo
        return selsource
    else:
        return sources

order = orders.CompositeOrder(vendor_list)


def get_vendor_by_name(name):
    for vendor in vendor_list:
        if vendor.vendor_name == name:
            return vendor
    return None
