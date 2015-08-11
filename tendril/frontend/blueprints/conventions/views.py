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


from flask import render_template, request
from flask_user import login_required

import iec60063

from . import conventions as blueprint

from tendril.conventions import electronics
from tendril.inventory import guidelines


def get_iec60063_params():
    stype = request.args.get('type')
    if stype and not stype.strip():
        stype = None

    series = request.args.get('series')
    if series and not series.strip():
        series = None

    start = request.args.get('start')
    try:
        if not start.strip():
            start = None
    except AttributeError:
        start = None

    end = request.args.get('end')
    try:
        if not end.strip():
            end = None
    except AttributeError:
        end = None

    if series is None:
        series = 'E24'
    if stype is None:
        stype = ''

    return get_iec60063_contextpart(stype, series, start, end)


def get_iec60063_contextpart(stype, series, start=None, end=None):
    return {"iec60063vals": [i for i in iec60063.gen_vals(iec60063.get_series(series),
                                                          iec60063.get_ostr(stype),
                                                          start, end)],
            "iec60063stype": stype,
            "iec60063series": series,
            "iec60063start": start,
            "iec60063end": end,
            }


@blueprint.route('/', methods=['GET'])
@login_required
def main():
    stage = {'devices': electronics.DEVICE_CLASSES,
             'guidelines': guidelines.electronics_qty.get_guideline_table()}
    if request.method == 'GET':
        stage.update(get_iec60063_params())
    return render_template('conventions_main.html', stage=stage,
                           pagetitle='Conventions')
