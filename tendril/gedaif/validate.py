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

import tendril.gedaif.projfile
import tendril.gedaif.gsymlib

import tendril.boms.electronics

from tendril.gedaif.conffile import NoGedaProjectException


def check(projectfolder):
    # TODO Ensure attribute promotion is acceptable
    # TODO Ensure attribute visibility is acceptable

    logger.info("Attempting to Validate Project at : " + projectfolder)
    try:
        gpf = tendril.gedaif.projfile.GedaProjectFile(projectfolder)
    except NoGedaProjectException:
        logger.critical("Configs file missing. No further validation will be attempted")
        return False

    logger.debug("Config and Project File loaded. Proceeding with Validation")

    configs = []
    for config in gpf.configsfile.configdata['configurations']:
        configs.append(config['configname'])

    logger.info("Found " + str(len(configs)) + " Configurations.")
    logger.debug("Creating Electronics BOM")
    bom = tendril.boms.electronics.import_pcb(projectfolder)

    for config in configs:
        logger.info("Validating Configuration : " + config)
        logger.debug("Creating Output BOM for Configuration : " + config)
        obom = bom.create_output_bom(config)
        logger.debug("Checking Components for Configuration : " + config)
        for line in obom.lines:
            ident = line.ident
            if not tendril.gedaif.gsymlib.is_recognized(ident) and not ident.startswith('PCB '):
                logger.warning("Component not recognized by gsymlib : " + line.ident + " " + str(line.refdeslist))
            elif not ident.startswith('PCB '):
                symbol = tendril.gedaif.gsymlib.get_symbol(line.ident)
                if symbol.status == "Deprecated":
                    logger.warning("Component or Symbol used is Deprecated : " + line.ident + " " + str(line.refdeslist))
        logger.info("Validation Complete for Configuration : " + config)
