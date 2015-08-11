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

from flask import render_template
from flask_user import login_required

from . import entityhub as blueprint

from tendril.entityhub import projects as ehprojects
from tendril.gedaif.conffile import ConfigsFile

from tendril.utils.fs import Crumb


@blueprint.route('/cards/')
@login_required
def cards():
    stage_cards = ehprojects.cards
    stage = {'cards': stage_cards,
             'crumbroot': '/entityhub',
             'breadcrumbs': [Crumb(name="Entity Hub", path=""),
                             Crumb(name="Cards", path="cards/")]
             }
    return render_template('entityhub_cards.html', stage=stage,
                           pagetitle="Cards")


@blueprint.route('/pcbs/detail/<pcbname>')
@blueprint.route('/pcbs/')
@login_required
def pcbs(pcbname=None):
    if pcbname is None:
        stage_pcbs = [{'name': k,
                       'configdata': ConfigsFile(v)}
                      for k, v in ehprojects.pcbs.iteritems()]
        stage = {'pcbs': sorted([x for x in stage_pcbs if x['configdata'].status == 'Experimental'],
                                key=lambda y: y['name']) +
                         sorted([x for x in stage_pcbs if x['configdata'].status == 'Active'],  # noqa
                                key=lambda y: y['name']) +
                         sorted([x for x in stage_pcbs if x['configdata'].status == 'Deprecated'],  # noqa
                                key=lambda y: y['name']),
                 'crumbroot': '/entityhub',
                 'breadcrumbs': [Crumb(name="Entity Hub", path=""),
                                 Crumb(name="Bare PCBs", path="pcbs/")]}
        return render_template('entityhub_pcbs.html', stage=stage,
                               pagetitle="Bare PCBs")
    else:
        stage = {'name': pcbname,
                 'configdata': ConfigsFile(ehprojects.pcbs[pcbname]),
                 'crumbroot': '/entityhub',
                 'breadcrumbs': [Crumb(name="Entity Hub", path=""),
                                 Crumb(name="Bare PCBs", path="pcbs/"),
                                 Crumb(name=pcbname, path="pcbs/" + pcbname)]}
        return render_template('entityhub_pcb_detail.html', stage=stage,
                               pagetitle="PCB Details")


@blueprint.route('/projects/')
@login_required
def projects():
    stage_projects = ehprojects.projects
    stage = {'projects': stage_projects,
             'crumbroot': '/entityhub',
             'breadcrumbs': [Crumb(name="Entity Hub", path=""),
                             Crumb(name="gEDA Projects", path="projects/")]
             }
    return render_template('entityhub_projects.html', stage=stage,
                           pagetitle="gEDA Projects")


@blueprint.route('/')
@login_required
def main():
    stage = {}
    return render_template('entityhub_main.html', stage=stage,
                           pagetitle='Entity Hub')
