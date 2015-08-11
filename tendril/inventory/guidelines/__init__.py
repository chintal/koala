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

import os

from tendril.entityhub.guidelines import QtyGuidelines
from tendril.utils.config import INSTANCE_ROOT


electronics_qty_file = os.path.join(INSTANCE_ROOT, 'inventory', 'guidelines', 'electronics-qty.yaml')
logger.info("Loading Electronics Inventory Qty Guidelines from file : " + os.linesep + electronics_qty_file)
electronics_qty = QtyGuidelines(electronics_qty_file)
