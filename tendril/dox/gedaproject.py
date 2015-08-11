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
gEDA Project Dox module documentation (:mod:`dox.gedaproject`)
==============================================================
"""
from tendril.utils import log
logger = log.get_logger(__name__, log.DEFAULT)

import os
import csv
import yaml
import glob
import shutil

from tendril.gedaif import gschem
from tendril.gedaif import conffile
from tendril.gedaif import projfile
from tendril.gedaif import pcb

from tendril.utils import pdf
from tendril.utils import fs

from tendril.entityhub import projects
from tendril.boms import electronics as boms_electronics
from tendril.boms import outputbase as boms_outputbase

import render


def gen_confbom(projfolder, configname):
    gpf = projfile.GedaProjectFile(projfolder)
    sch_mtime = fs.get_folder_mtime(gpf.schfolder)

    docfolder = projects.get_project_doc_folder(projfolder)
    outpath = os.path.join(docfolder, 'confdocs', configname + '-bom.pdf')
    outf_mtime = fs.get_file_mtime(outpath)

    if outf_mtime is not None and outf_mtime > sch_mtime:
        logger.debug('Skipping up-to-date ' + outpath)
        return outpath

    logger.info('Regenerating ' + outpath + os.linesep +
                'Last modified : ' + str(sch_mtime) + '; Last Created : ' + str(outf_mtime))
    bom = boms_electronics.import_pcb(projfolder)
    obom = bom.create_output_bom(configname)

    stage = {'configname': obom.descriptor.configname,
             'pcbname': obom.descriptor.pcbname,
             'lines': obom.lines}
    for config in obom.descriptor.configurations.configurations:
        if config['configname'] == configname:
            stage['desc'] = config['desc']

    template = 'geda-bom-simple.tex'

    render.render_pdf(stage, template, outpath)
    return outpath


def gen_configdoc(projfolder, namebase):
    pass


def gen_schpdf(projfolder, namebase):
    gpf = projfile.GedaProjectFile(projfolder)
    sch_mtime = fs.get_folder_mtime(gpf.schfolder)

    configfile = conffile.ConfigsFile(projfolder)
    docfolder = projects.get_project_doc_folder(projfolder)

    schpdfpath = os.path.join(docfolder, namebase + '-schematic.pdf')
    outf_mtime = fs.get_file_mtime(schpdfpath)

    if outf_mtime is not None and outf_mtime > sch_mtime:
        logger.debug('Skipping up-to-date ' + schpdfpath)
        return schpdfpath

    logger.info('Regenerating ' + schpdfpath + os.linesep +
                'Last modified : ' + str(sch_mtime) + '; Last Created : ' + str(outf_mtime))

    if configfile.configdata is not None:
        pdffiles = []
        for schematic in gpf.schfiles:
            schfile = os.path.normpath(projfolder + '/schematic/' + schematic)
            pdffile = gschem.conv_gsch2pdf(schfile, docfolder)
            pdffiles.append(pdffile)
        pdf.merge_pdf(pdffiles, schpdfpath)
        for pdffile in pdffiles:
            os.remove(pdffile)
        return schpdfpath


def gen_masterdoc(projfolder, namebase):
    gpf = projfile.GedaProjectFile(projfolder)
    sch_mtime = fs.get_folder_mtime(gpf.schfolder)

    docfolder = projects.get_project_doc_folder(projfolder)
    masterdocfile = os.path.join(docfolder, namebase + '-masterdoc.pdf')
    outf_mtime = fs.get_file_mtime(masterdocfile)

    if outf_mtime is not None and outf_mtime > sch_mtime:
        logger.debug('Skipping up-to-date ' + masterdocfile)
        return masterdocfile

    logger.info('Regnerating ' + masterdocfile + os.linesep +
                'Last modified : ' + str(sch_mtime) + '; Last Created : ' + str(outf_mtime))

    pdffiles = [gen_configdoc(projfolder, namebase),
                gen_schpdf(projfolder, namebase)]

    pdf.merge_pdf(pdffiles, masterdocfile)
    return masterdocfile


def gen_confpdf(projfolder, configname, namebase):
    gpf = projfile.GedaProjectFile(projfolder)
    sch_mtime = fs.get_folder_mtime(gpf.schfolder)

    docfolder = projects.get_project_doc_folder(projfolder)
    confdocfile = os.path.join(docfolder, 'confdocs', configname + '-doc.pdf')
    outf_mtime = fs.get_file_mtime(confdocfile)

    if outf_mtime is not None and outf_mtime > sch_mtime:
        logger.debug('Skipping up-to-date ' + confdocfile)
        return confdocfile

    logger.info('Regenerating ' + confdocfile + os.linesep +
                'Last modified : ' + str(sch_mtime) + '; Last Created : ' + str(outf_mtime))

    pdffiles = [gen_confbom(projfolder, configname),
                gen_schpdf(projfolder, namebase)]
    pdf.merge_pdf(pdffiles, confdocfile)
    return confdocfile


def gen_cobom_csv(projfolder, namebase):
    gpf = projfile.GedaProjectFile(projfolder)
    configfile = conffile.ConfigsFile(projfolder)
    sch_mtime = fs.get_folder_mtime(gpf.schfolder)

    docfolder = projects.get_project_doc_folder(projfolder)
    cobom_csv_path = os.path.join(docfolder, 'confdocs', 'conf-boms.csv')
    outf_mtime = fs.get_file_mtime(cobom_csv_path)

    if outf_mtime is not None and outf_mtime > sch_mtime:
        logger.debug('Skipping up-to-date ' + cobom_csv_path)
        return cobom_csv_path

    logger.info('Regenerating ' + cobom_csv_path + os.linesep +
                'Last modified : ' + str(sch_mtime) + '; Last Created : ' + str(outf_mtime))

    bomlist = []
    for cfn in configfile.configdata['configurations']:
        gen_confpdf(projfolder, cfn['configname'], namebase)
        lbom = boms_electronics.import_pcb(projfolder)
        lobom = lbom.create_output_bom(cfn['configname'])
        bomlist.append(lobom)
    cobom = boms_outputbase.CompositeOutputBom(bomlist)

    with open(cobom_csv_path, 'w') as f:
        writer = csv.writer(f)
        writer.writerow(['device'] + [x.configname for x in cobom.descriptors])
        for line in cobom.lines:
            writer.writerow([line.ident] + line.columns)


def gen_pcb_pdf(projfolder):
    configfile = conffile.ConfigsFile(projfolder)
    gpf = projfile.GedaProjectFile(configfile.projectfolder)
    pcb_mtime = fs.get_file_mtime(os.path.join(configfile.projectfolder, 'pcb', gpf.pcbfile + '.pcb'))
    docfolder = projects.get_project_doc_folder(projfolder)
    pdffile = os.path.join(docfolder, configfile.configdata['pcbname'] + '-pcb.pdf')
    outf_mtime = fs.get_file_mtime(pdffile)

    if outf_mtime is not None and outf_mtime > pcb_mtime:
        logger.debug('Skipping up-to-date ' + pdffile)
        return pdffile

    logger.info('Regenerating ' + pdffile + os.linesep +
                'Last modified : ' + str(pcb_mtime) + '; Last Created : ' + str(outf_mtime))

    pdffile = pcb.conv_pcb2pdf(os.path.join(configfile.projectfolder, 'pcb', gpf.pcbfile + '.pcb'),
                               docfolder, configfile.configdata['pcbname'])
    return pdffile


def gen_pcb_gbr(projfolder):
    configfile = conffile.ConfigsFile(projfolder)
    gpf = projfile.GedaProjectFile(configfile.projectfolder)
    pcb_mtime = fs.get_file_mtime(os.path.join(configfile.projectfolder, 'pcb', gpf.pcbfile + '.pcb'))
    gbrfolder = os.path.join(configfile.projectfolder, 'gerber')
    outf_mtime = None
    if not os.path.exists(gbrfolder):
        os.makedirs(gbrfolder)
    else:
        outf_mtime = fs.get_folder_mtime(gbrfolder)

    if outf_mtime is not None and outf_mtime > pcb_mtime:
        logger.debug('Skipping up-to-date ' + gbrfolder)
        return gbrfolder

    logger.info('Regenerating ' + gbrfolder + os.linesep +
                'Last modified : ' + str(pcb_mtime) + '; Last Created : ' + str(outf_mtime))
    glb = os.path.join(configfile.projectfolder, 'gerber', '*')
    rf = glob.glob(glb)
    for f in rf:
        os.remove(f)
    gbrfolder = pcb.conv_pcb2gbr(os.path.join(configfile.projectfolder, 'pcb', gpf.pcbfile + '.pcb'))
    zfile = os.path.join(projfolder, gpf.pcbfile + '-gerber.zip')
    fs.zipdir(gbrfolder, zfile)
    return gbrfolder


def gen_pcb_dxf(projfolder):
    configfile = conffile.ConfigsFile(projfolder)
    gpf = projfile.GedaProjectFile(configfile.projectfolder)
    pcb_mtime = fs.get_file_mtime(os.path.join(configfile.projectfolder, 'pcb', gpf.pcbfile + '.pcb'))
    dxffile = os.path.join(configfile.projectfolder, 'pcb', gpf.pcbfile + '.dxf')
    outf_mtime = fs.get_file_mtime(dxffile)

    if outf_mtime is not None and outf_mtime > pcb_mtime:
        logger.debug('Skipping up-to-date ' + dxffile)
        return dxffile

    logger.info('Regenerating ' + dxffile + os.linesep +
                'Last modified : ' + str(pcb_mtime) + '; Last Created : ' + str(outf_mtime))
    dxffile = pcb.conv_pcb2dxf(os.path.join(configfile.projectfolder, 'pcb', gpf.pcbfile + '.pcb'),
                               configfile.configdata['pcbname'])
    return dxffile


def gen_pcbpricing(projfolder, namebase):
    gpf = projfile.GedaProjectFile(projfolder)
    pcbpricingfp = os.path.join(gpf.configsfile.projectfolder, 'pcb', 'sourcing.yaml')
    pcbpricing_mtime = fs.get_file_mtime(pcbpricingfp)

    if not os.path.exists(pcbpricingfp):
        return None

    docfolder = projects.get_project_doc_folder(projfolder)
    plotfile = os.path.join(docfolder, namebase + '-pricing.pdf')
    outf_mtime = fs.get_file_mtime(plotfile)

    if outf_mtime is not None and outf_mtime > pcbpricing_mtime:
        logger.debug('Skipping up-to-date ' + pcbpricingfp)
        return pcbpricingfp

    logger.info('Regnerating ' + plotfile + os.linesep +
                'Last modified : ' + str(pcbpricing_mtime) + '; Last Created : ' + str(outf_mtime))

    with open(pcbpricingfp, 'r') as f:
        data = yaml.load(f)

    plot1file = os.path.join(docfolder, namebase + '-1pricing.pdf')
    plot2file = os.path.join(docfolder, namebase + '-2pricing.pdf')

    pltnote = "This pricing refers to the bare PCB only. See the corresponding Config Docs for Card Pricing"

    plt1data = {key: data['pricing'][key] for key in data['pricing'].keys() if key <= 10}
    plt1title = gpf.configsfile.configdata['pcbname'] + " PCB Unit Price vs Order Quantity (Low Quantity)"
    plot1file = render.render_lineplot(plot1file, plt1data, plt1title, pltnote)

    if max(data['pricing'].keys()) > 10:
        plt2data = {key: data['pricing'][key] for key in data['pricing'].keys() if key > 10}
        plt2title = gpf.configsfile.configdata['pcbname'] + " PCB Unit Price vs Order Quantity (Production Quantity)"
        plot2file = render.render_lineplot(plot2file, plt2data, plt2title, pltnote)
        pdf.merge_pdf([plot1file, plot2file], plotfile)
        os.remove(plot2file)
    else:
        shutil.copyfile(plot1file, plotfile)
    os.remove(plot1file)

    return pcbpricingfp


def generate_docs(projfolder):
    configfile = conffile.ConfigsFile(projfolder)
    namebase = configfile.configdata['pcbname']
    if namebase is None:
        try:
            namebase = configfile.configdata['cblname']
        except KeyError:
            logger.error("Project does not have a known identifier. Skipping : " + projfolder)
            return
    gen_masterdoc(projfolder, namebase)
    gen_cobom_csv(projfolder, namebase)
    if configfile.configdata['pcbname'] is not None:
        gen_pcb_pdf(projfolder)
        gen_pcb_gbr(projfolder)
        gen_pcb_dxf(projfolder)
        gen_pcbpricing(projfolder, namebase)


if __name__ == "__main__":
    pass
