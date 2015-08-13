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

logger = log.get_logger(__name__, log.INFO)

import yaml
import os

import tendril.boms.electronics
import tendril.boms.outputbase

import tendril.inventory.electronics
import tendril.dox.production
import tendril.dox.indent
import tendril.dox.docstore
import tendril.dox.labelmaker
import tendril.gedaif.conffile


from tendril.entityhub import projects
from tendril.entityhub import serialnos

from tendril.utils.pdf import merge_pdf
from tendril.utils.progressbar.progressbar import ProgressBar
from tendril.utils.config import INSTANCE_ROOT


if __name__ == "__main__":

    bomlist = []

    orderfolder = os.path.join(INSTANCE_ROOT, 'scratch', 'production')
    orderfile = os.path.join(orderfolder, 'order.yaml')

    with open(orderfile, 'r') as f:
        data = yaml.load(f)

    if os.path.exists(os.path.join(orderfolder, 'wsno')):
        with open(os.path.join(orderfolder, 'wsno'), 'r') as f:
            PROD_ORD_SNO = f.readline()
    else:
        PROD_ORD_SNO = None

    snomap = {}
    if os.path.exists(os.path.join(orderfolder, 'snomap.yaml')):
        with open(os.path.join(orderfolder, 'snomap.yaml'), 'r') as f:
            snomap = yaml.load(f)

    if data['register'] is True:
        REGISTER = True
    else:
        REGISTER = False

    if data['halt_on_shortage'] is True:
        HALT_ON_SHORTAGE = True
    else:
        HALT_ON_SHORTAGE = False

    if data['include_refbom_for_no_am'] is True:
        INCLUDE_REFBOM_FOR_NO_AM = True
    else:
        INCLUDE_REFBOM_FOR_NO_AM = False

    if data['force_labels'] is True:
        FORCE_LABELS = True
    else:
        FORCE_LABELS = False


    if 'sourcing_orders' in data.keys():
        SOURCING_ORDERS = data['sourcing_orders']
    else:
        SOURCING_ORDERS = None

    if 'root_orders' in data.keys():
        ROOT_ORDERS = data['root_orders']
        if len(ROOT_ORDERS) > 1:
            logger.warning("Having more than one Root Order is not fully defined. This may break other functionality")
    else:
        ROOT_ORDERS = None

    if PROD_ORD_SNO is None:
        PROD_ORD_SNO = serialnos.get_serialno('PROD', data['title'], register=False)

    # Generate Tendril Requisitions, confirm production viability.

    logger.info('Generating Card BOMs')
    for k, v in data['cards'].iteritems():
        bom = tendril.boms.electronics.import_pcb(projects.cards[k])
        obom = bom.create_output_bom(k)
        obom.multiply(v)
        logger.info('Inserting Card Bom : ' + obom.descriptor.configname +
                    ' x' + str(obom.descriptor.multiplier))
        bomlist.append(obom)

    cobom = tendril.boms.outputbase.CompositeOutputBom(bomlist)
    cobom.collapse_wires()

    with open(os.path.join(orderfolder, 'cobom.csv'), 'w') as f:
        logger.info('Exporting Composite Output BOM to File : ' + os.linesep + os.path.join(orderfolder, 'cobom.csv'))
        cobom.dump(f)


    unsourced = []
    pb = ProgressBar('red', block='#', empty='.')
    nlines = len(cobom.lines)

    for pbidx, line in enumerate(cobom.lines):
        percentage = (float(pbidx) / nlines) * 100.00
        pb.render(int(percentage),
                  "\n{0:>7.4f}% {1:<40} Qty:{2:<4}\nConstructing Reservations".format(
                      percentage, line.ident, line.quantity))
        shortage = 0

        for idx, descriptor in enumerate(cobom.descriptors):
            earmark = descriptor.configname + ' x' + str(descriptor.multiplier)
            avail = tendril.inventory.electronics.get_total_availability(line.ident)
            if line.columns[idx] == 0:
                continue
            if avail > line.columns[idx]:
                tendril.inventory.electronics.reserve_items(line.ident, line.columns[idx], earmark)
            elif avail > 0:
                tendril.inventory.electronics.reserve_items(line.ident, avail, earmark)
                pshort = line.columns[idx] - avail
                shortage += pshort
                logger.debug('Adding Partial Qty of ' + line.ident +
                             ' for ' + earmark + ' to shortage : ' + str(pshort))
            else:
                shortage += line.columns[idx]
                logger.debug('Adding Full Qty of ' + line.ident +
                             ' for ' + earmark + ' to shortage : ' + str(line.columns[idx]))

        if shortage > 0:
            unsourced.append((line.ident, shortage))


    if len(unsourced) > 0:
        logger.warning("Shortage of the following components: ")
        for elem in unsourced:
            logger.warning("{0:<40}{1:>5}".format(elem[0], elem[1]))
        if HALT_ON_SHORTAGE is True:
            logger.info("Halt on shortage is set. Reversing changes and exiting")
            exit()


    # TODO Transfer Reservations


    # Generate Indent
    logger.info("Generating Indent")

    indentfolder = orderfolder
    if 'indentsno' in snomap.keys():
        indentsno = snomap['indentsno']
    else:
        indentsno = serialnos.get_serialno('IDT', 'FOR ' + PROD_ORD_SNO, REGISTER)
        snomap['indentsno'] = indentsno
    title = data['title']
    indentpath, indentsno = tendril.dox.indent.gen_stock_idt_from_cobom(orderfolder,
                                                                      indentsno, title,
                                                                      data['cards'], cobom)
    if REGISTER is True:
        tendril.dox.docstore.register_document(indentsno, indentpath, 'INVENTORY INDENT', efield=title)
    else:
        logger.info("Not Registering Document : INVENTORY INDENT - " + indentsno)

    # Generate Production Order
    logger.info("Generating Production Order")
    if REGISTER is True:
        serialnos.register_serialno(PROD_ORD_SNO, efield=title)
        tendril.dox.docstore.register_document(indentsno, os.path.join(orderfolder, 'cobom.csv'),
                                             'PRODUCTION COBOM CSV', efield=title)
        serialnos.link_serialno(indentsno, PROD_ORD_SNO)
    else:
        logger.info("Not registering used serial number : " + PROD_ORD_SNO)
        logger.info("Not Registering Document : PRODUCTION COBOM CSV - " + indentsno)
        logger.info("Not Linking Serial Nos : " + indentsno + ' to parent ' + PROD_ORD_SNO)


    snos = []
    addldocs = []
    manifests = []
    manifestsfolder = os.path.join(orderfolder, 'manifests')
    if not os.path.exists(manifestsfolder):
        os.makedirs(manifestsfolder)
    manifestfiles = []

    for card, qty in sorted(data['cards'].iteritems()):
        try:
            cardfolder = projects.cards[card]
        except KeyError:
            logger.error("Could not find Card in entityhub.cards")
            raise KeyError
        cardconf = tendril.gedaif.conffile.ConfigsFile(cardfolder)
        snoseries = cardconf.configdata['snoseries']

        prodst = None
        lblst = None
        testst = None
        genmanifest = False

        if cardconf.configdata['documentation']['am'] is True:
            # Assembly manifest should be used
            prodst = "@AM"
            genmanifest = True
        elif cardconf.configdata['documentation']['am'] is False:
            # No Assembly manifest needed
            prodst = "@THIS"
            if INCLUDE_REFBOM_FOR_NO_AM is True:
                addldocs.append(os.path.join(cardconf.doc_folder, 'confdocs', card + '-bom.pdf'))
        if cardconf.configdata['productionstrategy']['testing'] == 'normal':
            # Normal test procedure, Test when made
            testst = "@NOW"
        if cardconf.configdata['productionstrategy']['testing'] == 'lazy':
            # Lazy test procedure, Test when used
            testst = "@USE"
        if cardconf.configdata['productionstrategy']['labelling'] == 'normal':
            # Normal test procedure, Label when made
            lblst = "@NOW"
        if cardconf.configdata['productionstrategy']['testing'] == 'lazy':
            # Lazy test procedure, Label when used
            lblst = "@USE"
        series = cardconf.configdata['snoseries']
        genlabel = False
        labels = []
        if isinstance(cardconf.configdata['documentation']['label'], dict):
            for k in sorted(cardconf.configdata['documentation']['label'].keys()):
                labels.append({'code': k, 'ident': card + '.' + cardconf.configdata['label'][k]})
            genlabel = True
        elif isinstance(cardconf.configdata['documentation']['label'], str):
            labels.append({'code': cardconf.configdata['documentation']['label'], 'ident': card})
            genlabel = True

        for idx in range(qty):
            if card in snomap.keys():
                if idx in snomap[card].keys():
                    sno = snomap[card][idx]
                else:
                    sno = serialnos.get_serialno(series, card, REGISTER)
                    snomap[card][idx] = sno
            else:
                snomap[card] = {}
                sno = serialnos.get_serialno(series, card, REGISTER)
                snomap[card][idx] = sno
            if REGISTER is True:
                serialnos.link_serialno(sno, PROD_ORD_SNO)
            c = {'sno': sno, 'ident': card, 'prodst': prodst, 'lblst': lblst, 'testst': testst}
            snos.append(c)
            if genlabel is True:
                for label in labels:
                    tendril.dox.labelmaker.manager.add_label(label['code'], label['ident'], sno)
            if genmanifest is True:
                ampath = tendril.dox.production.gen_pcb_am(cardfolder, card,
                                                         manifestsfolder, sno,
                                                         productionorderno=PROD_ORD_SNO,
                                                         indentsno=indentsno)
                manifestfiles.append(ampath)
                if REGISTER is True:
                    tendril.dox.docstore.register_document(sno, ampath, 'ASSEMBLY MANIFEST')

    production_order = tendril.dox.production.gen_production_order(orderfolder, PROD_ORD_SNO,
                                                                 data, snos,
                                                                 sourcing_orders=SOURCING_ORDERS,
                                                                 root_orders=ROOT_ORDERS)
    labelpaths = tendril.dox.labelmaker.manager.generate_pdfs(orderfolder, force=FORCE_LABELS)

    if len(labelpaths) > 0:
        merge_pdf(labelpaths, os.path.join(orderfolder, 'device-labels.pdf'))
    if len(addldocs) > 0:
        merge_pdf([production_order] + addldocs, production_order, remove_sources=False)
    if len(manifestfiles) > 0:
        merge_pdf(manifestfiles, os.path.join(orderfolder, 'manifests-printable.pdf'))

    if REGISTER is True:
        if os.path.exists(os.path.join(orderfolder, 'device-labels.pdf')):
            tendril.dox.docstore.register_document(PROD_ORD_SNO, os.path.join(orderfolder, 'device-labels.pdf'),
                                                 'DEVICE LABELS', data['title'])
        tendril.dox.docstore.register_document(PROD_ORD_SNO, production_order, 'PRODUCTION ORDER', data['title'])
        tendril.dox.docstore.register_document(PROD_ORD_SNO, orderfile, 'PRODUCTION ORDER YAML', data['title'])
    else:
        logger.info("Not registering document : DEVICE LABELS " + PROD_ORD_SNO)
        logger.info("Not registering document : PRODUCTION ORDER " + PROD_ORD_SNO)
        logger.info("Not registering document : PRODUCTION ORDER YAML " + PROD_ORD_SNO)

    with open(os.path.join(orderfolder, 'snomap.yaml'), 'w') as f:
        f.write(yaml.dump(snomap, default_flow_style=False))
    if REGISTER is True:
        tendril.dox.docstore.register_document(PROD_ORD_SNO, os.path.join(orderfolder, 'snomap.yaml'),
                                             'SNO MAP', data['title'])
