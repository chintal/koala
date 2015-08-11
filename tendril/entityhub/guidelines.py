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
from decimal import Decimal

import tendril.conventions.electronics


class QtyGuidelineTableRow(object):
    def __init__(self, ide, (oqty_min, oqty_multiple, baseline_qty, excess_min_pc, excess_min_qty, excess_max_qty)):
        self._id = ide
        self._oqty_min = oqty_min
        self._oqty_multiple = oqty_multiple
        self._baseline_qty = baseline_qty
        self._excess_min_pc = excess_min_pc
        self._excess_min_qty = excess_min_qty
        self._excess_max_qty = excess_max_qty

    @property
    def id(self):
        return self._id

    @property
    def oqty_min(self):
        return str(self._oqty_min)

    @property
    def oqty_multiple(self):
        return str(self._oqty_multiple)

    @property
    def baseline_qty(self):
        return str(self._baseline_qty)

    @property
    def excess_min_pc(self):
        return str(self._excess_min_pc) + " %"

    @property
    def excess_min_qty(self):
        return str(self._excess_min_qty)

    @property
    def excess_max_qty(self):
        return str(self._excess_max_qty)


class QtyGuidelines(object):
    def __init__(self, guidelinefile):
        self._idents = None
        self._generators = None
        self._devices = None
        self._guidelinefile = guidelinefile
        self._load_guidelines()

    def _load_guidelines(self):
        with open(self._guidelinefile, 'r') as f:
            data = yaml.load(f)
            self._idents = data['idents']
            self._generators = data['generators']
            self._devices = data['devices']
            self._default = data['default']

    def get_guideline_table(self):
        return {'idents': [QtyGuidelineTableRow(x, self._get_full_guideline(self._idents[x]))
                           for x in self._idents.keys()],
                'devices': [QtyGuidelineTableRow(x, self._get_full_guideline(self._devices[x]))
                            for x in self._devices.keys()],
                'defaults': [QtyGuidelineTableRow('Default', self._get_full_guideline(self._default))]
                }

    @staticmethod
    def _get_full_guideline(gldict):
        if 'oqty_min' in gldict.keys():
            oqty_min = int(gldict['oqty_min'])
        else:
            oqty_min = 1
        if 'oqty_multiple' in gldict.keys():
            oqty_multiple = int(gldict['oqty_multiple'])
        else:
            oqty_multiple = 1
        if 'baseline_qty' in gldict.keys():
            baseline_qty = int(gldict['baseline_qty'])
        else:
            baseline_qty = 0
        if 'excess_min_pc' in gldict.keys():
            excess_min_pc = Decimal(gldict['excess_min_pc'])
        else:
            excess_min_pc = 0
        if 'excess_min_qty' in gldict.keys():
            excess_min_qty = Decimal(gldict['excess_min_qty'])
        else:
            excess_min_qty = 0
        if 'excess_max_qty' in gldict.keys():
            excess_max_qty = int(gldict['excess_max_qty'])
        else:
            excess_max_qty = -1
        return oqty_min, oqty_multiple, baseline_qty, excess_min_pc, excess_min_qty, excess_max_qty

    def get_compliant_qty(self, ident, qty,
                          handle_excess=True,
                          except_on_overrun=True,
                          handle_baseline=False,
                          ):
        oqty = qty
        device, value, footprint = tendril.conventions.electronics.parse_ident(ident)
        if ident in self._idents.keys():
            gldict = self._idents[ident]
        elif device in self._devices.keys():
            gldict = self._devices[device]
        else:
            gldict = self._default
        if gldict is not None:
            if 'filter_std_vals_only' in gldict.keys() and gldict['filter_std_vals_only'] is True:
                is_std_val = tendril.conventions.electronics.check_for_std_val(ident)
                if not is_std_val:
                    gldict = self._default

            (oqty_min, oqty_multiple, baseline_qty,
             excess_min_pc, excess_min_qty, excess_max_qty) = self._get_full_guideline(gldict)
            tqty = qty
            if handle_excess is True:
                tqty1 = tqty * (1 + Decimal(excess_min_pc) / 100)
                tqty2 = tqty + Decimal(excess_min_qty)
                tqty = max([tqty1, tqty2])

            if tqty <= oqty_min:
                oqty = oqty_min
            else:
                oqty = oqty_min
                while oqty <= tqty:
                    oqty += oqty_multiple
            if handle_excess is True:
                excess = oqty - qty
                if 0 < excess_max_qty < excess:
                    logger.warning('Maximum Excess Quantity exceeds predefined maximum : ' +
                                   ident + "::" + str((qty, oqty, excess_max_qty)))
                    if except_on_overrun is True:
                        raise ValueError
        return oqty
