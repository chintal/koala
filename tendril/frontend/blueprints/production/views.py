#!/usr/bin/env python
# encoding: utf-8

# Copyright (C) 2015 Chintalagiri Shashank
#
# This file is part of tendril.
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
Docstring for views
"""

from flask import render_template
from flask_user import login_required
from flask import abort
from flask import Response
from flask import jsonify

from . import production as blueprint
from .forms import CreateProductionOrderForm

from tendril.production import order
from tendril.dox import production as dxproduction
from tendril.utils.fsutils import Crumb


@blueprint.route('/orders.json')
@login_required
def orders():
    return jsonify(dxproduction.get_all_prodution_order_snos())


@blueprint.route('/order/new', methods=['POST', 'GET'])
@login_required
def new_production_order():
    form = CreateProductionOrderForm()
    if form.validate_on_submit():
        # Construct Production Order

        # Check for Authorization
        # Nothing right now.

        # Create Order

        # Redirect to Created Indent
        pass
    stage = {'crumbroot': '/production'}
    stage_crumbs = {'breadcrumbs': [Crumb(name="Production", path=""),
                                    Crumb(name="Orders", path="order/"),
                                    Crumb(name="New", path="order/new")],
                    }
    stage.update(stage_crumbs)
    pagetitle = "Create New Production Order"
    return render_template('production_order_new.html', stage=stage, form=form,
                           pagetitle=pagetitle)


@blueprint.route('/manifests/<order_sno>')
@login_required
def manifests(order_sno=None):
    if not order_sno:
        abort(404)
    prod_order = order.ProductionOrder(order_sno)
    rfile = prod_order.collated_manifests_pdf
    if not rfile:
        return "Didn't get a manifest set!"
    try:
        content = open(rfile).read()
        return Response(content, mimetype="application/pdf")
    except IOError as exc:
        return str(exc)


@blueprint.route('/order/<order_sno>')
@blueprint.route('/order/')
@login_required
def production_orders(order_sno=None):
    # Presently only supports getting the latest result. A way to allow
    # any result to be retrieved would be nice.
    if order_sno is None:
        docs = dxproduction.get_all_production_orders_docs()
        stage = {'docs': docs,
                 'crumbroot': '/production',
                 'breadcrumbs': [Crumb(name="Production", path=""),
                                 Crumb(name="Orders", path="order/")],
                 }
        return render_template('production_orders.html', stage=stage,
                               pagetitle="All Production Orders")
    else:
        production_order = order.ProductionOrder(order_sno)
        docs = production_order.docs

        stage = {'docs': docs,
                 'order': production_order,
                 'title': production_order.title,
                 'order_sno': order_sno,
                 'crumbroot': '/production',
                 'breadcrumbs': [Crumb(name="Production", path=""),
                                 Crumb(name="Orders", path="order/"),
                                 Crumb(name=order_sno, path="order/" + order_sno)],  # noqa
                 }
        return render_template('production_order_detail.html', stage=stage,
                               pagetitle="Production Order " + order_sno)


@blueprint.route('/')
@login_required
def main():
    latest_prod = dxproduction.get_all_production_orders_docs(limit=5)
    stage = {'latest_prod': latest_prod,
             'crumbroot': '/production',
             'breadcrumbs': [Crumb(name="Production", path="")],
             }
    return render_template('production_main.html', stage=stage,
                           pagetitle='Production')
