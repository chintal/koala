#!/usr/bin/env python
# encoding: utf-8

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
Electronic Boms Module documentation (:mod:`boms.electronics`)
==============================================================

This module contains various classes for handling structured data present in
elctronics BOMs. The module is built for use with gEDA with specific additions
and/or constraints to the standard gEDA project structure. Use with other EDA
tools should be possible by replacing ``gedaif`` with an EDA tool specific
package.

Module Summary:
---------------

.. autosummary::
    EntityBase
    EntityElnComp
    EntityGroup
    import_pcb

Module Members:
---------------

"""

from tendril.utils import log
logger = log.get_logger(__name__, log.INFO)

import os
import copy

import tendril.gedaif.bomparser
import tendril.gedaif.conffile
import tendril.conventions.electronics

from outputbase import OutputElnBomDescriptor
from outputbase import OutputBom

from entitybase import EntityBase
from entitybase import EntityGroupBase
from entitybase import EntityBomBase


class EntityElnComp(EntityBase):
    """Object containing a single electronic component.

        Accept a ``gedaif.bomparser.BomLine`` generated through gnetlist's
        ``bom`` backend. The ``attribs`` file should atleast contain:
        * device
        * value
        * footprint
        * fillstatus

        :param item: BomLine containing details of component to be created
        :type item: gedaif.bomparser.BomLine

    """
    def __init__(self, item=None):
        super(EntityElnComp, self).__init__()
        self._device = ""
        self._value = ""
        self._footprint = ""
        self._fillstatus = ""

        if item is not None:
            self.define(item.data['refdes'], item.data['device'],
                        item.data['value'], item.data['footprint'],
                        item.data['fillstatus'])

    def define(self, refdes, device, value, footprint="", fillstatus=""):
        """
        Define the component.

        Can be used directly for special cases when there is no
        `tendril.gedaif.bomparser.BomLine` to pass to the class `__init__`
        function.

        :param refdes: Refdes string.
        :param device: Device string.
        :param value: Value string.
        :param footprint: Footprint string. Optional.
        :param fillstatus: Fillstatus string. Optional.
        """
        self.refdes = refdes
        self.device = device
        self.value = value
        self.footprint = footprint
        self.fillstatus = fillstatus
        self._defined = True

    @property
    def fillstatus(self):
        """ Fillstatus string.
        When ``fillstatus`` is ``DNP``, the component is not included in BOMs
        irrespective of other configuration states.
        """
        return self._fillstatus

    @fillstatus.setter
    def fillstatus(self, value):
        if value == 'DNP':
            self._fillstatus = 'DNP'
        elif value in ['unknown', '']:
            self._fillstatus = ''
        elif value == 'CONF':
            self._fillstatus = 'CONF'
        else:
            logger.warning("Unsupported fillstatus: " + value)

    @property
    def ident(self):
        return tendril.conventions.electronics.ident_transform(self.device,
                                                             self.value,
                                                             self.footprint)

    @property
    def device(self):
        """ Component device string. """
        return self._device

    @device.setter
    def device(self, value):
        self._device = value

    @property
    def value(self):
        """ Component value string. """
        return self._value

    @value.setter
    def value(self, value):
        self._value = value

    @property
    def footprint(self):
        """
        Component footprint string. ``MY-`` at the beginning of the footprint
        string is stripped away automatically.
        """
        return self._footprint

    @footprint.setter
    def footprint(self, value):
        if value is None:
            return
        if value[0:3] == "MY-":
            self._footprint = value[3:]
        else:
            self._footprint = value


class EntityElnGroup(EntityGroupBase):
    """ Container for a group of EntityElnComp objects.

        :ivar groupname: Name of the group
        :ivar eln_comp_list: List of EntityElnComp objects

    """
    def __init__(self, groupname, contextname):
        super(EntityElnGroup, self).__init__(groupname, contextname)
        pass

    def insert(self, item):
        """ Insert an electronic component into the EntityGroup.

        Accept a BomLine and generate an EntityElnComp to represent the
        component if it's ``fillstatus`` is not ``DNP``. Insert the created
        EntityElnComp object into the group.

        :param item: ``BomLine`` representing the item to insert.
        :type item: gedaif.bomparser.BomLine

        """
        if item.data['fillstatus'] != 'DNP':
            x = EntityElnComp(item)
            if x.defined:
                self.complist.append(x)

    def insert_eln_comp(self, comp):
        """ Insert a manually created component into the EntityGroup.

        This should be used for components not originating directly from
        gEDA's gnetlist output.

        :param comp: Existing component to insert
        :type comp: EntityElnComp
        """
        if comp.defined:
            self.complist.append(comp)


class EntityElnBomConf(object):
    def __init__(self, configdata):
        super(EntityElnBomConf, self).__init__()
        self.pcbname = configdata["pcbname"]
        self.grouplist = configdata["grouplist"]
        if "configsections" in configdata.keys():
            self.configsections = configdata["configsections"]
        else:
            self.configsections = None
        self.configurations = configdata["configurations"]
        if "motiflist" in configdata.keys():
            self.motiflist = configdata["motiflist"]
        else:
            self.motiflist = None
        if "sjlist" in configdata.keys():
            self.sjlist = configdata["sjlist"]
        else:
            self.sjlist = {}
        self.rawconfig = configdata

    def get_configurations(self):
        rval = []
        for configuration in self.configurations:
            rval.append(configuration["configname"])
        return rval
        pass

    def get_configsections(self):
        if self.configsections is None:
            raise AttributeError
        rval = []
        for configsection in self.configsections:
            rval.append(configsection["sectionname"])
        return rval

    def get_sec_groups(self, sectionname, config):
        rval = []
        for section in self.configsections:
            if section["sectionname"] == sectionname:
                for configuration in section["configurations"]:
                    if configuration["configname"] == config:
                        for group in configuration["groups"]:
                            if group is not None:
                                rval.append(group)
        return rval

    def get_configuration(self, configname):
        rval = ["default"]
        for configuration in self.configurations:
            if configuration["configname"] == configname:
                try:
                    for configsection in self.get_configsections():
                        sec_confname = configuration["config"][configsection]
                        rval = rval + self.get_sec_groups(configsection, sec_confname)
                except AttributeError:
                    rval = ["default"]
                    try:
                        for group in configuration["grouplist"]:
                            if group != "default":
                                rval = rval + [group]
                    except:
                        raise AttributeError
        return rval

    def get_configuration_motifs(self, configname):
        for configuration in self.configurations:
            if configuration["configname"] == configname:
                try:
                    return configuration["motiflist"]
                except KeyError:
                    logger.debug("Configuration missing motiflist : " + configname)
                    return None
        raise ValueError

    def get_configuration_gens(self, configname):
        for configuration in self.configurations:
            if configuration["configname"] == configname:
                try:
                    return configuration["genlist"]
                except KeyError:
                    logger.debug("Configuration missing genlist : " + configname)
                    return None
        raise ValueError

    def get_configuration_sjs(self, configname):
        if self.sjlist is not None:
            sjlist = copy.copy(self.sjlist)
        else:
            sjlist = None
        for configuration in self.configurations:
            if configuration['configname'] == configname:
                try:
                    if configuration['sjlist'] is not None:
                        sjlist.update(configuration['sjlist'])
                        return sjlist
                    return configuration['sjlist']
                except KeyError:
                    logger.debug("Configuration missing SJ list : " + configname)
                    return sjlist
        raise ValueError


class EntityElnBom(EntityBomBase):
    def __init__(self, configfile):
        """

        :type configfile: gedaif.conffile.ConfigsFile
        """
        super(EntityElnBom, self).__init__()
        self.pcbname = configfile.configdata["pcbname"]
        self.projfile = configfile.configdata["projfile"]
        self.projfolder = configfile.projectfolder

        self.configurations = EntityElnBomConf(configfile.configdata)
        self._motifs = []
        self.create_groups()
        self.populate_bom()

    def create_groups(self):
        groupnamelist = [x['name'] for x in self.configurations.grouplist]
        if 'default' not in groupnamelist:
            x = EntityElnGroup('default', self.pcbname)
            self.grouplist.append(x)
        for group in groupnamelist:
            logger.debug("Creating Group: " + str(group))
            x = EntityElnGroup(group, self.pcbname)
            self.grouplist.append(x)

    def find_tgroup(self, item):
        """

        :rtype : EntityElnGroup
        """
        groupname = item.data['group']
        if groupname == 'unknown':
            groupname = 'default'
        if groupname not in [x['name'] for x in self.configurations.grouplist]:
            logger.warning("Could not find group in config file : " + groupname)
            groupname = 'default'
        for group in self.grouplist:
            if group.groupname == groupname:
                return group

    def find_group(self, groupname):
        """

        :rtype : EntityElnGroup
        """
        for group in self.grouplist:
            if group.groupname == groupname:
                return group

    def populate_bom(self):
        if self.configurations.pcbname is not None:
            tgroup = self.find_group('default')
            comp = EntityElnComp()
            comp.define('PCB', 'PCB', self.configurations.pcbname)
            tgroup.insert_eln_comp(comp)
        parser = tendril.gedaif.bomparser.MotifAwareBomParser(self.projfolder, "bom")
        for item in parser.line_gen:
            if item.data['device'] == 'TESTPOINT':
                continue
            tgroup = self.find_tgroup(item)
            skip = False
            if item.data['footprint'] == 'MY-TO220':
                comp = EntityElnComp()
                comp.define('HS' + item.data['refdes'][1:], 'HEAT SINK', 'TO220')
                tgroup.insert_eln_comp(comp)
            if item.data['device'] == 'MODULE LCD' and \
                    item.data['value'] == "CHARACTER PARALLEL 16x2" and \
                    item.data['footprint'] == "MY-MTA100-16":
                comp = EntityElnComp()
                comp.define(item.data['refdes'], 'CONN SIP', "16PIN PM ST", "MY-MTA100-16")
                tgroup.insert_eln_comp(comp)
                skip = True
            if not skip:
                tgroup.insert(item)
        for item in parser.motif_gen:
            self._motifs.append(item)

    def get_motif_by_refdes(self, refdes):
        for motif in self._motifs:
            if refdes == motif.refdes:
                return motif
        return None

    def create_output_bom(self, configname):
        if configname not in self.configurations.get_configurations():
            raise ValueError
        outbomdescriptor = OutputElnBomDescriptor(self.pcbname, self.projfolder, configname, self.configurations)
        outbom = OutputBom(outbomdescriptor)
        outgroups = self.configurations.get_configuration(configname)

        genlist = self.configurations.get_configuration_gens(configname)

        gen_refdeslist = None
        if genlist is not None:
            gen_refdeslist = genlist.keys()

        sjlist = self.configurations.get_configuration_sjs(configname)
        sj_refdeslist = None
        if sjlist is not None:
            sj_refdeslist = sjlist.keys()

        for group in outgroups:
            grpobj = self.find_group(group)
            if grpobj is None:
                logger.critical("outgroups : " + str(outgroups))
                logger.critical("grpobj not found : " + str(group) + ":for " + configname)
            for comp in grpobj.complist:
                if gen_refdeslist is not None and comp.refdes in gen_refdeslist:
                    if tendril.conventions.electronics.fpiswire(comp.device):
                        comp.footprint = genlist[comp.refdes]
                    else:
                        comp.value = genlist[comp.refdes]
                if sj_refdeslist is not None and comp.refdes in sj_refdeslist:
                    if not comp.fillstatus == 'CONF':
                        logger.error("sjlist attempts to change not configurable SJ : " + comp.refdes)
                        raise AttributeError
                    if sjlist[comp.refdes]:
                        logger.debug("Setting Fillstatus : " + comp.refdes)
                        comp.fillstatus = ''
                    else:
                        logger.debug("Clearing Fillstatus : " + comp.refdes)
                        comp.fillstatus = 'DNP'
                outbom.insert_component(comp)

        motifconfs = self.configurations.get_configuration_motifs(configname)
        if motifconfs is None:
            outbom.sort_by_ident()
            return outbom

        for key, motifconf in motifconfs.iteritems():
            motif = self.get_motif_by_refdes(key)
            if motif is None:
                logger.error("Motif not defined : " + key)
                continue
            motifconf_act = motif.get_configdict_stub()
            if self.configurations.motiflist is not None:
                basemotifconfs = self.configurations.motiflist
                for bkey, baseconf in basemotifconfs.iteritems():
                    if bkey == key:
                        logger.debug("Found Base Configuration for : " + key)
                        motifconf_act.update(baseconf)
            motifconf_act.update(motifconf)
            motif.configure(motifconf_act)
            for item in motif.get_line_gen():
                if item.data['group'] in outgroups and item.data['fillstatus'] != 'DNP':
                    outbom.insert_component(EntityElnComp(item))

        outbom.sort_by_ident()
        return outbom


def import_pcb(cardfolder):
    """Import PCB and return a populated EntityBom

    Accept cardfolder as an argument and return a populated EntityBOM.
    The cardfolder should be the path to a PCB folder, containing the
    file structure described in ``somewhere``.

    .. seealso::
        - ``gedaif.projfile.GedaProjectFile``
        - ``gEDA Project Folder Structure``

    :param cardfolder: PCB folder (containing schematic, pcb, gerber)
    :type cardfolder: str
    :return: Populated EntityBom
    :rtype: EntityBom

    :Example:

    >>> import tendril.boms.electronics
    >>> bom = tendril.boms.electronics.import_pcb('path/to/cardfolder')

    """
    cardfolder = os.path.abspath(cardfolder)
    pcbbom = None
    configfile = tendril.gedaif.conffile.ConfigsFile(cardfolder)
    if configfile.configdata is not None:
        pcbbom = EntityElnBom(configfile)
    return pcbbom

if __name__ == "__main__":
    pass
