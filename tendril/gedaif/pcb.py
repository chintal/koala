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

import tendril.utils.log
logger = tendril.utils.log.get_logger(__name__, tendril.utils.log.INFO)

import os
import subprocess
import pyparsing

import tendril.utils.pdf

from tendril.utils.types.lengths import Length
from tendril.utils.types.cartesian import CartesianPoint
from tendril.utils.types.cartesian import CartesianLineSegment


class PCBPoint(CartesianPoint):
    unit = 'mm'

    def __init__(self, parent, x, y):
        super(PCBPoint, self).__init__(x.decimal, y.decimal)
        self._parent = parent

    @property
    def parent(self):
        return self._parent


class PCBLine(CartesianLineSegment):
    def __init__(self, parent, p1, p2):
        super(PCBLine, self).__init__(p1, p2)
        self._parent = parent

    @property
    def parent(self):
        return self._parent


class PCBElementBase(object):
    def __init__(self, tokens):
        if tokens is not None:
            for k in tokens.keys():
                setattr(self, k, tokens[k])
        self._parent = None

    @property
    def parent(self):
        return self._parent

    @parent.setter
    def parent(self, value):
        self._parent = value


# TODO Some refactoring of these classes may be useful


class PCBLayerLine(PCBElementBase):
    def __init__(self, tokens):
        super(PCBLayerLine, self).__init__(tokens)
        self.p1 = PCBPoint(self, self.X1, self.Y1)
        self.p2 = PCBPoint(self, self.X2, self.Y2)
        self.line = PCBLine(self, self.p1, self.p2)


class PCBLayerArc(PCBElementBase):
    def __init__(self, tokens):
        super(PCBLayerArc, self).__init__(tokens)
        # TODO handle arcs in cartesian
        # TODO Sort out relative locations
        self.center = PCBPoint(self, self.X, self.Y)


class PCBLayerText(PCBElementBase):
    def __init__(self, tokens):
        super(PCBLayerText, self).__init__(tokens)
        self.text_origin = PCBPoint(self, self.X, self.Y)


class PCBLayerPolygonVertex(PCBElementBase):
    def __init__(self, tokens):
        super(PCBLayerPolygonVertex, self).__init__(tokens)
        self.vertex = PCBPoint(self, self.X, self.Y)


class PCBLayerPolygonHole(PCBElementBase):
    def __init__(self, tokens):
        super(PCBLayerPolygonHole, self).__init__(tokens)
        if 'Content' in dir(self):
            self.vertices = [l[0] for l in self.Content]
            for line in self.vertices:
                line.parent = self


class PCBLayerPolygon(PCBElementBase):
    def __init__(self, tokens):
        super(PCBLayerPolygon, self).__init__(tokens)
        if 'Content' in dir(self):
            self.vertices = [l[0] for l in self.Content]
            for line in self.vertices:
                line.parent = self


class PCBLayer(PCBElementBase):
    def __init__(self, tokens):
        super(PCBLayer, self).__init__(tokens)
        if 'Content' in dir(self):
            self.content = [l[0] for l in self.Content]
            for line in self.content:
                line.parent = self


class PCBAttribute(PCBElementBase):
    def __init__(self, tokens):
        super(PCBAttribute, self).__init__(tokens)


class PCBSymbolLine(PCBElementBase):
    def __init__(self, tokens):
        super(PCBSymbolLine, self).__init__(tokens)
        self.p1 = PCBPoint(self, self.X1, self.Y1)
        self.p2 = PCBPoint(self, self.X2, self.Y2)
        self.line = PCBLine(self, self.p1, self.p2)


class PCBSymbol(PCBElementBase):
    def __init__(self, tokens):
        super(PCBSymbol, self).__init__(tokens)
        if 'Content' in dir(self):
            self.content = [l[0] for l in self.Content]
            for line in self.content:
                line.parent = self


class PCBElementLine(PCBElementBase):
    def __init__(self, tokens):
        super(PCBElementLine, self).__init__(tokens)
        # TODO Sort out relative locations
        self.p1 = PCBPoint(self, self.X1, self.Y1)
        self.p2 = PCBPoint(self, self.X2, self.Y2)
        self.line = PCBLine(self, self.p1, self.p2)


class PCBElementArc(PCBElementBase):
    def __init__(self, tokens):
        super(PCBElementArc, self).__init__(tokens)
        # TODO handle arcs in cartesian
        # TODO Sort out relative locations
        self.center = PCBPoint(self, self.X, self.Y)


class PCBPin(PCBElementBase):
    def __init__(self, tokens):
        super(PCBPin, self).__init__(tokens)
        # TODO Sort out relative locations
        self.center = PCBPoint(self, self.rX, self.rY)


class PCBPad(PCBElementBase):
    def __init__(self, tokens):
        super(PCBPad, self).__init__(tokens)
        # TODO Sort out relative locations
        self.p1 = PCBPoint(self, self.rX1, self.rY1)
        self.p2 = PCBPoint(self, self.rX2, self.rY2)
        self.line = PCBLine(self, self.p1, self.p2)


class PCBElement(PCBElementBase):
    def __init__(self, tokens):
        super(PCBElement, self).__init__(tokens)
        # TODO Sort out relative locations
        self.origin = PCBPoint(self, self.MX, self.MY)
        self.text_origin = PCBPoint(self, self.TX, self.TY)
        if 'Content' in dir(self):
            self.content = [l[0] for l in self.Content]
            for line in self.content:
                try:
                    line.parent = self
                except AttributeError, e:
                    print line
                    raise e


class PCBConnect(PCBElementBase):
    def __init__(self, tokens):
        super(PCBConnect, self).__init__(tokens)


class PCBNet(PCBElementBase):
    def __init__(self, tokens):
        super(PCBNet, self).__init__(tokens)
        if 'Content' in dir(self):
            self.connects = [l[0] for l in self.Content]
            for line in self.connects:
                line.parent = self


class PCBNetList(PCBElementBase):
    def __init__(self, tokens):
        super(PCBNetList, self).__init__(tokens)
        if 'Content' in dir(self):
            self.nets = [l[0] for l in self.Content]
            for line in self.nets:
                line.parent = self


class PCBVia(PCBElementBase):
    def __init__(self, tokens):
        super(PCBVia, self).__init__(tokens)
        self.center = PCBPoint(self, self.X, self.Y)


class PCBGrid(object):
    def __init__(self, step, offset_x, offset_y, visible):
        self._step = step
        self._offsetX = offset_x
        self._offsetY = offset_y
        self._visible = visible


class PCBDRC(object):
    def __init__(self, bloat, shrink, drill, line, silk, ring):
        self._bloat = bloat
        self._shrink = shrink
        self._drill = drill
        self._line = line
        self._silk = silk
        self._ring = ring


class PCBStyles(list):
    def __init__(self, string):
        meas = pyparsing.Regex(r"-?[0-9\\.]+[a-z]*")
        meas.addParseAction(length)
        name = pyparsing.Word(pyparsing.alphas)
        comma = pyparsing.Suppress(pyparsing.Literal(','))
        style = pyparsing.Group(name('name') + comma + meas('thickness') + comma + meas('diameter') +
                                comma + meas('drill') + comma + meas('keepaway'))
        style.setResultsName('Style', True)
        styles = pyparsing.delimitedList(style, delim=':')
        stylelist = styles.parseString(string)
        super(PCBStyles, self).__init__(stylelist)


class PCBFile(object):
    def __init__(self, tokens=None):
        # Unhandled
        self.comments = []
        self.mark = []
        self.cursor = []
        self.rats = []

        # Object Hierarchy
        self.vias = []
        self.symbols = []
        self.elements = []
        self.attributes = []
        self.layers = []
        self.netlist = None

        # Embedded Here
        self._fileversion = None
        self._pcb_width = None
        self._pcb_height = None
        self._grid = None
        self._polyarea = None
        self._thermalscale = None
        self._drc = None
        self._flags = None
        self._groups = None
        self._styles = None

        if tokens is not None:
            self._load_from_pptokens(tokens)

    def _load_from_pptokens(self, tokens):
        self._pptokens = tokens.Content
        for line in self._pptokens:
            if isinstance(line[0], PCBVia):
                line[0].parent = self
                self.vias.append(line[0])
            elif isinstance(line[0], PCBSymbol):
                line[0].parent = self
                self.symbols.append(line[0])
            elif isinstance(line[0], PCBElement):
                line[0].parent = self
                self.elements.append(line[0])
            elif isinstance(line[0], PCBAttribute):
                line[0].parent = self
                self.attributes.append(line[0])
            elif isinstance(line[0], PCBLayer):
                line[0].parent = self
                self.layers.append(line[0])
            elif isinstance(line[0], PCBNetList):
                line[0].parent = self
                if self.netlist is not None:
                    logger.warning("UNEXPECTED :: NetList Redefined")
                self.netlist = line[0]
            elif line[0] == "#":
                self.comments.append(line)
            elif line[0] == "FileVersion":
                if self._fileversion is not None:
                    logger.warning("UNEXPECTED :: FileVersion Redefined")
                self._fileversion = line.Version
            elif line[0] == "PCB":
                if self._pcb_width is not None:
                    logger.warning("UNEXPECTED :: PCB Size Redefined")
                self._pcb_width = line.Width
                self._pcb_height = line.Height
            elif line[0] == "Grid":
                if self._grid is not None:
                    logger.warning("UNEXPECTED :: Grid Redefined")
                self._grid = PCBGrid(line.Step, line.OffsetX, line.OffsetY, line.Visible)
            elif line[0] == "PolyArea":
                if self._polyarea is not None:
                    logger.warning("UNEXPECTED :: Polyarea Redefined")
                self._polyarea = line.Area
            elif line[0] == "Thermal":
                if self._thermalscale is not None:
                    logger.warning("UNEXPECTED :: Thermal Scale Redefined")
                self._thermalscale = line.Scale
            elif line[0] == "DRC":
                if self._drc is not None:
                    logger.warning("UNEXPECTED :: DRC Redefined")
                self._drc = PCBDRC(line.Bloat, line.Shrink, line.Drill, line.Line, line.Silk, line.Ring)
            elif line[0] == "Flags":
                if self._flags is not None:
                    logger.warning("UNEXPECTED :: Flags Redefined")
                self._flags = line.Flags
            elif line[0] == "Groups":
                if self._groups is not None:
                    logger.warning("UNEXPECTED :: Groups Redefined")
                self._groups = line.Groups
            elif line[0] == "Styles":
                if self._styles is not None:
                    logger.warning("UNEXPECTED :: Styles Redefined")
                self._styles = PCBStyles(line.Styles)
            elif line[0] == "Mark":
                self.mark.append(line)
            elif line[0] == "Cursor":
                self.cursor.append(line)
            elif line[0] == "Rat":
                self.rats.append(line)
            else:
                print line[0]


class StringFlags(object):
    """
        From :
        PCB file parser written by Lilith Byrant 2014
        http://pastebin.com/2TqbDfKf
        GPLv2
    """
    L = pyparsing.Literal("(").suppress()
    R = pyparsing.Literal(")").suppress()
    PartStart = pyparsing.Regex(r"[^,\(\)]*")
    CSV = pyparsing.delimitedList(PartStart)
    Part = pyparsing.Group(PartStart + pyparsing.Group(pyparsing.Optional(L + CSV + R)))
    Parts = pyparsing.delimitedList(Part)

    def __init__(self, s):
        self.s = s
        all_flags = StringFlags.Parts.parseString(s)
        self.flags = set([PP[0] for PP in all_flags if PP[0] != "thermal"])
        thermal_flags = [PP for PP in all_flags if PP[0] == "thermal"]
        if len(thermal_flags) == 0:
            self.thermals = {}
        else:
            t = set(thermal_flags[0][1])
            self.thermals = dict([(i[0], (i+"!")[1]) for i in t])

    def __contains__(self, s):
        if s == "thermal":
            return len(self.thermals) > 0
        else:
            return s in self.flags

    def add(self, s):
        self.flags.add(s)

    def remove(self, s):
        if s in self.flags:
            self.flags.remove(s)

    def add_thermal(self, n, ttype):
        self.thermals[n] = ttype

    def remove_thermal(self, n):
        if n in self.thermals:
            del self.thermals[n]

    def remove_all_thermal(self):
        self.thermals = {}

    def __str__(self):
        if self.thermals is not None and len(self.thermals) > 0:
            s = [str(i[0])+(str(i[1]).replace("!", "")) for i in self.thermals.items()]
            t = "thermal("+",".join(sorted(s))+")"
            return ",".join(list(self.flags) + [t])
        else:
            return ",".join(self.flags)

    def __repr__(self):
        return self.__str__()


def length(s, loc, toks):
    if toks is not None and len(toks):
        try:
            toks = [Length(lstr=token, defunit='cmil') for token in toks]
        except Exception, e:
            print "Exception : ", loc, toks
            raise e
        return toks
    else:
        print s


def introspect(s, loc, toks):
    if toks is not None:
        print toks


def build_bnf(pp=pyparsing):
    """
        From :
        PCB file parser written by Lilith Byrant 2014
        http://pastebin.com/2TqbDfKf
        GPLv2
    """
    S = pp.Suppress
    C = pp.Combine
    G = pp.Group

    LRND = S(pp.Literal("("))
    RRND = S(pp.Literal(")"))
    LSQ = S(pp.Literal("["))
    RSQ = S(pp.Literal("]"))

    Str = pp.QuotedString('"')
    Char = pp.Regex(r"'.'")

    Meas = pp.Regex(r"-?[0-9\\.]+[a-z]*")
    Meas.addParseAction(length)

    Digits = pp.Regex(r"-?[0-9]+")
    Digits.setParseAction(lambda t: int(t[0]))

    Float = pp.Regex(r"-?[0-9\\.]+")
    Float.setParseAction(lambda t: float(t[0]))

    Comment = pp.Literal('#') + pp.restOfLine

    SFlags = C(Str)
    SFlags.setParseAction(lambda t: StringFlags(t[0]))

    QSFlags = SFlags

    FileVersion = pp.Keyword("FileVersion") + LSQ + Digits("Version") + RSQ

    PCB = pp.Keyword("PCB") + LSQ + (Str("Name") + Meas("Width") + Meas("Height"))("PCB") + RSQ
    Grid = pp.Keyword("Grid") + LSQ+Meas("Step") + Meas("OffsetX") + Meas("OffsetY") + Digits("Visible") + RSQ
    PolyArea = pp.Keyword("PolyArea") + LSQ+Float("Area") + RSQ
    Thermal = pp.Keyword("Thermal") + LSQ+Float("Scale") + RSQ
    DRC = pp.Keyword("DRC") + LSQ + Meas("Bloat") + Meas("Shrink") + \
        Meas("Line") + Meas("Silk") + Meas("Drill") + Meas("Ring") + RSQ
    Flags = pp.Keyword("Flags") + LRND + QSFlags("Flags") + RRND
    Groups = pp.Keyword("Groups") + LRND + Str("Groups") + RRND
    Styles = pp.Keyword("Styles") + LSQ + Str("Styles") + RSQ
    Mark = pp.Keyword("Mark") + LSQ + Meas("X")+Meas("Y") + RSQ
    Cursor = pp.Keyword("Cursor") + LSQ + Meas("X") + Meas("Y") + Float("Zoom") + RSQ

    PCBAttributep = pp.Keyword("Attribute") + LRND + Str("AttrKey") + Str("AttrValue") + RRND
    PCBAttributep.addParseAction(PCBAttribute)

    SymbolLine = pp.Keyword("SymbolLine") + LSQ + Meas("X1") + Meas("Y1") + \
        Meas("X2") + Meas("Y2") + Meas("Thickness") + RSQ
    SymbolLine.addParseAction(PCBSymbolLine)
    SymContent2 = SymbolLine
    SymContent = G(SymContent2)
    SymContent = SymContent.setResultsName("Content", True)

    PCBSymbolp = pp.Keyword("Symbol") + LSQ + Char("Char") + Meas("Delta") + RSQ + \
        LRND + pp.ZeroOrMore(SymContent) + RRND
    PCBSymbolp.addParseAction(PCBSymbol)

    Via = pp.Keyword("Via") + LSQ + Meas("X") + Meas("Y") + Meas("Thickness") + \
        Meas("Clearance") + Meas("Mask") + Meas("Drill") + Str("Name") + QSFlags("SFlags") + RSQ
    Via.addParseAction(PCBVia)
    Pin = pp.Keyword("Pin") + LSQ + Meas("rX") + Meas("rY") + Meas("Thickness") + \
        Meas("Clearance") + Meas("Mask") + Meas("Drill") + Str("Name") + Str("Number") + QSFlags("SFlags") + RSQ
    Pin.addParseAction(PCBPin)
    Pad = pp.Keyword("Pad") + LSQ + Meas("rX1") + Meas("rY1") + Meas("rX2") + Meas("rY2") + Meas("Thickness") + \
        Meas("Clearance") + Meas("Mask") + Str("Name") + Str("Number") + QSFlags("SFlags") + RSQ
    Pad.addParseAction(PCBPad)

    ElementArc = pp.Keyword("ElementArc") + LSQ + Meas("X") + Meas("Y") + Meas("Width") + Meas("Height") + \
        Digits("StartAngle") + Digits("DeltaAngle") + Meas("Thickness") + RSQ
    ElementArc.addParseAction(PCBElementArc)
    ElementLine = pp.Keyword("ElementLine") + LSQ + Meas("X1") + Meas("Y1") + Meas("X2") + Meas("Y2") + \
        Meas("Thickness") + RSQ
    ElementLine.addParseAction(PCBElementLine)

    ElemContent2 = PCBAttributep | Pin | Pad | ElementLine | ElementArc
    ElemContent = G(ElemContent2)
    ElemContent = ElemContent.setResultsName("Content", True)

    PCBElementp = (pp.Keyword("Element") + LSQ + QSFlags("SFlags") + Str("Desc") + Str("Name") + Str("Value") +
                  Meas("MX") + Meas("MY") + Meas("TX") + Meas("TY") + Digits("TDir") + Digits("TScale") +
                  QSFlags("TSFlags") + RSQ + LRND + pp.ZeroOrMore(ElemContent) + RRND)
    PCBElementp.addParseAction(PCBElement)

    Rat = pp.Keyword("Rat") + LSQ + Meas("X1") + Meas("Y1") + Digits("Group1") + Meas("X2") + Meas("Y2") + \
        Digits("Group2") + QSFlags("SFlags") + RSQ
    Line = pp.Keyword("Line") + LSQ + Meas("X1") + Meas("Y1") + Meas("X2") + Meas("Y2") + Meas("Thickness") + \
        Meas("Clearance") + QSFlags("SFlags") + RSQ
    Line.addParseAction(PCBLayerLine)
    Arc = pp.Keyword("Arc") + LSQ + Meas("X") + Meas("Y") + Meas("Width") + Meas("Height") + Meas("Thickness") + \
        Meas("Clearance") + Digits("StartAngle") + Digits("DeltaAngle") + QSFlags("SFlags") + RSQ
    Arc.addParseAction(PCBLayerArc)
    Text = pp.Keyword("Text") + LSQ + Meas("X") + Meas("Y") + Digits("Direction") + Meas("Scale") + Str("String") + \
        QSFlags("SFlags") + RSQ
    Text.addParseAction(PCBLayerText)

    PolyVertex = LSQ + Meas("X") + Meas("Y") + RSQ
    PolyVertex.addParseAction(PCBLayerPolygonVertex)
    PolyVertex = PolyVertex.setResultsName("Vertex", True)

    Hole = pp.Keyword("Hole") + LRND + pp.ZeroOrMore(PolyVertex) + RRND
    Hole.addParseAction(PCBLayerPolygonHole)

    PolyContent2 = PolyVertex | Hole
    PolyContent = G(PolyContent2)
    PolyContent = PolyContent.setResultsName("Content", True)

    Polygon = pp.Keyword("Polygon") + LRND + QSFlags("SFlags") + RRND + LRND + pp.ZeroOrMore(PolyContent) + RRND
    Polygon.addParseAction(PCBLayerPolygon)

    LayerContent2 = PCBAttributep | Line | Arc | Polygon | Text
    LayerContent = G(LayerContent2)
    LayerContent = LayerContent.setResultsName("Content", True)

    Layer = pp.Keyword("Layer") + LRND + Digits("LayerNum") + Str("Name") + RRND + \
        LRND + pp.ZeroOrMore(LayerContent) + RRND
    Layer.addParseAction(PCBLayer)

    Connect = pp.Keyword("Connect") + LRND + Str("PinPad") + RRND
    Connect.addParseAction(PCBConnect)
    Connect = Connect.setResultsName("Connect", True)
    Connects = G(Connect)
    Connects.setResultsName("Content", True)

    Net = pp.Keyword("Net") + LRND + Str("Name") + Str("Style") + RRND + \
        LRND + pp.ZeroOrMore(Connects)("Content") + RRND
    Net.addParseAction(PCBNet)
    Net = Net.setResultsName("Net", True)
    Nets = G(Net)
    Nets.setResultsName("Content", True)

    NetList = pp.Keyword("NetList") + LRND + RRND + \
        LRND + pp.ZeroOrMore(Nets)("Content") + RRND
    NetList.addParseAction(PCBNetList)

    TopLevelThing2 = Comment | FileVersion | PCB | Grid | PolyArea | Thermal | DRC | Flags | Groups | Styles | \
        Mark | Cursor | PCBSymbolp | PCBAttributep | Via | PCBElementp | Rat | Layer | NetList

    TopLevelThing = G(TopLevelThing2)
    TopLevelThing = TopLevelThing.setResultsName("Content", True)

    FileGrammar = pp.ZeroOrMore(TopLevelThing)
    FileGrammar.addParseAction(PCBFile)

    return FileGrammar


def conv_pcb2pdf(pcbpath, docfolder, projname):
    pcb_folder, pcb_file = os.path.split(pcbpath)
    psfile = os.path.join(docfolder, projname + '-pcb.ps')
    subprocess.call(['pcb', '-x', 'ps',
                     '--psfile', psfile,
                     '--outline', '--media', 'A4', '--show-legend',
                     pcb_file], cwd=pcb_folder)
    pdffile = os.path.join(docfolder, projname + '-pcb.pdf')
    tendril.utils.pdf.conv_ps2pdf(psfile, pdffile)
    os.remove(psfile)
    return pdffile


def conv_pcb2gbr(pcbpath):
    pcb_folder, pcb_file = os.path.split(pcbpath)
    gbrfile = os.path.join(os.path.join(pcb_folder, os.pardir), 'gerber', os.path.splitext(pcb_file)[0])
    subprocess.call(['pcb', '-x', 'gerber',
                     '--gerberfile', gbrfile,
                     '--all-layers', '--verbose', '--outline',
                     pcb_file], cwd=pcb_folder)
    return os.path.join(os.path.join(pcb_folder, os.pardir), 'gerber')


def conv_pcb2dxf(pcbpath, pcbname):
    pcb_folder, pcb_file = os.path.split(pcbpath)
    dxffile = os.path.splitext(pcbpath)[0] + '.dxf'
    psfile = os.path.splitext(pcbpath)[0] + '.ps'
    subprocess.call(['pcb', '-x', 'ps',
                     '--psfile', psfile,
                     '--media', 'A4', '--show-legend', '--multi-file',
                     pcb_file], cwd=pcb_folder)
    psfile = os.path.splitext(pcbpath)[0] + '.top.ps'
    subprocess.call(['pstoedit', '-f', 'dxf', psfile, dxffile])
    cleanlist = [f for f in os.listdir(pcb_folder) if f.endswith(".ps")]
    for f in cleanlist:
        os.remove(os.path.join(pcb_folder, f))
    return dxffile
