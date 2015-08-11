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


def create_motif_object(motifst):
    modname = motifst.split('.')[0]
    modstr = 'tendril.conventions.motifs.' + modname
    clsname = 'Motif' + modname
    try:
        mod = __import__(modstr, fromlist=[clsname])
        cls = getattr(mod, clsname)
        instance = cls(motifst)
        return instance
    except ImportError:
        raise ValueError("Motif Unrecognized :" + motifst)
