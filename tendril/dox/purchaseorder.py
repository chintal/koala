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

import datetime

import render
from tendril.entityhub import serialnos

from tendril.utils.config import COMPANY_PO_LCO_PATH
from tendril.utils.config import COMPANY_PO_POINT


def render_po(stage, templateid, outpath):
    template = 'po_' + templateid + '_template.tex'
    stage['lcofile'] = COMPANY_PO_LCO_PATH
    if 'point' not in stage.keys():
        stage['point'] = COMPANY_PO_POINT
    if 'no' not in stage.keys():
        stage['no'] = serialnos.get_serialno(series='PO', efield=templateid)
    if 'date' not in stage.keys():
        stage['date'] = str(datetime.date.today())
    return render.render_pdf(stage, template, outpath)
