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
logger = log.get_logger(__name__, None)

import iec60063

from tendril.conventions.motifs.motifbase import MotifBase
from tendril.conventions import electronics
from tendril.gedaif import gsymlib


class MotifInampGainBase(MotifBase):
    def __init__(self, identifier):
        super(MotifInampGainBase, self).__init__(identifier)
        self._configdict = None

    def validate(self):
        logger.debug("Validating Motif : " + self.refdes)
        logger.debug("RES : " + str(self.R1) + " GAIN : " + str(self.gain))

    def get_configdict_stub(self):
        stub = {'desc': 'Instrumentation Amplifier Gain',
                'gain': '1',
                'Rseries': 'E12',
                'Rmin': '10E',
                'Rmax': '10M'}
        return stub

    def configure(self, configdict):
        self._configdict = configdict
        self.gain = configdict['gain']
        self.validate()

    def res_to_gain(self, res):
        raise NotImplementedError

    def gain_to_res(self, gain):
        raise NotImplementedError

    @property
    def R1(self):
        elem = self.get_elem_by_idx('R1')
        assert elem.data['device'] in ['RES SMD', 'RES THRU']
        if elem.data['fillstatus'] == 'DNP':
            return None
        return electronics.parse_resistance(electronics.parse_resistor(elem.data['value'])[0])

    @property
    def gain(self):
        return self.res_to_gain(self.R1)

    @gain.setter
    def gain(self, value):
        r1_dev = self.get_elem_by_idx('R1').data['device']
        r1_fp = self.get_elem_by_idx('R1').data['footprint']
        if r1_fp[0:3] == "MY-":
            r1_fp = r1_fp[3:]

        allowed_res_vals = iec60063.gen_vals(self._configdict['Rseries'],
                                             iec60063.res_ostrs,
                                             self._configdict['Rmin'],
                                             self._configdict['Rmax'])

        required_res_val = self.gain_to_res(value)
        if required_res_val is None:
            self.get_elem_by_idx('R1').data['fillstatus'] = 'DNP'
            return
        rval = None
        lastval = None
        for val in allowed_res_vals:
            lastval = rval
            rval = electronics.parse_resistance(val)
            if rval > required_res_val:
                self.get_elem_by_idx('R1').data['value'] = gsymlib.find_resistor(lastval, r1_fp, r1_dev)
                break
