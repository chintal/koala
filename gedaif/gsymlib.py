"""
gEDA gsymlib Module documentation (:mod:`gedaif.gsymlib`)
=========================================================
"""

import os
import csv
import logging

import yaml
import jinja2

from utils.config import GEDA_SYMLIB_ROOT
from utils.config import AUDIT_PATH
from utils.config import KOALA_ROOT
from utils.config import INSTANCE_CACHE

import utils.fs
import conventions.electronics
import conventions.iec60063

from gschem import conv_gsch2png


class GedaSymbol(object):
    def __init__(self, fpath):
        self.fpath = fpath
        self.fname = os.path.split(fpath)[1]
        self.device = ''
        self.value = ''
        self.footprint = ''
        self.description = ''
        self.status = ''
        self.package = ''
        self._is_virtual = ''
        self._img_repr_path = ''
        self._img_repr_fname = ''
        self._acq_sym(fpath)
        self._img_repr()

    def _acq_sym(self, fpath):
        with open(fpath, 'r') as f:
            for line in f.readlines():
                if line.startswith('device='):
                    self.device = line.split('=')[1].strip()
                if line.startswith('value='):
                    self.value = line.split('=')[1].strip()
                if line.startswith('footprint'):
                    self.footprint = line.split('=')[1].strip()
                    if self.footprint[0:3] == 'MY-':
                        self.footprint = self.footprint[3:]
                if line.startswith('description'):
                    self.description = line.split('=')[1].strip()
                if line.startswith('status'):
                    self.status = line.split('=')[1].strip()
                if line.startswith('package'):
                    self.package = line.split('=')[1].strip()
            if self.status == '':
                self.status = 'Active'

    def _img_repr(self):
        outfolder = os.path.join(INSTANCE_CACHE, 'gsymlib')
        self._img_repr_fname = os.path.splitext(self.fname)[0]+'.png'
        self._img_repr_path = os.path.join(outfolder, self._img_repr_fname)
        if not os.path.exists(outfolder):
            os.makedirs(outfolder)
        if os.path.exists(self._img_repr_path):
            if utils.fs.get_file_mtime(self._img_repr_path) > utils.fs.get_file_mtime(self.fpath):
                return
        conv_gsch2png(self.fpath, outfolder)

    @property
    def img_repr_fname(self):
        return self._img_repr_fname

    @property
    def ident(self):
        return conventions.electronics.ident_transform(self.device,
                                                       self.value,
                                                       self.footprint)

    @property
    def sym_ok(self):
        rval = False
        if self.device in conventions.electronics.DEVICE_CLASSES:
            rval = True
        return rval

    @property
    def is_generator(self):
        if self.status == 'Generator':
            return True
        return False

    @property
    def is_virtual(self):
        if self.status == 'Virtual':
            return True
        return False

    @property
    def is_deprecated(self):
        if self.status == 'Deprecated':
            return True
        return False

    @property
    def is_experimental(self):
        if self.status == 'Experimental':
            return True
        return False

    @is_virtual.setter
    def is_virtual(self, value):
        if self.status == 'Generator':
            if value is True:
                self.status = 'Virtual'
        else:
            raise AttributeError

    @property
    def is_wire(self):
        return conventions.electronics.fpiswire(self.device)

    @property
    def is_modlen(self):
        return conventions.electronics.fpismodlen(self.device)

    def __repr__(self):
        return '{0:40}'.format(self.ident)


class GSymGeneratorFile(object):
    def __init__(self, sympath):
        self._genpath = os.path.splitext(sympath)[0] + '.gen.yaml'
        data = self._get_data()
        self._values = []
        for value in data:
            if value is not None:
                self._values.append(value)

    def _get_data(self):
        with open(self._genpath) as genfile:
            gendata = yaml.load(genfile)
        if gendata["schema"]["name"] == "gsymgenerator" and \
           gendata["schema"]["version"] == 1.0:

            if gendata['type'] == 'simple':
                return gendata['values']
            values = []

            if gendata['type'] == 'resistor':
                for resistance in gendata['resistances']:
                    values.append(resistance)
                if 'generators' in gendata.keys():
                    for generator in gendata['generators']:
                        if generator['std'] == 'iec60063':
                            rvalues = conventions.iec60063.gen_vals(generator['series'],
                                                                    conventions.iec60063.res_ostrs,
                                                                    start=generator['start'],
                                                                    end=generator['end'])
                            for rvalue in rvalues:
                                values.append(conventions.electronics.construct_resistor(rvalue, generator['wattage']))
                        else:
                            raise ValueError
                if 'values' in gendata.keys():
                    if gendata['values'][0].strip() != '':
                        values += gendata['values']
                return values

            if gendata['type'] == 'capacitor':
                for capacitance in gendata['capacitances']:
                        values.append(capacitance)
                if 'generators' in gendata.keys():
                    for generator in gendata['generators']:
                        if generator['std'] == 'iec60063':
                            cvalues = conventions.iec60063.gen_vals(generator['series'],
                                                                    conventions.iec60063.cap_ostrs,
                                                                    start=generator['start'],
                                                                    end=generator['end'])
                            for cvalue in cvalues:
                                values.append(conventions.electronics.construct_capacitor(cvalue, generator['voltage']))
                        else:
                            raise ValueError
                if 'values' in gendata.keys():
                    if gendata['values'][0].strip() != '':
                        values += gendata['values']
                return values
        else:
            logging.ERROR("Config file schema is not supported")

    @property
    def values(self):
        if len(self._values) > 0:
            return self._values
        return None


def get_folder_symbols(path, template=None, resolve_generators=True, include_generators=False):
    if template is None:
        template = _jinja_init()
    symbols = []
    files = [f for f in os.listdir(path) if os.path.isfile(os.path.join(path, f))]
    for f in files:
        if f.endswith(".sym"):
            symbol = GedaSymbol(os.path.join(path, f))
            if symbol.is_generator:
                if include_generators is True:
                    symbols.append(symbol)
                if resolve_generators is True:
                    genpath = os.path.splitext(symbol.fpath)[0] + '.gen.yaml'
                    if os.path.exists(genpath):
                        genfile = GSymGeneratorFile(symbol.fpath)
                        values = genfile.values
                        if values is not None:
                            for value in values:
                                if value is not None:
                                    vsymbol = GedaSymbol(symbol.fpath)
                                    vsymbol.is_virtual = True
                                    vsymbol.value = value
                                    symbols.append(vsymbol)
                    else:
                        stage = {'symbolfile': os.path.split(symbol.fpath)[1],
                                 'value': symbol.value.strip(),
                                 'description': symbol.description}
                        with open(genpath, 'w') as gf:
                            gf.write(template.render(stage=stage))
            else:
                symbols.append(symbol)
    return symbols


def gen_symlib(path, recursive=True,
               resolve_generators=True, include_generators=False):
    symbols = []
    template = _jinja_init()
    if recursive:
        for root, dirs, files in os.walk(path):
            symbols += get_folder_symbols(root, template,
                                          resolve_generators=resolve_generators,
                                          include_generators=include_generators)
    else:
        symbols = get_folder_symbols(path, template,
                                     resolve_generators=resolve_generators,
                                     include_generators=include_generators)
    return symbols


def _jinja_init():
    loader = jinja2.FileSystemLoader(searchpath=os.path.join(KOALA_ROOT, 'gedaif', 'templates'))
    renderer = jinja2.Environment(loader=loader)
    template_file = 'generator.gen.yaml'
    template = renderer.get_template(template_file)
    return template


gsymlib = gen_symlib(GEDA_SYMLIB_ROOT)
gsymlib_idents = [x.ident for x in gsymlib]


def is_recognized(ident):
    if ident in gsymlib_idents:
        return True
    return False


def get_symbol(ident, case_insensitive=False):
    for symbol in gsymlib:
        if case_insensitive is False:
            if symbol.ident == ident:
                return symbol
        else:
            if symbol.ident.upper() == ident.upper():
                return symbol
    raise ValueError(ident)


def get_symbol_folder(ident, case_insensitive=False):
    symobj = get_symbol(ident, case_insensitive=case_insensitive)
    sympath = symobj.fpath
    symfolder = os.path.split(sympath)[0]
    return os.path.relpath(symfolder, GEDA_SYMLIB_ROOT)


def find_capacitor(capacitance, footprint, device='CAP CER SMD', voltage=None):
    for symbol in gsymlib:
        if symbol.device == device and symbol.footprint == footprint:
            cap, volt = conventions.electronics.parse_capacitor(symbol.value)
            sym_capacitance = conventions.electronics.parse_capacitance(cap)
            if capacitance == sym_capacitance:
                return symbol
    raise ValueError


def find_resistor(resistance, footprint, device='RES SMD', wattage=None):
    if device == 'RES THRU':
        if resistance in [conventions.electronics.parse_resistance(x) for x in conventions.iec60063.gen_vals(conventions.iec60063.get_series('E24'), conventions.iec60063.res_ostrs)]:
            return conventions.electronics.construct_resistor(conventions.electronics.normalize_resistance(resistance), '0.25W')
        else:
            raise ValueError(resistance, device)
    for symbol in gsymlib:
        if symbol.device == device and symbol.footprint == footprint:
            res, watt = conventions.electronics.parse_resistor(symbol.value)
            sym_resistance = conventions.electronics.parse_resistance(res)
            if resistance == sym_resistance:
                return symbol.value
    raise ValueError(resistance)


def export_gsymlib_audit():
    auditfname = os.path.join(AUDIT_PATH, 'gsymlib-audit.csv')
    outf = utils.fs.VersionedOutputFile(auditfname)
    outw = csv.writer(outf)
    outw.writerow(['filename', 'status', 'ident', 'device', 'value',
                   'footprint', 'description', 'path', 'package'])
    for symbol in gsymlib:
        outw.writerow([symbol.fname, symbol.status, symbol.ident, symbol.device, symbol.value,
                       symbol.footprint, symbol.description, symbol.fpath, symbol.package])
    outf.close()
