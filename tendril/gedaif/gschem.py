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
gEDA gschem module documentation (:mod:`gedaif.gschem`)
=======================================================
"""

import re
import os
import subprocess
from collections import deque

import tendril.utils.log
logger = tendril.utils.log.get_logger(__name__, tendril.utils.log.INFO)

rex_vstring = re.compile(ur'^v (?P<gsch_ver>\d+) (?P<file_ver>\d+)$')

rex_el_line = re.compile(ur'^L (?P<x1>-?\d+) (?P<y1>-?\d+) (?P<x2>-?\d+) (?P<y2>-?\d+) (?P<color>\d+) (?P<width>\d+) (?P<capstyle>\d+) (?P<dashstyle>-?\d+) (?P<dashlength>-?\d+) (?P<dashspace>-?\d+)$')
rex_el_picture = re.compile(ur'^G (?P<x1>-?\d+) (?P<y1>-?\d+) (?P<width>\d+) (?P<height>\d+) (?P<angle>\d+) (?P<mirrored>[01]) (?P<embedded>[01])$')
rex_el_box = re.compile(ur'^B (?P<x>-?\d+) (?P<y>-?\d+) (?P<boxwidth>-?\d+) (?P<boxheight>-?\d+) (?P<color>\d+) (?P<width>\d+) (?P<capstyle>[012]) (?P<dashstyle>[01234]) (?P<dashlength>-?\d+) (?P<dashspace>-?\d+) (?P<filltype>[01234]) (?P<fillwidth>-?\d+) (?P<angle1>-?\d+) (?P<pitch1>-?\d+) (?P<angle2>-?\d+) (?P<pitch2>-?\d+)$')
rex_el_circle = re.compile(ur'^V (?P<x>-?\d+) (?P<y>-?\d+) (?P<radius>-?\d+) (?P<color>\d+) (?P<width>\d+) (?P<capstyle>[0]) (?P<dashstyle>[01234]) (?P<dashlength>-?\d+) (?P<dashspace>-?\d+) (?P<filltype>[01234]) (?P<fillwidth>-?\d+) (?P<angle1>-?\d+) (?P<pitch1>-?\d+) (?P<angle2>-?\d+) (?P<pitch2>-?\d+)$')
rex_el_arc = re.compile(ur'^A (?P<x>-?\d+) (?P<y>-?\d+) (?P<radius>-?\d+) (?P<startangle>-?\d+) (?P<sweepangle>-?\d+) (?P<color>\d+) (?P<width>\d+) (?P<capstyle>[0]) (?P<dashstyle>[01234]) (?P<dashlength>-?\d+) (?P<dashspace>-?\d+)$')
rex_el_text = re.compile(ur'^T (?P<x>-?\d+) (?P<y>-?\d+) (?P<color>\d+) (?P<size>\d+) (?P<visibility>[01]) (?P<show_name_value>[012]) (?P<angle>\d+) (?P<alignment>[0-8]) (?P<num_lines>\d+)$')
rex_el_net = re.compile(ur'^N (?P<x1>-?\d+) (?P<y1>-?\d+) (?P<x2>-?\d+) (?P<y2>-?\d+) (?P<color>\d+)$')
rex_el_bus = re.compile(ur'^U (?P<x1>-?\d+) (?P<y1>-?\d+) (?P<x2>-?\d+) (?P<y2>-?\d+) (?P<color>\d+) (?P<ripperdir>-?\d)$')
rex_el_pin = re.compile(ur'^P (?P<x1>-?\d+) (?P<y1>-?\d+) (?P<x2>-?\d+) (?P<y2>-?\d+) (?P<color>\d+) (?P<pintype>[01]) (?P<whichend>[01])$')
rex_el_component = re.compile(ur'^C (?P<x>-?\d+) (?P<y>-?\d+) (?P<selectable>[01]) (?P<angle>\d+) (?P<mirror>[01]) (?P<basename>[\w.+ -]*)$')
rex_el_path = re.compile(ur'^H (?P<color>\d+) (?P<width>\d+) (?P<capstyle>[012]) (?P<dashstyle>[01234]) (?P<dashlength>-?\d+) (?P<dashspace>-?\d+) (?P<filltype>[01234]) (?P<fillwidth>-?\d+) (?P<angle1>-?\d+) (?P<pitch1>-?\d+) (?P<angle2>-?\d+) (?P<pitch2>-?\d+) (?P<num_lines>[\d]+)$')

rex_block_start = re.compile(ur'^\s*[{]\s*$')
rex_block_end = re.compile(ur'^\s*[}]\s*$')


map_color = {0: 'BACKGROUND_COLOR',
             1: 'PIN_COLOR',
             2: 'NET_ENDPOINT_COLOR',
             3: 'GRAPHIC_COLOR',
             4: 'NET_COLOR',
             5: 'ATTRIBUTE_COLOR',
             6: 'LOGIC_BUBBLE_COLOR',
             7: 'DOTS_GRID_COLOR',
             8: 'DETACHED_ATTRIBUTE_COLOR',
             9: 'TEXT_COLOR',
             10: 'BUS_COLOR',
             11: 'SELECT_COLOR',
             12: 'BOUNDINGBOX_COLOR',
             13: 'ZOOM_BOX_COLOR',
             14: 'STROKE_COLOR',
             15: 'LOCK_COLOR',
             16: 'OUTPUT_BACKGROUND_COLOR',
             17: 'FREESTYLE1_COLOR',
             18: 'FREESTYLE2_COLOR',
             19: 'FREESTYLE3_COLOR',
             20: 'FREESTYLE4_COLOR',
             21: 'JUNCTION_COLOR',
             22: 'MESH_GRID_MAJOR_COLOR',
             23: 'MESH_GRID_MINOR_COLOR'
             }

map_capstyle = {0: 'END NONE',
                1: 'END SQUARE',
                2: 'END ROUND'
                }

map_dashstyle = {0: 'TYPE SOLID',
                 1: 'TYPE DOTTED',
                 2: 'TYPE DASHED',
                 3: 'TYPE CENTER',
                 4: 'TYPE PHANTOM'
                 }

map_filltype = {0: 'FILLING HOLLOW',
                1: 'FILLING FILL',
                2: 'FILLING MESH',
                3: 'FILLING HATCH',
                4: 'FILLING VOID'
                }

map_pintype = {0: 'NORMAL PIN',
               1: 'BUS PIN'
               }

map_shownamevalue = {0: 'SHOW NAME VALUE',
                     1: 'SHOW VALUE',
                     2: 'SHOW NAME'
                     }


import tendril.utils.pdf
from tendril.utils.types.cartesian import CartesianPoint
from tendril.utils.types.cartesian import CartesianLineSegment

from tendril.utils.config import GEDA_SCHEME_DIR


class GschPoint(CartesianPoint):
    unit = 'mil'

    def __init__(self, parent, x, y):
        super(GschPoint, self).__init__(x, y)
        self._parent = parent

    @property
    def parent(self):
        return self._parent


class GschLine(CartesianLineSegment):
    def __init__(self, parent, p1, p2):
        super(GschLine, self).__init__(p1, p2)
        self._parent = parent

    @property
    def parent(self):
        return self._parent


class GschElementBase(object):
    def __init__(self, parent, lines, **kwargs):
        for k, v in kwargs.items():
            try:
                setattr(self, k, int(v))
            except ValueError:
                setattr(self, k, v)
        self._parent = parent
        self._elements = []
        self._get_multiline(lines)

    def add_element(self, element):
        self._elements.append(element)

    def _get_multiline(self, lines):
        return

    @property
    def parent(self):
        return self._parent

    @property
    def active_point(self):
        return []

    @property
    def active_points(self):
        rval = self.active_point
        for element in self._elements:
            rval += element.active_points
        return rval

    @property
    def passive_line(self):
        return []

    @property
    def passive_lines(self):
        rval = self.passive_line
        for element in self._elements:
            rval += element.passive_lines
        return rval

    def write_out(self, f):
        raise NotImplementedError


class GschElementComponent(GschElementBase):
    def __init__(self, parent=None, lines=None, **kwargs):
        super(GschElementComponent, self).__init__(parent, lines, **kwargs)


class GschElementNet(GschElementBase):
    def __init__(self, parent=None, lines=None, **kwargs):
        super(GschElementNet, self).__init__(parent, lines, **kwargs)


class GschElementBus(GschElementBase):
    def __init__(self, parent=None, lines=None, **kwargs):
        super(GschElementBus, self).__init__(parent, lines, **kwargs)


class GschElementPin(GschElementBase):
    def __init__(self, parent=None, lines=None, **kwargs):
        super(GschElementPin, self).__init__(parent, lines, **kwargs)


class GschElementLine(GschElementBase):
    def __init__(self, parent=None, lines=None, **kwargs):
        super(GschElementLine, self).__init__(parent, lines, **kwargs)


class GschElementBox(GschElementBase):
    def __init__(self, parent=None, lines=None, **kwargs):
        super(GschElementBox, self).__init__(parent, lines, **kwargs)


class GschElementCircle(GschElementBase):
    def __init__(self, parent=None, lines=None, **kwargs):
        super(GschElementCircle, self).__init__(parent, lines, **kwargs)


class GschElementArc(GschElementBase):
    def __init__(self, parent=None, lines=None, **kwargs):
        super(GschElementArc, self).__init__(parent, lines, **kwargs)


class GschElementText(GschElementBase):
    def __init__(self, parent=None, lines=None, **kwargs):
        super(GschElementText, self).__init__(parent, lines, **kwargs)

    def _get_multiline(self, lines):
        self._lines = []
        for i in range(int(self.num_lines)):
            self._lines.append(lines.popleft())


class GschElementPicture(GschElementBase):
    def __init__(self, parent=None, lines=None, **kwargs):
        super(GschElementPicture, self).__init__(parent, lines, **kwargs)

    def _get_multiline(self, lines):
        self.fpath = lines.popleft()
        self._encoded = []
        if self.embedded == 1:
            line = None
            while line.strip() != '.':
                self._encoded.append(lines.popleft())


class GschElementPath(GschElementBase):
    def __init__(self, parent=None, lines=None, **kwargs):
        super(GschElementPath, self).__init__(parent, lines, **kwargs)

    def _get_multiline(self, lines):
        self._segments = []
        for i in range(int(self.num_lines)):
            self._segments.append(lines.popleft())


class GschFile(object):
    def __init__(self, fpath):
        self.fpath = fpath
        self._elements = []
        self._load_file()

    def add_element(self, element):
        self._elements.append(element)

    def _get_version(self, lines):
        m = None
        while not m:
            m = rex_vstring.match(lines.popleft())
        self._gschver = m.group('gsch_ver')
        self._filever = m.group('file_ver')

    @staticmethod
    def _get_next_element(parent, lines):
        line = None
        while not line:
            line = lines.popleft()
        if line.startswith('L'):
            return GschElementLine(parent, lines=lines, **rex_el_line.match(line).groupdict())
        elif line.startswith('G'):
            return GschElementPicture(parent, lines=lines, **rex_el_picture.match(line).groupdict())
        elif line.startswith('B'):
            return GschElementBox(parent, lines=lines, **rex_el_box.match(line).groupdict())
        elif line.startswith('V'):
            return GschElementCircle(parent, lines=lines, **rex_el_circle.match(line).groupdict())
        elif line.startswith('A'):
            return GschElementArc(parent, lines=lines, **rex_el_arc.match(line).groupdict())
        elif line.startswith('T'):
            return GschElementText(parent, lines=lines, **rex_el_text.match(line).groupdict())
        elif line.startswith('N'):
            return GschElementNet(parent, lines=lines, **rex_el_net.match(line).groupdict())
        elif line.startswith('U'):
            return GschElementBus(parent, lines=lines, **rex_el_bus.match(line).groupdict())
        elif line.startswith('P'):
            return GschElementPin(parent, lines=lines, **rex_el_pin.match(line).groupdict())
        elif line.startswith('C'):
            return GschElementComponent(parent, lines=lines, **rex_el_component.match(line).groupdict())
        elif line.startswith('H'):
            return GschElementPath(parent, lines=lines, **rex_el_path.match(line).groupdict())
        else:
            raise AttributeError(line)

    def _load_file(self):
        with open(self.fpath, 'r') as f:
            lines = deque(f.readlines())
        self._get_version(lines)
        block_level = 0
        targets = {0: self}
        element = None
        while len(lines):
            if rex_block_start.match(lines[0]):
                if not element:
                    raise Exception
                block_level += 1
                targets[block_level] = element
                lines.popleft()
            elif rex_block_end.match(lines[0]):
                block_level -= 1
                lines.popleft()
            element = self._get_next_element(targets[block_level], lines)
            targets[block_level].add_element(element)

    def write_out(self, f):
        raise NotImplementedError


def conv_gsch2pdf(schpath, docfolder):
    schpath = os.path.normpath(schpath)
    schfname = os.path.splitext(os.path.split(schpath)[1])[0]
    pspath = os.path.join(docfolder, schfname + '.ps')
    pdfpath = os.path.join(docfolder, schfname + '.pdf')
    gschem_pscmd = "gschem -o" + pspath + " -s" + GEDA_SCHEME_DIR + '/print.scm ' + schpath
    subprocess.call(gschem_pscmd.split(' '))
    tendril.utils.pdf.conv_ps2pdf(pspath, pdfpath)
    os.remove(pspath)
    return pdfpath


def conv_gsch2png(schpath, outfolder):
    schpath = os.path.normpath(schpath)
    schfname, ext = os.path.splitext(os.path.split(schpath)[1])

    outpath = os.path.join(outfolder, schfname + '.png')
    epspath = os.path.join(outfolder, schfname + '.eps')

    if ext == '.sym':
        gschem_epscmd = ["sym2eps", schpath, epspath]
        try:
            subprocess.check_call(gschem_epscmd)
            gschem_pngcmd = ["convert", epspath, "-transparent", "white", outpath]
            subprocess.call(gschem_pngcmd)
            os.remove(epspath)
        except subprocess.CalledProcessError:
            logger.error("SYM2EPS Segmentation Fault on symbol : " + schpath)
    elif ext == '.sch':
        gschem_pngcmd = "gschem -p -o" + outpath + " -s" + GEDA_SCHEME_DIR + '/image.scm ' + schpath
        subprocess.call(gschem_pngcmd)
    return outpath


if __name__ == "__main__":
    pass
