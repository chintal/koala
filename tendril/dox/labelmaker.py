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
import qrcode
import atexit
import cPickle

import render
from tendril.utils.fs import TEMPDIR
from tendril.utils.config import COMPANY_NAME
from tendril.utils.config import COMPANY_LOGO_PATH
from tendril.utils.config import INSTANCE_CACHE


LABEL_TEMPLATES_ROOT = 'labels'


class LabelBase(object):

    templatefile = None

    def __init__(self, code, ident, sno, branding=None, logo=None,
                 include_qr=True, include_logo=True):
        self._code = code
        self._sno = sno
        self._ident = ident
        if branding is None:
            self._branding = COMPANY_NAME
        else:
            self._branding = branding
        if logo is None and include_logo is True:
            self._logo = COMPANY_LOGO_PATH
        else:
            self._logo = logo
        self._include_qr = include_qr
        self._include_logo = include_logo
        self._qr_path = None
        if self._include_qr is True:
            self._gen_qrcode()

    @property
    def code(self):
        return self._code

    @property
    def sno(self):
        return self._sno

    @property
    def ident(self):
        # if len(self._ident) > 16:
        #     return r"\tiny " + self._ident
        # if len(self._ident) > 14:
        #     return r"\scriptsize " + self._ident
        # else:
        return r"\footnotesize " + self._ident

    @property
    def branding(self):
        return self._branding

    @property
    def include_logo(self):
        return self._include_logo

    @property
    def include_qr(self):
        return self._include_qr

    @property
    def logo(self):
        return self._logo

    @property
    def qrcode(self):
        return self._qr_path

    def _gen_qrcode(self, wfpath=None):
        if wfpath is None:
            wfpath = os.path.join(TEMPDIR, 'qrcache')
            if not os.path.exists(wfpath):
                os.makedirs(wfpath)
        qr = qrcode.make(self._ident + ' ' + self._sno)
        self._qr_path = os.path.join(wfpath, 'QR-' + self._ident + '-' + self._sno + '.png')
        qr.save(self._qr_path)

    def __repr__(self):
        return "<Label for " + self._ident + ' ' + self._sno + '>'


class LabelCW1(LabelBase):
    templatefile = os.path.join(LABEL_TEMPLATES_ROOT, 'CW1_template.tex')
    lpp = 88


class LabelP1(LabelBase):
    templatefile = os.path.join(LABEL_TEMPLATES_ROOT, 'CW1_template.tex')
    lpp = 88


class LabelP2(LabelBase):
    templatefile = os.path.join(LABEL_TEMPLATES_ROOT, 'P2_template.tex')
    lpp = 120


class LabelD1(LabelBase):
    templatefile = os.path.join(LABEL_TEMPLATES_ROOT, 'CW1_template.tex')
    lpp = 88


class LabelIDT(LabelBase):
    templatefile = os.path.join(LABEL_TEMPLATES_ROOT, 'IDT_template.tex')
    lpp = 88

    def __init__(self, code, ident, sno, **kwargs):
        super(LabelIDT, self).__init__(code, ident, sno,
                                       include_logo=False, include_qr=False)
        self._qty = kwargs['qty']

    @property
    def qty(self):
        return self._qty

    @property
    def ident(self):
        return self._ident


def get_labelbase(code):
    # TODO change this dispatch to use introspection instead
    if code == 'CW1':
        return LabelCW1
    elif code == 'D1':
        return LabelD1
    elif code == 'P1':
        return LabelP1
    elif code == 'P2':
        return LabelP2
    elif code == 'IDT':
        return LabelIDT
    else:
        return LabelBase


class LabelSheet(object):
    def __init__(self, base, code):
        self._base = base
        self._code = code
        self._labels = []

    @property
    def code(self):
        return self._code

    @property
    def base(self):
        return self._base

    @property
    def labels(self):
        for label in self._labels:
            yield label

    def add_label(self, label):
        self._labels.append(label)

    @property
    def nl(self):
        return len(self._labels)

    def generate_pdf(self, targetfolder, force=True):
        labels = [label for label in self._labels]
        nl = len(labels)
        sheets, remain = divmod(nl, self.base.lpp)
        if nl == 0:
            return None
        if remain > self.base.lpp * 0.8 or force is True:
            stage = {'labels': labels}
            self._labels = []
            logger.info("Creating all labels for sheet : " + self._code)
        elif sheets > 0:
            stage = {'labels': labels[:self.base.lpp * sheets]}
            self._labels = labels[self.base.lpp * sheets:]
            logger.info("Holding back " + str(remain) + " labels for sheet : " + self._code)
        else:
            logger.info("Not generating labels for sheet : " + self._code + ' ' + str(remain))
            return None
        return render.render_pdf(stage, self._base.templatefile,
                                 os.path.join(targetfolder, 'labels-' + self.code + '.pdf'))

    def clear_sno_label(self, sno):
        if self._labels is None:
            self._labels = []
        for label in self._labels:
            if label.sno == sno:
                self._labels.remove(label)


class LabelMaker(object):
    def __init__(self):
        self._sheets = []

    def add_label(self, code, ident, sno, **kwargs):
        self._clear_sno_label(sno)
        sheet = self._get_sheet(code)
        label = sheet.base(code, ident, sno, **kwargs)
        sheet.add_label(label)

    def _get_sheet(self, code):
        if code not in self._sheetdict.keys():
            self._sheets.append(LabelSheet(get_labelbase(code), code))
        return self._sheetdict[code]

    @property
    def _sheetdict(self):
        return {x.code: x for x in self._sheets}

    def generate_pdfs(self, targetfolder, force=False):
        rval = []
        for sheet in self._sheets:
            opath = sheet.generate_pdf(targetfolder, force)
            if opath is not None:
                rval.append(opath)
        return rval

    @property
    def nl(self):
        return sum([x.nl for x in self._sheets])

    def _clear_sno_label(self, sno):
        for sheet in self._sheets:
            sheet.clear_sno_label(sno)


def get_manager():
    try:
        with open(os.path.join(INSTANCE_CACHE, 'labelmaker.p'), 'rb') as f:
            return cPickle.load(f)
    except IOError:
        return LabelMaker()

manager = get_manager()


def dump_manager():
    with open(os.path.join(INSTANCE_CACHE, 'labelmaker.p'), 'wb') as f:
        cPickle.dump(manager, f)

atexit.register(dump_manager)
