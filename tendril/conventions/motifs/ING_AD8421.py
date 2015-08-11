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

from ingbase import MotifInampGainBase


class MotifING_AD8421(MotifInampGainBase):
    def res_to_gain(self, res):
        if res is None:
            return 1
        return 1 + (9900 / res)

    def gain_to_res(self, gain):
        if gain is 1:
            return None
        if gain < 1:
            raise ValueError
        return 9900.0 / (gain - 1)
