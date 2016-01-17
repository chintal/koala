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
import argparse

from tendril.entityhub import projects
from tendril.sourcing import csil

from tendril.gedaif.conffile import NoGedaProjectException
from tendril.gedaif import conffile

from tendril.utils.config import PROJECTS_ROOT
from tendril.utils.fsutils import in_directory
from tendril.utils import log
logger = log.get_logger("genpcbpricing", log.DEFAULT)


def regenerate_all(force=False, lazy=False, dry_run=False):
    for project in projects.pcbs:
        if dry_run:
            conffile.ConfigsFile(projects.pcbs[project])
            logger.info("Will check " + projects.pcbs[project])
        else:
            logger.info("Checking " + projects.pcbs[project])
            csil.generate_pcb_pricing(projects.pcbs[project],
                                      forceregen=force, noregen=lazy)


def main():
    parser = argparse.ArgumentParser(
        description='(Re-)Generate CSIL PCB Pricing Information.',
        prog='tendril-genpcbpricing'
    )
    parser.add_argument(
        'projfolders', metavar='PATH', type=str, nargs='*',
        help='gEDA PCB Project Folder(s), ignored for --all'
    )
    parser.add_argument(
        '--force', '-f', action='store_true', default=False,
        help='Regenerate pricing even if it seems to be up-to-date'
    )
    parser.add_argument(
        '--lazy', '-l', action='store_true', default=False,
        help="Don't regenerate pricing if it exists, even if it "
             "seems to be out-of-date"
    )
    parser.add_argument(
        '--all', '-a', action='store_true', default=False,
        help='Regenerate pricing for all projects'
    )
    parser.add_argument(
        '--recurse', '-r', action='store_true', default=False,
        help='Recursively search for projects under each provided folder'
    )
    parser.add_argument(
        '--dry-run', '-n', action='store_true', default=False,
        help="Dry run only. Don't do anything which can change the filesystem"
    )

    args = parser.parse_args()
    force = args.force
    lazy = args.lazy
    if args.all:
        regenerate_all(force=force, lazy=lazy, dry_run=args.dry_run)
    else:
        if not len(args.projfolders):
            parser.print_help()
        for projfolder in args.projfolders:
            if not os.path.isabs(projfolder):
                projfolder = os.path.join(os.getcwd(), projfolder)
                projfolder = os.path.normpath(projfolder)
            if not in_directory(projfolder, PROJECTS_ROOT):
                logger.error(
                    'Provided directory does not seem to be under the '
                    'tendril PROJECTS_ROOT. Skipping ' + projfolder
                )
                continue
            targets = [projfolder]
            if args.recurse:
                lprojects, lpcbs, lcards, lcard_reporoot = \
                    projects.get_projects(projfolder)
                targets.extend([lpcbs[x] for x in lpcbs.keys()])
            for target in targets:
                try:
                    if args.dry_run is False:
                        csil.generate_pcb_pricing(
                            target, forceregen=force, noregen=lazy
                        )
                        logger.info("Checked " + target)
                    else:
                        conffile.ConfigsFile(target)
                        logger.info("Will check " + target)
                except NoGedaProjectException:
                    # Make a guess.
                    if os.path.split(target)[1] == 'configs.yaml':
                        target == os.path.split(target)[0]
                    if os.path.split(target)[1] == 'schematic':
                        target == os.path.split(target)[0]
                    try:
                        if args.dry_run is False:
                            csil.generate_pcb_pricing(
                                target, forceregen=force, noregen=lazy
                            )
                            logger.info("Checked " + target)
                        else:
                            conffile.ConfigsFile(target)
                            logger.info("Will check " + target)
                    except NoGedaProjectException:
                        logger.error("No gEDA Project found at " + target)


if __name__ == '__main__':
    main()
