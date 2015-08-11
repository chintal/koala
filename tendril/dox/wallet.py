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

from tendril.utils.config import DOCUMENT_WALLET
from tendril.utils.config import DOCUMENT_WALLET_ROOT


def get_document_path(key):
    if key in DOCUMENT_WALLET.keys():
        return os.path.join(DOCUMENT_WALLET_ROOT, DOCUMENT_WALLET[key])
    else:
        raise ValueError


def is_in_wallet(fpath):
    if DOCUMENT_WALLET_ROOT in os.path.split(fpath)[0]:
        return True
