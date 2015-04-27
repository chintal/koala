"""
This file is part of koala
See the COPYING, README, and INSTALL files for more information
"""

from utils import log
logger = log.get_logger(__name__, log.INFO)

import yaml
import csv
import os

import boms.electronics
import boms.outputbase

import inventory.electronics
import conventions.electronics
import sourcing.electronics


from entityhub import projects
from gedaif import gsymlib
import inventory.guidelines

from utils.config import KOALA_ROOT


bomlist = []

orderfolder = os.path.join(KOALA_ROOT, 'scratch')
orderfile = os.path.join(orderfolder, 'order.yaml')

with open(orderfile, 'r') as f:
    data = yaml.load(f)

LOAD_PRESHORT = False
LOAD_EXTERNAL_REQ = False
external_req_file = None
USE_STOCK = True

if 'preshort' in data.keys():
    LOAD_PRESHORT = data['preshort']
if 'external' in data.keys():
    external_req_file = os.path.join(orderfolder, data['external'])
    LOAD_EXTERNAL_REQ = True
if 'use_stock' in data.keys():
    USE_STOCK = data['use_stock']


# Define base transforms for external data
base_tf = inventory.electronics.inventory_locations[0]._reader.tf


if LOAD_PRESHORT is True:
    # Load Preshort File
    if os.path.exists(os.path.join(orderfolder, 'preshort.csv')):
        with open(os.path.join(orderfolder, 'preshort.csv'), 'r') as f:
            logger.debug('Creating PRESHORT Bom')
            obom_descriptor = boms.outputbase.OutputElnBomDescriptor('PRESHORT', os.path.join(KOALA_ROOT, 'scratch'),
                                                                     'PRESHORT', None)
            obom = boms.outputbase.OutputBom(obom_descriptor)

            reader = csv.reader(f)
            for line in reader:
                line = [elem.strip() for elem in line]
                if line[0] == 'S.No.':
                    continue
                if line[1] == line[2] == line[3]:
                    continue
                if line[1] == 'Electricals':
                    break
                if base_tf.has_contextual_repr(line[1]):
                    device, value, footprint = conventions.electronics.parse_ident(base_tf.get_canonical_repr(line[1]))
                    item = boms.electronics.EntityElnComp()
                    item.define('Undef', device, value, footprint)
                    for i in range(int(line[2]) + 1):
                        obom.insert_component(item)
                else:
                    print line[1], 'No'
            logger.info('Inserting PRESHORT Bom')
            bomlist.append(obom)

# Load External Requisitions
if LOAD_EXTERNAL_REQ is True:
    if os.path.exists(external_req_file):
        with open(external_req_file, 'r') as f:
            header = []
            reader = csv.reader(f)
            for line in reader:
                line = [elem.strip() for elem in line]
                if line[0] == 'Device':
                    header = line
                    break

            logger.info('Inserting External Boms')
            oboms = []
            for head in header[1:]:
                logger.debug('Creating Bom : ' + head)
                obom_descriptor = boms.outputbase.OutputElnBomDescriptor(head, os.path.join(KOALA_ROOT, 'scratch'),
                                                                         head, None)
                obom = boms.outputbase.OutputBom(obom_descriptor)
                oboms.append(obom)

            for line in reader:
                line = [elem.strip() for elem in line]
                if line[0] == '':
                    continue
                if line[0] == 'END':
                    break
                if not base_tf.has_contextual_repr(line[0]):
                    print line[0] + ' Possibly not recognized'
                device, value, footprint = conventions.electronics.parse_ident(base_tf.get_canonical_repr(line[0]))
                # print base_tf.get_canonical_repr(line[0])
                item = boms.electronics.EntityElnComp()
                item.define('Undef', device, value, footprint)
                for idx, col in enumerate(line[1:]):
                    num = int(col)
                    if num > 0:
                        for i in range(num):
                            oboms[idx].insert_component(item)

            for obom in oboms:
                logger.info('Inserting External Bom : ' + obom.descriptor.configname)
                bomlist.append(obom)


# Generate Koala Requisitions
logger.info('Generating Card BOMs')
for k, v in data['cards'].iteritems():
    bom = boms.electronics.import_pcb(projects.cards[k])
    obom = bom.create_output_bom(k)
    obom.multiply(v)
    logger.info('Inserting Card Bom : ' + obom.descriptor.configname +
                ' x' + str(obom.descriptor.multiplier))
    bomlist.append(obom)

cobom = boms.outputbase.CompositeOutputBom(bomlist)

with open(os.path.join(orderfolder, 'cobom.csv'), 'w') as f:
    logger.info('Exporting Composite Output BOM to File : ' + os.path.join(orderfolder, 'cobom.csv'))
    cobom.dump(f)


dkv = sourcing.electronics.vendor_list[0]
dkvmap = dkv.map

with open(os.path.join(orderfolder, 'shortage.csv'), 'w') as f:
    logger.info('Constructing Shortage File')
    w = csv.writer(f)
    logger.info('Opening Digikey Order File')
    dkof = open(os.path.join(orderfolder, 'digikey-importable.csv'), 'w')
    wdk = csv.writer(dkof)
    w.writerow(["Component Details", '', '', '',
                "Requirement", '', '',
                "Guideline Compliant", '',
                "Order Details", '', '', '', '', '', '',
                "Vendor Pricing", '', '', '', '', '', '',
                "Order Pricing", '', '', '', ''
                ]
               )
    w.writerow(["Ident", "In gsymlib", "From DK", "Strategy",
                "Required", "Reserved", "Shortage",
                "Buy Qty", "Excess Qty",
                "Vendor", "Vendor Part No", "Manufacturer", "Manufacturer Part No", "Description", "Order Qty", "Excess Qty",
                "Vendor Currency", "Next Break Qty", "NB Unit Price", "NB Extended Price",
                "Used Break Qty", "Unit Price", "Extended Price",
                "Lower Break Unit Price", "Unit Price", "Effective Unit Price", "Order Qty", "Effective Extended Price",
                "Effective Excess Price", "Excess Rationale"
                ]
               )
    w.writerow(['', '', '', '',
                "Qty", "Qty", "Qty",
                "Qty", "Qty",
                "", "", "", "", "", "Qty", "Qty",
                "", "Qty", "(VC)", "(VC)",
                "Qty", "(VC)", "(VC)",
                "INR", "INR", "INR", "Qty", "INR", "INR"
                ]
               )
    for line in cobom.lines:
        shortage = 0
        if USE_STOCK is True:
            for idx, descriptor in enumerate(cobom.descriptors):
                earmark = descriptor.configname + ' x' + str(descriptor.multiplier)
                avail = inventory.electronics.get_total_availability(line.ident)
                if line.columns[idx] == 0:
                    continue
                if avail > line.columns[idx]:
                    inventory.electronics.reserve_items(line.ident, line.columns[idx], earmark)
                elif avail > 0:
                    inventory.electronics.reserve_items(line.ident, avail, earmark)
                    pshort = line.columns[idx] - avail
                    shortage += pshort
                    logger.debug('Adding Partial Qty of ' + line.ident +
                                 ' for ' + earmark + ' to shortage : ' + str(pshort))
                else:
                    shortage += line.columns[idx]
                    logger.debug('Adding Full Qty of ' + line.ident +
                                 ' for ' + earmark + ' to shortage : ' + str(line.columns[idx]))
        else:
            shortage = line.quantity
        if shortage > 0:
            if gsymlib.is_recognized(line.ident):
                in_gsymlib = "YES"
            else:
                in_gsymlib = ""
            dk_vpnos = dkvmap.get_partnos(line.ident)
            strategy = dkvmap.get_strategy(line.ident)
            buy_qty = inventory.guidelines.electronics_qty.get_compliant_qty(line.ident, shortage)
            if len(dk_vpnos) > 0:
                avail_from_dk = 'YES'
            else:
                avail_from_dk = ''

            row = [line.ident, in_gsymlib, avail_from_dk, strategy,
                   line.quantity, line.quantity-shortage, shortage,
                   buy_qty, (buy_qty-shortage)]
            logger.info("Attempting to source " + line.ident)
            try:
                vobj, vpno, oqty, nbprice, ubprice, effprice, urationale, olduprice = sourcing.electronics.get_sourcing_information(line.ident,
                                                                                                                         buy_qty)

                vcurr = vobj.currency.symbol
                if nbprice is not None:
                    nbqty = nbprice.moq
                    nbunitp_vst = nbprice.unit_price.source_value
                    nbextp_vst = nbprice.extended_price(nbqty).source_value
                else:
                    nbqty = None
                    nbunitp_vst = None
                    nbextp_vst = None

                if olduprice is not None:
                    unitp_lb_nst = olduprice.unit_price.native_value
                else:
                    unitp_lb_nst = None

                ubqty = ubprice.moq
                ubunitp_vst = ubprice.unit_price.source_value
                ubextp_vst = ubprice.extended_price(oqty).source_value

                unitp_nst = ubprice.unit_price.native_value

                eff_unitp_nst = effprice.unit_price.native_value
                eff_extp_nst = effprice.extended_price(oqty).native_value
                eff_excess_price = (oqty-shortage) * effprice.unit_price.native_value

                logger.info("Sourced " + line.ident + ":" + str((vpno, oqty)))

                try:
                    vpobj = vobj.get_vpart(vpno, line.ident)
                    manufacturer = vpobj.manufacturer
                    mpartno = vpobj.mpartno
                    description = vpobj.vpartdesc
                except:
                    vpobj = None
                    manufacturer = None
                    description = None
                    mpartno = None

                row += [vobj.name, vpno, manufacturer, mpartno, description,
                        oqty, (oqty-shortage),             # Order Details
                        vcurr, nbqty, nbunitp_vst, nbextp_vst,              # Final Pricing (Vendor Currency)
                        ubqty, ubunitp_vst, ubextp_vst,
                        unitp_lb_nst, unitp_nst, eff_unitp_nst, oqty, eff_extp_nst,       # Final Pricing (Native Currency)
                        eff_excess_price, urationale
                        ]

                if vobj.name == 'Digi-Key Corporation':
                    logger.info("Adding to DK Order : " + line.ident + " : " + str(oqty))
                    wdk.writerow([oqty, vpno, line.ident])

            except sourcing.electronics.SourcingException:
                logger.warning("Could Not Source Component : " + line.ident + " : " + str(line.quantity))
            w.writerow(row)
    logger.info('Exported Digikey Order to File : ' + os.path.join(orderfolder, 'digikey-importable.csv'))
    dkof.close()
logger.info('Exported Shortage and Sourcing List to File : ' + os.path.join(orderfolder, 'shortage.csv'))
inventory.electronics.export_reservations(orderfolder)
