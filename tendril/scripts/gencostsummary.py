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
import csv

from tendril.entityhub import projects
from tendril.gedaif import conffile

from tendril.utils.config import INSTANCE_ROOT


if __name__ == '__main__':
    fpath = os.path.join(INSTANCE_ROOT, 'scratch', 'costing-summary-all.csv')
    with open(fpath, 'w') as f:
        writer = csv.writer(f)
        writer.writerow(["Card", "Indicative Cost"])
        for card, cardfolder in sorted(projects.cards.iteritems()):
            cfg = conffile.ConfigsFile(cardfolder)
            for configuration in cfg.configdata['configurations']:
                if configuration['configname'] == card:
                    carddesc = configuration['desc']
            if carddesc is None:
                carddesc = ''
            cost = projects.get_card_indicative_cost(card)
            if cost is not None:
                writer.writerow([card, round(cost), carddesc])
            else:
                writer.writerow([card, None, carddesc])
