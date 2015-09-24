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

from tendril.entityhub import projects
from tendril.dox import gedaproject
from tendril.utils import log
logger = log.get_logger(__name__, log.DEFAULT)

if __name__ == '__main__':
    for project in projects.projects:
        logger.info(
            "Checking " + project +
            " for changes and updating documentation"
        )
        gedaproject.generate_docs(projects.projects[project])
