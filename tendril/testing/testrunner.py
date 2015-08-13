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


from tendril.utils import log
logger = log.get_logger(__name__, log.DEFAULT)

import sys
import copy

from tendril.entityhub import serialnos
from tendril.entityhub import projects

from tendril.gedaif.conffile import ConfigsFile
from tendril.gedaif.conffile import NoGedaProjectException
from tendril.boms.electronics import import_pcb

from testbase import TestSuiteBase
from testbase import TestPrepUser

from tests import get_test_object

from db import controller


def add_prep_steps_from_cnf_prep(testobj, cnf_prep):
    for step in cnf_prep:
        if 'user' in step.keys():
            stepobj = TestPrepUser(step['user'])
            testobj.add_prep(stepobj)


def get_testobj_from_cnf_test(cnf_test, testvars, bomobj):
    if len(cnf_test.keys()) != 1:
        raise ValueError("Test configurations are "
                         "expected to have exactly "
                         "one key at the top level")
    logger.debug("Creating test object : " + cnf_test.keys()[0])
    testobj = get_test_object(cnf_test.keys()[0])
    additionalvars = cnf_test[cnf_test.keys()[0]]
    if 'prep' in additionalvars.keys():
        add_prep_steps_from_cnf_prep(testobj, additionalvars.pop('prep'))
    vardict = copy.copy(testvars)
    if additionalvars is not None:
        vardict.update(additionalvars)
    logger.debug("Configuring test object : " + cnf_test.keys()[0])
    if 'desc' in vardict.keys():
        testobj.desc = vardict.pop('desc')
    testobj.configure(**vardict)
    testobj.use_bom(bomobj)
    logger.info("Adding test object to suite : " + repr(testobj))
    return testobj


def get_suiteobj_from_cnf_suite(cnf_suite, gcf, devicetype):
    if len(cnf_suite.keys()) != 1:
        raise ValueError("Suite configurations are expected "
                         "to have exactly one key at the top level")
    cnf_suite_name = cnf_suite.keys()[0]
    testvars = gcf.testvars(devicetype)
    bomobj = import_pcb(gcf.projectfolder)
    bomobj.configure_motifs(devicetype)
    logger.debug("Creating test suite : " + cnf_suite_name)
    if cnf_suite_name == "TestSuiteBase":
        suite = TestSuiteBase()
        suite_detail = cnf_suite[cnf_suite_name]
        if 'prep' in suite_detail.keys():
            add_prep_steps_from_cnf_prep(suite, suite_detail['prep'])
        if 'group-tests' in suite_detail.keys():
            cnf_groups = suite_detail['group-tests']
            cnf_grouplist = gcf.grouplist(devicetype)
            for cnf_group in cnf_groups:
                if len(cnf_suite.keys()) != 1:
                    raise ValueError("Group test configurations are "
                                     "expected to have exactly one "
                                     "key at the top level")
                logger.debug("Creating group tests : " + cnf_group.keys()[0])
                if cnf_group.keys()[0] in cnf_grouplist:
                    cnf_test_list = cnf_group[cnf_group.keys()[0]]
                    for cnf_test in cnf_test_list:
                        suite.add_test(get_testobj_from_cnf_test(cnf_test, testvars, bomobj))
    else:
        suite = get_test_object(cnf_suite)
    if 'desc' in cnf_suite.keys():
        suite.desc = cnf_suite['desc']
    return suite


def get_electronics_test_suites(serialno, devicetype, projectfolder):
    try:
        gcf = ConfigsFile(projectfolder)
        logger.info("Using gEDA configs file from : " + projects.cards[devicetype])
    except NoGedaProjectException:
        raise AttributeError("gEDA project for " + devicetype + " not found.")
    suites = []
    cnf_suites = gcf.tests()
    for cnf_suite in cnf_suites:
        suite = get_suiteobj_from_cnf_suite(cnf_suite, gcf, devicetype)
        suite.serialno = serialno
        logger.info("Created test suite : " + repr(suite))
        suites.append(suite)
    return suites


def run_electronics_test(serialno, devicetype, projectfolder):
    suites = get_electronics_test_suites(serialno, devicetype, projectfolder)
    for suite in suites:
        suite.run_test()
    return suites


def commit_test_results(suites):
    for suite in suites:
        controller.commit_test_suite(suiteobj=suite)


def run_test(serialno=None):
    if serialno is None:
        raise AttributeError("serialno cannot be None")
    logger.info("Staring test for serial no : " + serialno)

    devicetype = serialnos.get_serialno_efield(sno=serialno)
    logger.info(serialno + " is device : " + devicetype)

    try:
        projectfolder = projects.cards[devicetype]
    except KeyError:
        raise AttributeError("Project for " + devicetype + " not found.")

    suites = run_electronics_test(serialno, devicetype, projectfolder)

    user_input = raw_input("Commit Results [y/n] ?: ").strip()
    if user_input.lower() in ['y', 'yes', 'ok', 'pass']:
        commit_test_results(suites)
    for suite in suites:
        suite.finish()

    return suites


if __name__ == '__main__':
    run_test(sys.argv[1])
