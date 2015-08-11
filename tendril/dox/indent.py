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
Production Dox module documentation (:mod:`dox.production`)
============================================================
"""

import render
import os

import labelmaker


def gen_stock_idt_from_cobom(outfolder, sno, title, carddict, cobom):

    outpath = os.path.join(outfolder, str(sno) + '.pdf')
    cards = ""
    for card, qty in sorted(carddict.iteritems()):
        cards += card + ' x' + str(qty) + ', '

    indentsno = sno

    lines = []
    for idx, line in enumerate(cobom.lines):
        lines.append({'ident': line.ident, 'qty': line.quantity})
        labelmaker.manager.add_label('IDT', line.ident, indentsno + '.' + str(idx), qty=line.quantity)

    stage = {'title': title,
             'sno': indentsno,
             'lines': lines,
             'cards': cards}

    template = 'indent_stock_template.tex'
    render.render_pdf(stage, template, outpath)

    return outpath, indentsno
