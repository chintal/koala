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
Docstring for order
"""

import os
import yaml
import arrow
from copy import deepcopy

from tendril.dox import docstore
from tendril.entityhub import serialnos

from tendril.entityhub.modules import get_module_instance
from tendril.entityhub.modules import get_module_prototype

from tendril.boms.outputbase import DeltaOutputBom
from tendril.boms.outputbase import CompositeOutputBom
from tendril.entityhub.snomap import SerialNumberMap

from tendril.entityhub.db.controller import SerialNoNotFound
from tendril.entityhub.entitybase import EntityNotFound
from tendril.entityhub.modules import ModuleInstanceTypeMismatchError

from tendril.dox.production import gen_production_order
from tendril.dox.production import gen_delta_pcb_am
from tendril.dox.production import gen_pcb_am
from tendril.dox.production import get_production_order_manifest_set

from tendril.inventory.indent import InventoryIndent

from tendril.utils.db import get_session


class ProductionOrderNotFound(EntityNotFound):
    pass


class DeltaValidationError(Exception):
    pass


class NothingToProduceError(Exception):
    pass


class ProductionActionBase(object):
    def __init__(self, *args, **kwargs):
        self._is_done = None
        self._scaffold = False
        self._session = kwargs.get('session')
        self.setup(*args, **kwargs)

    def set_session(self, session):
        self._session = session

    def unset_session(self):
        self._session = None

    @property
    def scaffold(self):
        return self._scaffold

    @scaffold.setter
    def scaffold(self, value):
        self._scaffold = value

    def setup(self, *args, **kwargs):
        raise NotImplementedError

    def commit(self, outfolder=None,
               indent_sno=None, prod_ord_sno=None,
               register=False, session=None):
        raise NotImplementedError

    @property
    def obom(self):
        raise NotImplementedError

    @property
    def ident(self):
        raise NotImplementedError

    @property
    def refdes(self):
        raise NotImplementedError

    @property
    def modules(self):
        return [get_module_instance(x, self.ident,
                                    scaffold=self._scaffold,
                                    session=self._session)
                for x in self.refdes]

    @property
    def order_lines(self):
        raise NotImplementedError


class DeltaProductionAction(ProductionActionBase):
    def __init__(self, delta_order):
        self._sno = None
        self._original = None
        self._target = None
        self._orig_modulename = None
        self._target_modulename = None
        super(DeltaProductionAction, self).__init__(delta_order)

    def setup(self, delta_order):
        self._sno = delta_order['sno']
        self._orig_modulename = delta_order['orig-cardname']
        self._target_modulename = delta_order['target-cardname']
        try:
            try:
                self._original = get_module_instance(
                        self._sno, self._orig_modulename,
                        session=self._session
                )
                self._target = get_module_prototype(self._target_modulename)
                self._is_done = False
            except ModuleInstanceTypeMismatchError:
                self._target = get_module_instance(
                        self._sno, self._target_modulename,
                        session=self._session
                )
                self._original = get_module_prototype(self._orig_modulename)
                self._is_done = True
        except:
            # TODO a second delta on the same serial number will
            # make the first one fail. The entire delta architecture
            # may need to be thought through. Additionally, this
            # structure only handles deltas between cardnames, and
            # will go to hell in a handbasket if there are any
            # temporal changes to cards.
            raise DeltaValidationError

    def _generate_docs(self, manifestsfolder, indent_sno=None, prod_ord_sno=None,
                       register=False, session=None):
        dmpath = gen_delta_pcb_am(
                self._orig_modulename, self._orig_modulename,
                outfolder=manifestsfolder, sno=self._sno,
                indentsno=indent_sno, productionorderno=prod_ord_sno
        )
        if register is True:
            docstore.register_document(serialno=self._sno, docpath=dmpath,
                                       doctype='DELTA ASSEMBLY MANIFEST',
                                       session=session)

    def commit(self, outfolder=None, indent_sno=None, prod_ord_sno=None,
               register=False, session=None):
        if self._is_done is True:
            raise NothingToProduceError
        self._generate_docs(outfolder, indent_sno, prod_ord_sno, session)
        if register is True:
            serialnos.set_serialno_efield(
                sno=self._sno, efield=self._target_modulename,
                register=register, session=session
            )
            serialnos.link_serialno(
                child=self._sno, parent=prod_ord_sno, session=session
            )
            self._original = get_module_prototype(self._orig_modulename)
            self._target = get_module_instance(self._sno,
                                               self._target_modulename)
            self._is_done = True

    @property
    def delta_bom(self):
        original_obom = self._original.obom
        target_obom = self._target.obom
        delta_obom = DeltaOutputBom(original_obom, target_obom)
        return delta_obom

    @property
    def obom(self):
        return self.delta_bom

    @property
    def ident(self):
        return '{0} -> {1}'.format(self._original.ident, self._target.ident)

    @property
    def refdes(self):
        return [self._sno]

    @property
    def modules(self):
        return [get_module_instance(x, self._target_modulename, self._session)
                for x in self.refdes]

    @property
    def order_lines(self):
        target_prototype = get_module_prototype(self._target_modulename)
        ctx = target_prototype.strategy
        ctx['ident'] = self._target_modulename
        ctx['is_delta'] = True
        ctx['desc'] = self.ident
        ctx['sno'] = self._sno
        return [ctx]

    def __repr__(self):
        if self._is_done is True:
            done = 'DONE'
        elif self._is_done is False:
            done = 'NOT DONE'
        else:
            done = 'NOT DEFINED'
        return '<DeltaProductionAction {0} {1} {2}>'.format(
            self.ident, self.refdes, done
        )


class CardProductionAction(ProductionActionBase):
    def __init__(self, *args, **kwargs):
        self._ident = None
        self._qty = None
        self._prototype = None
        self._snos = None
        super(CardProductionAction, self).__init__(*args, **kwargs)

    def setup(self, card, qty, snofunc):
        self._ident = card
        self._prototype = get_module_prototype(card)
        self._qty = qty
        self._snos = []
        for idx in range(self._qty):
            # Registration is dependent on the snofunc, and consequently
            # the state of the corresponding snomap.
            self._snos.append(snofunc(self.ident))

    def _generate_am(self, manifestsfolder, sno, prod_ord_sno, indent_sno,
                     register=False, session=None):
        ampath = gen_pcb_am(self._ident, manifestsfolder, sno,
                            productionorderno=prod_ord_sno,
                            indentsno=indent_sno, scaffold=self.scaffold,
                            session=session)
        if register is True:
            docstore.register_document(serialno=sno, docpath=ampath,
                                       doctype='ASSEMBLY MANIFEST',
                                       session=session)

    def commit(self, outfolder=None, indent_sno=None, prod_ord_sno=None,
               register=False, session=None):
        # Serial numbers will already have been written in.
        if self._prototype.strategy['genmanifest'] is True:
            for card in self.modules:
                self._generate_am(
                    outfolder, card.refdes, prod_ord_sno, indent_sno,
                    register=register, session=session
                )
                if register is True:
                    serialnos.link_serialno(
                        child=card.refdes, parent=prod_ord_sno,
                        session=session
                    )

    @property
    def obom(self):
        obom = self._prototype.bom.create_output_bom(self.ident)
        obom.multiply(self._qty)
        return obom

    @property
    def ident(self):
        return self._ident

    @property
    def refdes(self):
        return self._snos

    @property
    def order_lines(self):
        rval = []
        base_ctx = self._prototype.strategy
        base_ctx['ident'] = self.ident
        base_ctx['is_delta'] = False
        for card in self.modules:
            ctx = deepcopy(base_ctx)
            ctx['sno'] = card.refdes
            rval.append(ctx)
        return rval


class ProductionOrder(object):
    def __init__(self, sno=None):
        self._sno = sno
        self._card_actions = []
        self._delta_actions = []

        self._last_generated_at = None
        self._first_generated_at = None
        self._title = None
        self._desc = None
        self._indents = []
        self._root_order_snos = []
        self._sourcing_order_snos = []
        self._snomap_path = None
        self._snomap = None
        self._cards = None
        self._deltas = None
        self._order_yaml_path = None
        self._yaml_data = None
        self._ordered_by = None

        try:
            self.load_from_db()
            self._defined = True
        except ProductionOrderNotFound:
            self._defined = False

    def create(self, title=None, desc=None, cards=None, deltas=None,
               sourcing_order_snos=None, root_order_snos=None,
               ordered_by=None, order_yaml_path=None, snomap_path=None):
        # Load in the various parameters and such, creating the necessary
        # containers only.
        if self._defined is True:
            raise Exception("This production order instance seems to be already "
                            "done. You can't 'create' it again.")
        if order_yaml_path is not None:
            self._order_yaml_path = order_yaml_path
            with open(self._order_yaml_path, 'r') as f:
                self._yaml_data = yaml.load(f)
            self._load_order_yaml_data()
        if title is not None:
            self._title = title
        if desc is not None:
            self._desc = desc
        if cards is not None:
            self._cards = self._yaml_data.pop('cards', {})
        if deltas is not None:
            self._deltas = self._yaml_data.pop('deltas', [])
        if sourcing_order_snos is not None:
            self._sourcing_order_snos = self._yaml_data.pop('sourcing_orders', [])
        if root_order_snos is not None:
            self._root_order_snos = self._yaml_data.pop('root_orders', [])
        if ordered_by is not None:
            self._ordered_by = ordered_by
        if snomap_path is not None:
            self._snomap_path = snomap_path

        if len(self._cards) + len(self._deltas) == 0:
            raise NothingToProduceError

    def process(self, session=None, **kwargs):
        if self._defined is True:
            raise Exception("This production order instance seems to be already "
                            "done. You can't 'create' it again.")

        if session is None:
            with get_session() as session:
                return self._process(session=session, **kwargs)
        else:
            return self._process(session=session, **kwargs)

    def _process(self, outfolder=None, manifestsfolder=None,
                 label_manager=None, register=False, session=None):

        if outfolder is None:
            if self._order_yaml_path is not None:
                outfolder = os.path.split(self._order_yaml_path)[0]
            else:
                raise AttributeError('Output folder needs to be defined')

        if manifestsfolder is None:
            manifestsfolder = os.path.join(outfolder, 'manifests')
            if not os.path.exists(manifestsfolder):
                os.makedirs(manifestsfolder)

        if self._sno is None:
            self._sno = serialnos.get_serialno(
                    series='PROD', efield=self._title,
                    register=register, session=session
            )

        # Create Snomap
        if self._snomap_path is not None:
            with open(self._snomap_path, 'r') as f:
                self._snomap = SerialNumberMap(yaml.load(f), self._sno)
        else:
            self._snomap = SerialNumberMap({}, self._sno)

        self._snomap.set_session(session=session)
        if register is True:
            self._snomap.enable_creation()

        indent_sno = self._snomap.get_sno('indentsno')
        if register is True:
            serialnos.link_serialno(child=indent_sno, parent=self.serialno,
                                    session=session)

        # Create cards and deltas and so forth
        actions = self.card_actions + self.delta_actions

        for action in actions:
            if register is False:
                action.scaffold = True
            action.set_session(session=session)
            action.commit(
                outfolder=manifestsfolder,
                indent_sno=indent_sno, prod_ord_sno=self._sno,
                register=register, session=session
            )

        self._snomap.disable_creation()

        cobom = CompositeOutputBom(self.bomlist)

        # Assume Indent is non-empty.
        # Create indent
        indent = InventoryIndent(indent_sno, session=session)
        indent.create(cobom, title="FOR {0}".format(self.serialno),
                      desc=None, prod_order_sno=self.serialno,
                      requested_by=self._ordered_by)

        indent.process(outfolder=outfolder, register=register,
                       session=session)
        self._indents.append(indent)

        # Make production order doc
        self._generate_doc(outfolder=outfolder, register=register,
                           session=session)

        self.make_labels(label_manager=label_manager)
        self._last_generated_at = arrow.utcnow().isoformat()
        if self._first_generated_at is None:
            self._first_generated_at = arrow.utcnow().isoformat()
        for action in actions:
            action.scaffold = False
            action.unset_session()
        self._dump_order_yaml(outfolder=outfolder, register=register,
                              session=session)
        self._snomap.dump_to_file(outfolder)
        self._snomap.unset_session()

        if register is True:
            docstore.register_document(
                    serialno=self.serialno,
                    docpath=os.path.join(outfolder, 'snomap.yaml'),
                    doctype='SNO MAP', efield=self.title,
                    session=session
            )

        self._defined = True

    def _generate_doc(self, outfolder=None, register=False, session=None):
        outpath = gen_production_order(
                outfolder, self.serialno, self._yaml_data, self.lines,
                sourcing_orders=self._sourcing_order_snos,
                root_orders=self.root_order_snos
        )
        if register is True:
            docstore.register_document(
                serialno=self.serialno, docpath=outpath,
                doctype='PRODUCTION ORDER', efield=self.title,
                session=session
            )

    def _build_yaml_data(self):
        self._yaml_data['title'] = self._title
        self._yaml_data['desc'] = self._desc
        self._yaml_data['cards'] = self._cards
        self._yaml_data['deltas'] = self._deltas
        self._yaml_data['sourcing_order_snos'] = self._sourcing_order_snos
        self._yaml_data['root_order_snos'] = self._root_order_snos
        self._yaml_data['first_generated_at'] = self._first_generated_at
        self._yaml_data['last_generated_at'] = self._last_generated_at
        self._yaml_data['ordered_by'] = self._ordered_by
        self._yaml_data['prod_order_sno'] = self._sno

    def _dump_order_yaml(self, outfolder=None, register=False, session=None):
        self._build_yaml_data()
        with open(os.path.join(outfolder, 'order.yaml'), 'w') as f:
            f.write(yaml.dump(self._yaml_data, default_flow_style=False))
        if register is True:
            docstore.register_document(
                    serialno=self.serialno,
                    docpath=os.path.join(outfolder, 'order.yaml'),
                    doctype='PRODUCTION ORDER YAML',
                    efield=self.title, session=session
            )

    def _load_snomap_legacy(self):
        # New form should construct directly from DB
        snomap_path = docstore.get_docs_list_for_sno_doctype(
            serialno=self._sno, doctype='SNO MAP', one=True
        ).path
        with docstore.docstore_fs.open(snomap_path, 'r') as f:
            snomap_data = yaml.load(f)
        self._snomap = SerialNumberMap(snomap_data, self._sno)

    def _load_order_yaml(self):
        try:
            order_path = docstore.get_docs_list_for_sno_doctype(
                serialno=self._sno, doctype='PRODUCTION ORDER YAML', one=True
            ).path
        except SerialNoNotFound:
            raise ProductionOrderNotFound
        with docstore.docstore_fs.open(order_path, 'r') as f:
            self._yaml_data = yaml.load(f)

    def _load_order_yaml_data(self):
        # Following keys are ignored / deprecated:
        #  - register
        #  - halt_on_shortage
        #  - include_refbom_for_no_am
        #  - force_labels
        #
        # All of these are more about run control than defining
        # the production order, and thus are left to the run control
        # code to work out. The order.yaml files are now only
        # going to define things that are not temporally transient.

        self._title = self._yaml_data.get('title')
        self._desc = self._yaml_data.get('title', None)
        self._cards = self._yaml_data.get('cards', {})
        self._deltas = self._yaml_data.get('deltas', [])
        self._sourcing_order_snos = self._yaml_data.get('sourcing_orders', [])
        self._root_order_snos = self._yaml_data.get('root_orders', [])
        self._last_generated_at = self._yaml_data.get('last_generated_at', None)
        self._first_generated_at = self._yaml_data.get('first_generated_at', None)
        self._ordered_by = self._yaml_data.get('ordered_by', None)

    def _load_legacy(self):
        if self._sno is None:
            raise ProductionOrderNotFound
        self._load_order_yaml()
        self._load_order_yaml_data()
        self._load_snomap_legacy()

    def load_from_db(self):
        # Retrieve old production orders. If process is called on a loaded
        # production order, it'll overwrite whatever came before.
        self._load_legacy()

    @property
    def card_orders(self):
        return self._cards

    @property
    def card_actions(self):
        # This first len(..) bit is a litte dicey.
        if not len(self._card_actions):
            for card, qty in self.card_orders.iteritems():
                self._card_actions.append(
                    CardProductionAction(card, qty, self._snomap.get_sno)
                )
        return self._card_actions

    @property
    def card_boms(self):
        return [x.obom for x in self.card_actions]

    @property
    def cards(self):
        rval = []
        for action in self.card_actions:
            rval.extend(action.modules)
        return rval

    @property
    def card_lines(self):
        rval = []
        for action in self.card_actions:
            rval.extend(action.order_lines)
        return rval

    @property
    def delta_orders(self):
        return self._deltas

    @property
    def delta_actions(self):
        # This first len(..) bit is a litte dicey.
        if not len(self._delta_actions):
            for delta in self._deltas:
                self._delta_actions.append(
                        DeltaProductionAction(delta)
                )
        return self._delta_actions

    @property
    def delta_boms(self):
        return [x.obom for x in self.delta_actions]

    @property
    def deltas(self):
        # This will return the original card if the delta hasn't yet been
        # processed. Consider the inconsistency of this behavior and see what
        # to do about it.
        rval = []
        for action in self.delta_actions:
            rval.extend(action.modules)
        return rval

    @property
    def delta_lines(self):
        rval = []
        for action in self.delta_actions:
            rval.extend(action.order_lines)
        return rval

    @property
    def bomlist(self):
        return self.card_boms + self.delta_boms

    @property
    def lines(self):
        return self.card_lines + self.delta_lines

    @property
    def collated_manifests_pdf(self):
        return get_production_order_manifest_set(self.serialno)

    @property
    def title(self):
        return self._title

    @property
    def desc(self):
        if self._desc is None:
            return 'Production Order for {0}'.format(self._title)
        else:
            return self._desc

    @property
    def serialno(self):
        return self._sno

    @property
    def root_orders(self):
        pass

    @property
    def root_order_snos(self):
        return self._root_order_snos

    @property
    def indent_snos(self):
        if 'indentsno' in self._snomap.map_keys():
            return self._snomap.mapped_snos('indentsno')
        else:
            return []

    @property
    def indents(self):
        if self._indents is None:
            from tendril.inventory.indent import InventoryIndent
            return [InventoryIndent(x) for x in self.indent_snos]
        else:
            return self._indents

    @property
    def docs(self):
        return docstore.get_docs_list_for_serialno(serialno=self.serialno)

    @property
    def status(self):
        return

    def make_labels(self, label_manager=None, include_all_indents=False):
        if include_all_indents is True:
            for indent in self.indents:
                indent.make_labels(label_manager=label_manager)
        else:
            if len(self.indent_snos):
                self.indents[-1].make_labels(label_manager=label_manager)
        for card in self.cards:
            card.make_labels(label_manager=label_manager)
        for delta in self.deltas:
            delta.make_labels(label_manager=label_manager)

    def __repr__(self):
        return '<Production Order {0} {1}>'.format(self.serialno, self.title)
