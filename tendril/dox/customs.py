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

import os
import datetime
import copy

import render
import wallet
import docstore

from tendril.utils import pdf
from tendril.entityhub import serialnos

from tendril.utils.config import COMPANY_GOVT_POINT


def gen_declaration(invoice, target_folder, copyt, serialno):
    outpath = os.path.join(target_folder, "customs-declaration-" + copyt + '-' + str(invoice.inv_no) + ".pdf")

    given_data = copy.deepcopy(invoice.given_data)

    for k, v in given_data['costs_not_included'].iteritems():
        given_data['costs_not_included'][k] = render.escape_latex(v)

    stage = {'date': datetime.date.today().isoformat(),
             'signatory': COMPANY_GOVT_POINT,
             'inv_no': invoice.inv_no,
             'inv_date': invoice.inv_date,
             'given_data': given_data,
             'currency': render.escape_latex(invoice.currency.symbol),
             'inv_total': render.escape_latex(invoice.extendedtotal.source_string),
             'exchrate': invoice.given_data['exchrate'],
             'exchnotif': invoice.given_data['exchnotif'],
             'exchnotifdt': invoice.given_data['exchnotif_date'],
             'extended_total_sc': render.escape_latex(invoice.extendedtotal.source_string),
             'assessable_total_sc': render.escape_latex(invoice.assessabletotal.source_string),
             'assessable_total_nc': render.escape_latex(invoice.assessabletotal.native_string),
             'copyt': copyt,
             'sno': serialno + '.5'
             }

    return render.render_pdf(stage, 'customs/decl.tex', outpath)


def gen_valuation(invoice, target_folder, serialno):
    outpath = os.path.join(target_folder, "customs-valuation-" + str(invoice.inv_no) + ".pdf")

    note1 = ''
    if invoice.includes_freight is True:
        note1 += "As listed in the invoice, {0} towards freight is also added. ".format(invoice.freight.source_string)
    note1 = render.escape_latex(note1)

    note2 = []

    if invoice.added_insurance is True:
        note2.append("An additional {0}% of FOB is added to the assessable value as per Rule 10(2)(c)(iii) of Customs Valuation (Determination of Value of Imported Goods) Rules, 2007. No specific insurance charges were paid as part of the transaction.".format(invoice.insurance_pc))
    if invoice.added_handling is True:
        note2.append("An additional {0}% of CIF is added to the assessable value as per Rule 10(2)(b)(ii) of Customs Valuation (Determination of Value of Imported Goods) Rules, 2007. No specific handling charges were paid as part of the transaction.".format(invoice.handling_pc))

    include_note2 = False
    if len(note2) > 0:
        include_note2 = True
    if invoice.given_data['bank_ref'] is None:
        is_wire = False
    else:
        is_wire = True

    stage = {'date': datetime.date.today().isoformat(),
             'signatory': COMPANY_GOVT_POINT,
             'inv_no': invoice.inv_no,
             'inv_date': invoice.inv_date,
             'given_data': invoice.given_data,
             'currency': render.escape_latex(invoice.currency.symbol),
             'inv_total': render.escape_latex(invoice.extendedtotal.source_string),
             'exchrate': invoice.given_data['exchrate'],
             'exchnotif': invoice.given_data['exchnotif'],
             'exchnotifdt': invoice.given_data['exchnotif_date'],
             'note1': note1,
             'note2': note2,
             'include_note2': include_note2,
             'extended_total_sc': render.escape_latex(invoice.extendedtotal.source_string),
             'assessable_total_sc': render.escape_latex(invoice.assessabletotal.source_string),
             'assessable_total_nc': render.escape_latex(invoice.assessabletotal.native_string),
             'sno': serialno + '.3',
             'is_wire': is_wire
             }

    return render.render_pdf(stage, 'customs/valuation.tex', outpath)


def gen_rsp_declaration(invoice, target_folder, serialno):
    outpath = os.path.join(target_folder, "customs-rsp-declaration-" + str(invoice.inv_no) + ".pdf")
    stage = {'date': datetime.date.today().isoformat(),
             'signatory': COMPANY_GOVT_POINT,
             'inv_no': invoice.inv_no,
             'inv_date': invoice.inv_date,
             'given_data': invoice.given_data,
             'sno': serialno + '.2'
             }

    return render.render_pdf(stage, 'customs/rsp-declaration.tex', outpath)


def gen_authorization(invoice, target_folder, serialno):
    outpath = os.path.join(target_folder, "customs-authorization-" + str(invoice.inv_no) + ".pdf")
    stage = {'date': datetime.date.today().isoformat(),
             'signatory': COMPANY_GOVT_POINT,
             'inv_no': invoice.inv_no,
             'inv_date': invoice.inv_date,
             'given_data': invoice.given_data,
             'sno': serialno + '.1'
             }

    if invoice.given_data['cha'] == 'DHL':
        template = 'customs/authorization.dhl.tex'
    elif invoice.given_data['cha'] == 'FedEx':
        template = 'customs/authorization.fedex.tex'
    else:
        raise ValueError('CHA unsupported')
    return render.render_pdf(stage, template, outpath)


def gen_tech_writeup(invoice, target_folder, serialno):
    outpath = os.path.join(target_folder, "customs-tech-writeup-" + str(invoice.inv_no) + ".pdf")
    sectable = []
    tqty = 0
    tvalue = 0
    for section in invoice.hssections:
        secline = {'code': section.code,
                   'name': section.name,
                   'idxs': invoice.getsection_idxs(section),
                   'qty': invoice.getsection_qty(section),
                   'value': render.escape_latex(invoice.getsection_assessabletotal(section).source_string)
                   }
        sectable.append(secline)
        tqty += invoice.getsection_qty(section)
        tvalue += invoice.getsection_assessabletotal(section)

    unclassified = {'idxs': [x.idx for x in invoice.unclassified],
                    'qty': sum([x.qty for x in invoice.unclassified]),
                    }
    if unclassified['qty'] > 0:
        unclassified['value'] = render.escape_latex(sum([x.assessableprice for x in invoice.unclassified]).source_string)
        tvalue += sum([x.assessableprice for x in invoice.unclassified])
        tqty += unclassified['qty']
    else:
        unclassified['value'] = None

    stage = {'date': datetime.date.today().isoformat(),
             'signatory': COMPANY_GOVT_POINT,
             'inv_no': invoice.inv_no,
             'inv_date': invoice.inv_date,
             'given_data': invoice.given_data,
             'linecount': invoice.linecount,
             'sectable': sectable,
             'tqty': tqty,
             'tvalue': render.escape_latex(tvalue.source_string),
             'unclassified': unclassified,
             'sno': serialno + '.4'
             }
    return render.render_pdf(stage, 'customs/technical-writeup.tex', outpath)


def gen_submitdocs(invoice, target_folder, serialno):
    lh_files = [gen_authorization(invoice, target_folder, serialno),
                gen_rsp_declaration(invoice, target_folder, serialno),
                gen_valuation(invoice, target_folder, serialno),
                gen_tech_writeup(invoice, target_folder, serialno)
                ]
    lh_fpath = os.path.join(target_folder, "customs-printable-lh-" + str(invoice.inv_no) + ".pdf")
    lh_fpath = pdf.merge_pdf(lh_files, lh_fpath, remove_sources=True)

    pp_files = [gen_declaration(invoice, target_folder, 'ORIGINAL', serialno),
                gen_declaration(invoice, target_folder, 'DUPLICATE', serialno),
                wallet.get_document_path('CUSTOMS-DECL'),
                wallet.get_document_path('CUSTOMS-DECL'),
                wallet.get_document_path('IEC'),
                ]
    pp_fpath = os.path.join(target_folder, "customs-printable-pp-" + str(invoice.inv_no) + ".pdf")
    pp_fpath = pdf.merge_pdf(pp_files, pp_fpath, remove_sources=True)

    files = [(lh_fpath, 'CUST-PRINTABLE-LH'), (pp_fpath, 'CUST-PRINTABLE-PP')]
    return files


def gen_verification_sections(invoice, target_folder, serialno):
    outpath = os.path.join(target_folder, "customs-verification-sections-" + str(invoice.inv_no) + ".pdf")
    stage = {'date': datetime.date.today().isoformat(),
             'signatory': COMPANY_GOVT_POINT,
             'inv_no': invoice.inv_no,
             'inv_date': invoice.inv_date,
             'given_data': invoice.given_data,
             'lines': invoice.lines,
             'sno': serialno + '.6',
             }

    outpath = render.render_pdf(stage, 'customs/verification-sections.tex', outpath)
    return outpath, 'CUST-VERIF-SEC'


def gen_verification_checklist(invoice, target_folder, serialno):
    outpath = os.path.join(target_folder, "customs-verification-duties-" + str(invoice.inv_no) + ".pdf")
    summary = []
    for section in invoice.hssections:
        secsum = {'section': section, 'code': section.code, 'name': section.name,
                  'idxs': invoice.getsection_idxs(hssection=section),
                  'assessablevalue': invoice.getsection_assessabletotal(hssection=section),
                  'qty': invoice.getsection_qty(hssection=section),
                  'bcd': sum([x.bcd.value for x in invoice.getsection_lines(hssection=section)]),
                  'cvd': sum([x.cvd.value for x in invoice.getsection_lines(hssection=section)]),
                  'acvd': sum([x.acvd.value for x in invoice.getsection_lines(hssection=section)]),
                  'cec': sum([x.cec.value for x in invoice.getsection_lines(hssection=section)]),
                  'cshec': sum([x.cshec.value for x in invoice.getsection_lines(hssection=section)]),
                  'cvdec': sum([x.cvdec.value for x in invoice.getsection_lines(hssection=section)]),
                  'cvdshec': sum([x.cvdshec.value for x in invoice.getsection_lines(hssection=section)]),
                  }
        summary.append(secsum)
    stage = {'date': datetime.date.today().isoformat(),
             'signatory': COMPANY_GOVT_POINT,
             'inv_no': invoice.inv_no,
             'inv_date': invoice.inv_date,
             'given_data': invoice.given_data,
             'lines': invoice.lines,
             'summary': summary,
             'invoice': invoice,
             'sno': serialno + '.7'}
    outpath = render.render_pdf(stage, 'customs/verification-duties.tex', outpath)
    return outpath, 'CUST-VERIF-BOE'


def gen_verificationdocs(invoice, target_folder, serialno):
    files = [gen_verification_sections(invoice, target_folder, serialno),
             gen_verification_checklist(invoice, target_folder, serialno)
             ]
    return files


def generate_docs(invoice, target_folder=None, serialno=None, register=False, efield=None):
    if efield is None:
        efield = ' '.join([invoice.vendor_name, str(invoice.inv_no)])
    if serialno is None:
        if os.path.exists(os.path.join(invoice.source_folder, 'wsno')):
            with open(os.path.join(invoice.source_folder, 'wsno'), 'r') as f:
                serialno = f.readline()
        else:
            serialno = serialnos.get_serialno('PINV', efield,
                                              register=register)
    if target_folder is None:
        target_folder = invoice.source_folder
    files = gen_submitdocs(invoice, target_folder, serialno=serialno)
    files.extend(gen_verificationdocs(invoice, target_folder, serialno=serialno))
    files.extend(invoice.source_files)
    if register is True:
        for document in files:
            docstore.register_document(serialno, docpath=document[0], doctype=document[1],
                                       efield=efield, series='PINV')
    return serialno
