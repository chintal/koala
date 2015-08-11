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
logger = log.get_logger(__name__, log.DEFAULT)

import csv
from entitybase import EntityBase

from tendril.conventions.electronics import fpiswire
from tendril.conventions.electronics import parse_ident
from tendril.utils.types.lengths import Length


class OutputElnBomDescriptor(object):
    def __init__(self, pcbname, cardfolder, configname, configurations, multiplier=1):
        self.pcbname = pcbname
        self.cardfolder = cardfolder
        self.configname = configname
        self.multiplier = multiplier
        self.configurations = configurations


class OutputBomLine(object):

    def __init__(self, comp, parent):
        assert isinstance(comp, EntityBase)
        self.ident = comp.ident
        self.refdeslist = []
        self.parent = parent

    def add(self, comp):
        assert isinstance(comp, EntityBase)
        if comp.fillstatus == "DNP":
            return
        if comp.fillstatus == "CONF":
            logger.warning("Configurable Component not Configured by Conf File : " + comp.refdes)
        if comp.ident == self.ident:
            self.refdeslist.append(comp.refdes)
        else:
            logger.error("Ident Mismatch")

    @property
    def quantity(self):
        device, value, footprint = parse_ident(self.ident)
        if device is None:
            logger.warning("Device not identified : " + self.ident)
        elif fpiswire(device):
            try:
                elen = Length(footprint) * 10 / 100
                if elen < Length('5mm'):
                    elen = Length('5mm')
                elif elen > Length('1inch'):
                    elen = Length('1inch')
                return len(self.refdeslist) * (Length(footprint) + elen) * self.parent.descriptor.multiplier
            except ValueError:
                logger.error("Problem parsing length for ident : " + self.ident)
                raise
        return len(self.refdeslist) * self.parent.descriptor.multiplier

    def __repr__(self):
        return "{0:<50} {1:<4} {2}".format(self.ident, self.quantity, str(self.refdeslist))


class OutputBom(object):

    def __init__(self, descriptor):
        """

        :type descriptor: outputbase.OutputElnBomDescriptor
        """
        self.lines = []
        self.descriptor = descriptor

    def sort_by_ident(self):
        self.lines.sort(key=lambda x: x.ident, reverse=False)
        for line in self.lines:
            line.refdeslist.sort()

    def find_by_ident(self, ident):
        for line in self.lines:
            assert isinstance(line, OutputBomLine)
            if line.ident == ident:
                return line
        return None

    def insert_component(self, item):
        assert isinstance(item, EntityBase)
        line = self.find_by_ident(item.ident)
        if line is None:
            line = OutputBomLine(item, self)
            self.lines.append(line)
        line.add(item)

    def multiply(self, factor, composite=False):
        if composite is True:
            self.descriptor.multiplier = self.descriptor.multiplier * factor
        else:
            self.descriptor.multiplier = factor


class CompositeOutputBomLine(object):

    def __init__(self, line, colcount):
        self.ident = line.ident
        self.columns = [0] * colcount

    def add(self, line, column):
        """

        :type line: outputbase.OutputBomLine
        """
        if line.ident == self.ident:
            self.columns[column] = line.quantity
        else:
            logger.error("Ident Mismatch")

    @property
    def quantity(self):
        try:
            return sum(self.columns)
        except TypeError:
            print self.ident
            raise TypeError(self.columns)

    def subset_qty(self, idxs):
        try:
            rval = 0
            for idx in idxs:
                rval += self.columns[idx]
            return rval
        except TypeError:
            print self.ident
            raise TypeError(self.columns)

    def merge_line(self, cline):
        for idx, column in enumerate(self.columns):
            self.columns[idx] += cline.columns[idx]


class CompositeOutputBom(object):
    def __init__(self, bom_list):
        self.descriptors = []
        self.lines = []
        self.colcount = len(bom_list)
        i = 0
        for bom in bom_list:
            self.insert_bom(bom, i)
            i += 1
        self.sort_by_ident()

    def get_subset_idxs(self, confignames):
        rval = []
        for configname in confignames:
            for idx, descriptor in enumerate(self.descriptors):
                if descriptor.configname == configname:
                    rval.append(idx)
        return rval

    def insert_bom(self, bom, i):
        """

        :type bom: outputbase.OutputBom
        """
        self.descriptors.append(bom.descriptor)
        for line in bom.lines:
            self.insert_line(line, i)

    def insert_line(self, line, i):
        """

        :type line: outputbase.OutputBomLine
        """
        cline = self.find_by_ident(line.ident)
        if cline is None:
            cline = CompositeOutputBomLine(line, self.colcount)
            self.lines.append(cline)
        cline.add(line, i)

    def find_by_ident(self, ident):
        """

        :type line: outputbase.OutputBomLine
        """
        for cline in self.lines:
            assert isinstance(cline, CompositeOutputBomLine)
            if cline.ident == ident:
                return cline
        return None

    def sort_by_ident(self):
        self.lines.sort(key=lambda x: x.ident, reverse=False)

    def dump(self, stream):
        writer = csv.writer(stream)
        writer.writerow(['device'] + [x.configname + ' x' + str(x.multiplier) for x in self.descriptors] + ['Total'])
        for line in self.lines:
            columns = [None if x == 0 else x for x in line.columns]
            writer.writerow([line.ident] + columns + [line.quantity])

    def collapse_wires(self):
        for line in self.lines:
            device, value, footprint = parse_ident(line.ident)
            if device is None:
                continue
            if fpiswire(device):
                newident = device + ' ' + value
                newline = self.find_by_ident(newident)
                if newline is None:
                    line.ident = newident
                else:
                    newline.merge_line(line)
                    self.lines.remove(line)
