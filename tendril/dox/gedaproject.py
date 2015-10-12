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
gEDA Project Dox Module (:mod:`tendril.dox.gedaproject`)
========================================================

This module generates the standard documentation set for gEDA projects.

The functions here use the :mod:`tendril.dox.render` module to actually
produce the output files after constructing the appropriate stage.

Each document generator function in this module uses a predefined set of
source files (relative to the project folder), and the output files
generated by this module are put into predefined locations, with predefined
names. Each function specifies the paths it operates on.

``<project_doc_folder>`` is obtained from
:func:`get_project_doc_folder`

.. warning:: Unless otherwise specified in the function documentation, the
             functions of this module will not overwrite any target output
             files unless the pre-existing output files are older than the
             source files. Note that this means the output will not be
             regenerated if the template is changed. You should ``touch``
             one of the source files if you want to force a rebuild.

.. seealso:: :mod:`tendril.dox`, :mod:`tendril.gedaif`

.. rubric:: Document Set Generators

.. autosummary::

    generate_docs

.. rubric:: Document Generators

.. autosummary::

    gen_confbom
    gen_configdoc
    gen_schpdf
    gen_masterdoc
    gen_confpdf
    gen_cobom_csv
    gen_pcb_pdf
    gen_pcb_gbr
    gen_pcb_dxf
    gen_pcbpricing

"""

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
from tendril.utils import fsutils

from tendril.boms import electronics as boms_electronics
from tendril.boms import outputbase as boms_outputbase

import render
from fs import path
from fs.utils import copyfile
from fs.errors import PermissionDeniedError

from docstore import ExposedDocument
from docstore import refdoc_fs

from tendril.utils.config import PROJECTS_ROOT

from tendril.utils import log
from tendril.utils.fsutils import temp_fs

workspace_fs = temp_fs.makeopendir('workspace_gpd')
logger = log.get_logger(__name__, log.DEFAULT)


def get_project_doc_folder(projectfolder):
    projectfolder = os.path.realpath(projectfolder)
    projectfolder = os.path.relpath(projectfolder, PROJECTS_ROOT)
    pth = path.join(projectfolder, 'doc')
    try:
        if not refdoc_fs.exists(pth):
            refdoc_fs.makedir(pth, recursive=True)
        if not refdoc_fs.exists(path.join(pth, 'confdocs')):
            refdoc_fs.makedir(path.join(pth, 'confdocs'), recursive=True)
    except PermissionDeniedError:
        logger.warning(
            "Permission denied when creating folder for " + projectfolder
        )
        return None
    return pth


def gen_confbom(projfolder, configname, force=False):
    """
    Generates a PDF of the BOM for a specified configuration of a gEDA
    project.

    :param projfolder: The gEDA project folder
    :type projfolder: str
    :param configname: The configuration name for which the BOM should be
                       generated.
    :return: The output file path.

    .. rubric:: Paths

    * Output File :  ``<project_doc_folder>/confdocs/<configname>-bom.pdf``
    * Source Files : The project's schematic folder.

    .. rubric:: Template Used

    ``tendril/dox/templates/geda-bom-simple.tex``
    (:download:`Included version
    <../../tendril/dox/templates/geda-bom-simple.tex>`)

    .. rubric:: Stage Keys Provided
    .. list-table::

        * - ``configname``
          - The name of the configuration (a card or cable name).
        * - ``desc``
          - The description of the configuration.
        * - ``pcbname``
          - The name of the base PCB.
        * - ``lines``
          - A list of :mod:`tendril.boms.outputbase.OutputBomLine` instances

    """

    gpf = projfile.GedaProjectFile(projfolder)
    sch_mtime = fsutils.get_folder_mtime(gpf.schfolder)

    docfolder = get_project_doc_folder(projfolder)
    outpath = path.join(docfolder, 'confdocs', configname + '-bom.pdf')
    outf_mtime = fsutils.get_file_mtime(outpath, fs=refdoc_fs)

    if not force and outf_mtime is not None and outf_mtime > sch_mtime:
        logger.debug('Skipping up-to-date ' + outpath)
        return outpath

    logger.info('Regenerating ' + outpath + os.linesep +
                'Last modified : ' + str(sch_mtime) +
                '; Last Created : ' + str(outf_mtime))
    bom = boms_electronics.import_pcb(projfolder)
    obom = bom.create_output_bom(configname)

    stage = {'configname': obom.descriptor.configname,
             'pcbname': obom.descriptor.pcbname,
             'lines': obom.lines}
    for config in obom.descriptor.configurations.configurations:
        if config['configname'] == configname:
            stage['desc'] = config['desc']

    template = 'geda-bom-simple.tex'

    workspace_outpath = workspace_fs.getsyspath(outpath)
    workspace_fs.makedir(path.dirname(outpath),
                         recursive=True, allow_recreate=True)
    render.render_pdf(stage, template, workspace_outpath)
    copyfile(workspace_fs, outpath, refdoc_fs, outpath, overwrite=True)

    return outpath


def gen_configdoc(projfolder, namebase, force=False):
    """
    Generate a PDF documenting the configs of the project. The document should
    include a reasonably thorough representation of the contents of the
    configuration related sections of the
    ``tendril.gedaif.conffile.ConfigsFile``.

    .. todo:: Implement this.

    :param projfolder: The gEDA project folder.
    :type projfolder: str
    :param namebase: The project name.
    :type namebase: str
    :return: The output file path.

    .. rubric:: Paths

    * Output File :  ``<project_doc_folder>/<namebase>-configs.pdf``
    * Source Files : The project's schematic folder.

    """
    pass


def gen_schpdf(projfolder, namebase, force=False):
    """
    Generates a PDF file of all the project schematics listed in the
    gEDA project file. This function does not ise jinja2 and latex. It
    relies on :func:`tendril.gedaif.gschem.conv_gsch2pdf` instead.

    :param projfolder: The gEDA project folder.
    :type projfolder: str
    :param namebase: The project name.
    :type namebase: str
    :return: The output file path.

    .. rubric:: Paths

    * Output File :  ``<project_doc_folder>/<namebase>-schematic.pdf``
    * Source Files : The project's schematic folder.

    """
    gpf = projfile.GedaProjectFile(projfolder)
    sch_mtime = fsutils.get_folder_mtime(gpf.schfolder)

    configfile = conffile.ConfigsFile(projfolder)
    docfolder = get_project_doc_folder(projfolder)

    schpdfpath = path.join(docfolder, namebase + '-schematic.pdf')
    outf_mtime = fsutils.get_file_mtime(schpdfpath, fs=refdoc_fs)

    if not force and outf_mtime is not None and outf_mtime > sch_mtime:
        logger.debug('Skipping up-to-date ' + schpdfpath)
        return schpdfpath

    logger.info('Regenerating ' + schpdfpath + os.linesep +
                'Last modified : ' + str(sch_mtime) +
                '; Last Created : ' + str(outf_mtime))

    if configfile.configdata is not None:
        workspace_outpath = workspace_fs.getsyspath(schpdfpath)
        workspace_folder = workspace_fs.getsyspath(path.dirname(schpdfpath))
        workspace_fs.makedir(path.dirname(schpdfpath),
                             recursive=True, allow_recreate=True)
        pdffiles = []
        for schematic in gpf.schfiles:
            schfile = os.path.normpath(projfolder + '/schematic/' + schematic)
            pdffile = gschem.conv_gsch2pdf(schfile, workspace_folder)
            pdffiles.append(pdffile)
        pdf.merge_pdf(pdffiles, workspace_outpath)
        for pdffile in pdffiles:
            os.remove(pdffile)
        copyfile(workspace_fs, schpdfpath,
                 refdoc_fs, schpdfpath,
                 overwrite=True)
        return schpdfpath


def gen_masterdoc(projfolder, namebase, force=False):
    """
    Generates a PDF file of the project's Master documentation. It uses
    other document generator functions to make the various parts of the
    master document and then merges them.

    .. note:: Due to the way groups and motifs are handled, an
              unconfigured BOM is somewhat meaningless. Therefore,
              no BOM is included in the masterdoc.

    :param projfolder: The gEDA project folder.
    :type projfolder: str
    :param namebase: The project name.
    :type namebase: str
    :return: The output file path.

    .. rubric:: Paths

    * Output File :  ``<project_doc_folder>/<namebase>-masterdoc.pdf``
    * Source Files : The project's schematic folder.

    .. rubric:: Included Documents

    * Config Documentation, generated by :func:`gen_configdoc`
    * Schematic PDF, generated by :func:`gen_schpdf`

    """
    gpf = projfile.GedaProjectFile(projfolder)
    sch_mtime = fsutils.get_folder_mtime(gpf.schfolder)

    docfolder = get_project_doc_folder(projfolder)
    masterdocfile = path.join(docfolder, namebase + '-masterdoc.pdf')
    outf_mtime = fsutils.get_file_mtime(masterdocfile, fs=refdoc_fs)

    if not force and outf_mtime is not None and outf_mtime > sch_mtime:
        logger.debug('Skipping up-to-date ' + masterdocfile)
        return masterdocfile

    logger.info('Regnerating ' + masterdocfile + os.linesep +
                'Last modified : ' + str(sch_mtime) +
                '; Last Created : ' + str(outf_mtime))

    pdffiles = [gen_configdoc(projfolder, namebase, force=False),
                gen_schpdf(projfolder, namebase, force=False)]

    for p in pdffiles:
        if p and not workspace_fs.exists(p):
            workspace_fs.makedir(path.dirname(p),
                                 recursive=True, allow_recreate=True)
            copyfile(refdoc_fs, p, workspace_fs, p)

    workspace_pdffiles = [workspace_fs.getsyspath(x)
                          for x in pdffiles if x is not None]

    workspace_outpath = workspace_fs.getsyspath(masterdocfile)
    workspace_fs.makedir(path.dirname(masterdocfile),
                         recursive=True, allow_recreate=True)
    pdf.merge_pdf(workspace_pdffiles, workspace_outpath)
    copyfile(workspace_fs, masterdocfile,
             refdoc_fs, masterdocfile,
             overwrite=True)
    return masterdocfile


def gen_confpdf(projfolder, configname, namebase, force=False):
    """
    Generates a PDF file of the documentation for a specific configuration
    of a project. It uses other document generator functions to make the
    various parts of the master document and then merges them.

    :param projfolder: The gEDA project folder.
    :type projfolder: str
    :param configname: The name of the configuration.
    :type configname: str
    :param namebase: The project name.
    :type namebase: str
    :return: The output file path.

    .. rubric:: Paths

    * Output File :  ``<project_doc_folder>/confdocs/<configname>-doc.pdf``
    * Source Files : The project's schematic folder.

    .. rubric:: Included Documents

    * Configuration BOM, generated by :func:`gen_confbom`
    * (Full) Schematic PDF, generated by :func:`gen_schpdf`

    .. todo:: It may be useful to rebuild the schematics after removing
              all the unpopulated components. This is a fairly involved
              process, and is deferred until later.

    """
    gpf = projfile.GedaProjectFile(projfolder)
    sch_mtime = fsutils.get_folder_mtime(gpf.schfolder)

    docfolder = get_project_doc_folder(projfolder)
    confdocfile = path.join(docfolder, 'confdocs', configname + '-doc.pdf')
    outf_mtime = fsutils.get_file_mtime(confdocfile, fs=refdoc_fs)

    if not force and outf_mtime is not None and outf_mtime > sch_mtime:
        logger.debug('Skipping up-to-date ' + confdocfile)
        return confdocfile

    logger.info('Regenerating ' + confdocfile + os.linesep +
                'Last modified : ' + str(sch_mtime) +
                '; Last Created : ' + str(outf_mtime))

    pdffiles = [gen_confbom(projfolder, configname),
                gen_schpdf(projfolder, namebase)]

    for p in pdffiles:
        if p and not workspace_fs.exists(p):
            workspace_fs.makedir(path.dirname(p),
                                 recursive=True, allow_recreate=True)
            copyfile(refdoc_fs, p, workspace_fs, p)

    workspace_pdffiles = [workspace_fs.getsyspath(x)
                          for x in pdffiles if x is not None]

    workspace_outpath = workspace_fs.getsyspath(confdocfile)
    workspace_fs.makedir(path.dirname(confdocfile),
                         recursive=True, allow_recreate=True)
    pdf.merge_pdf(workspace_pdffiles, workspace_outpath)
    copyfile(workspace_fs, confdocfile,
             refdoc_fs, confdocfile,
             overwrite=True)
    return confdocfile


def gen_cobom_csv(projfolder, namebase, force=False):
    """
    Generates a CSV file in the
    :mod:`tendril.boms.outputbase.CompositeOutputBom` format, including the
    BOMs of the all the defined configurations of the project. This function
    uses a :mod:`csv.writer` instead of rendering a jinja2 template.

    It also generates configdocs for all the defined configurations of the
    project, using :func:`gen_confpdf`.

    :param projfolder: The gEDA project folder.
    :type projfolder: str
    :param namebase: The project name.
    :type namebase: str
    :return: The output file path.

    .. rubric:: Paths

    * Output Files :  ``<project_doc_folder>/confdocs/conf_boms.csv``
    * Also triggers : :func:`gen_confpdf` for all listed configurations.
    * Source Files : The project's schematic folder.

    """
    gpf = projfile.GedaProjectFile(projfolder)
    configfile = conffile.ConfigsFile(projfolder)
    sch_mtime = fsutils.get_folder_mtime(gpf.schfolder)

    docfolder = get_project_doc_folder(projfolder)
    cobom_csv_path = path.join(docfolder, 'confdocs', 'conf-boms.csv')
    outf_mtime = fsutils.get_file_mtime(cobom_csv_path, fs=refdoc_fs)

    if not force and outf_mtime is not None and outf_mtime > sch_mtime:
        logger.debug('Skipping up-to-date ' + cobom_csv_path)
        return cobom_csv_path

    logger.info('Regenerating ' + cobom_csv_path + os.linesep +
                'Last modified : ' + str(sch_mtime) +
                '; Last Created : ' + str(outf_mtime))

    bomlist = []
    for cfn in configfile.configdata['configurations']:
        gen_confpdf(projfolder, cfn['configname'], namebase, force=force)
        lbom = boms_electronics.import_pcb(projfolder)
        lobom = lbom.create_output_bom(cfn['configname'])
        bomlist.append(lobom)
    cobom = boms_outputbase.CompositeOutputBom(bomlist)

    with refdoc_fs.open(cobom_csv_path, 'wb') as f:
        writer = csv.writer(f)
        writer.writerow(['device'] +
                        [x.configname for x in cobom.descriptors])
        for line in cobom.lines:
            writer.writerow([line.ident] + line.columns)


def gen_pcb_pdf(projfolder, force=False):
    """
    Generates a PDF file of the PCB layers for the PCB provided by the
    gEDA project.

    The pcb file is the one listed in the gEDA project file, and the
    pcbname is the one specified in the
    :mod:`tendril.gedaif.conffile.ConfigsFile`.

    This function does not use jinja2 and latex. It relies on
    :func:`tendril.gedaif.pcb.conv_pcb2pdf` instead.

    :param projfolder: The gEDA project folder.
    :type projfolder: str
    :return: The output file path.

    .. rubric:: Paths

    * Output File :  ``<project_doc_folder>/<pcbname>-pdf.pdf``
    * Source Files : The project's `.pcb` file.

    """
    configfile = conffile.ConfigsFile(projfolder)
    gpf = projfile.GedaProjectFile(configfile.projectfolder)
    pcb_mtime = fsutils.get_file_mtime(
        os.path.join(configfile.projectfolder, 'pcb', gpf.pcbfile + '.pcb')
    )
    if pcb_mtime is None:
        logger.warning("PCB does not seem to exist for : " + projfolder)
        return
    docfolder = get_project_doc_folder(projfolder)
    pdffile = path.join(docfolder,
                        configfile.configdata['pcbname'] + '-pcb.pdf')
    outf_mtime = fsutils.get_file_mtime(pdffile, fs=refdoc_fs)

    if not force and outf_mtime is not None and outf_mtime > pcb_mtime:
        logger.debug('Skipping up-to-date ' + pdffile)
        return pdffile

    logger.info('Regenerating ' + pdffile + os.linesep +
                'Last modified : ' + str(pcb_mtime) +
                '; Last Created : ' + str(outf_mtime))

    workspace_folder = workspace_fs.getsyspath(path.dirname(pdffile))
    workspace_fs.makedir(path.dirname(pdffile),
                         recursive=True, allow_recreate=True)

    pcb.conv_pcb2pdf(
        os.path.join(configfile.projectfolder, 'pcb', gpf.pcbfile + '.pcb'),
        workspace_folder, configfile.configdata['pcbname']
    )

    copyfile(workspace_fs, pdffile, refdoc_fs, pdffile, overwrite=True)
    return pdffile


def gen_pcb_gbr(projfolder, force=False):
    """
    Generates gerber files for the PCB provided by the gEDA project, and also
    creates a ``zip`` file of the generated gerbers.

    The pcbfile is the one listed in the gEDA project file, and the
    pcbname is the one specified in the
    :mod:`tendril.gedaif.conffile.ConfigsFile`.

    This function does not use jinja2 and latex. It relies on
    :func:`tendril.gedaif.pcb.conv_pcb2gbr` instead.

    The generated gerber files are retained in the source tree instead of
    being moved to the refdoc filesystem due to the relative sensitivity of
    gerber files to version mismatches.

    :param projfolder: The gEDA project folder.
    :type projfolder: str
    :return: The output file path.

    .. rubric:: Paths

    * Output Files :  ``<projfolder>/gerber/*``
    * Output Zip File : ``<projfolder>/<pcbfile>-gerber.zip``
    * Source Files : The project's `.pcb` file.

    """
    configfile = conffile.ConfigsFile(projfolder)
    gpf = projfile.GedaProjectFile(configfile.projectfolder)
    pcb_mtime = fsutils.get_file_mtime(
        os.path.join(configfile.projectfolder, 'pcb', gpf.pcbfile + '.pcb')
    )
    if pcb_mtime is None:
        logger.warning("PCB does not seem to exist for : " + projfolder)
        return
    gbrfolder = os.path.join(configfile.projectfolder, 'gerber')
    outf_mtime = None
    if not os.path.exists(gbrfolder):
        os.makedirs(gbrfolder)
    else:
        outf_mtime = fsutils.get_folder_mtime(gbrfolder)

    if not force and outf_mtime is not None and outf_mtime > pcb_mtime:
        logger.debug('Skipping up-to-date ' + gbrfolder)
        return gbrfolder

    logger.info('Regenerating ' + gbrfolder + os.linesep +
                'Last modified : ' + str(pcb_mtime) +
                '; Last Created : ' + str(outf_mtime))
    glb = os.path.join(configfile.projectfolder, 'gerber', '*')
    rf = glob.glob(glb)
    for f in rf:
        os.remove(f)
    gbrfolder = pcb.conv_pcb2gbr(
        os.path.join(configfile.projectfolder, 'pcb', gpf.pcbfile + '.pcb')
    )
    zfile = os.path.join(projfolder, gpf.pcbfile + '-gerber.zip')
    fsutils.zipdir(gbrfolder, zfile)
    return gbrfolder


def gen_pcb_dxf(projfolder, force=False):
    """
    Generates a DXF file of the PCB provided by the gEDA project.

    The pcb file is the one listed in the gEDA project file, and the
    pcbname is the one specified in the
    :mod:`tendril.gedaif.conffile.ConfigsFile`.

    This function does not use jinja2 and latex. It relies on
    :func:`tendril.gedaif.pcb.conv_pcb2dxf` instead.

    The generated DXF file is retained in the source tree instead of
    being moved to the refdoc filesystem since is it not just
    expositional, and is a source file for other processes.

    :param projfolder: The gEDA project folder.
    :type projfolder: str
    :return: The output file path.

    .. rubric:: Paths

    * Output File :  ``<projectfolder>/pcb/<pcbfile>.dxf``
    * Source Files : The project's `.pcb` file.

    """
    configfile = conffile.ConfigsFile(projfolder)
    gpf = projfile.GedaProjectFile(configfile.projectfolder)
    pcb_mtime = fsutils.get_file_mtime(
        os.path.join(configfile.projectfolder, 'pcb', gpf.pcbfile + '.pcb')
    )
    if pcb_mtime is None:
        logger.warning("PCB does not seem to exist for : " + projfolder)
        return
    dxffile = os.path.join(configfile.projectfolder, 'pcb',
                           gpf.pcbfile + '.dxf')
    outf_mtime = fsutils.get_file_mtime(dxffile)

    if not force and outf_mtime is not None and outf_mtime > pcb_mtime:
        logger.debug('Skipping up-to-date ' + dxffile)
        return dxffile

    logger.info('Regenerating ' + dxffile + os.linesep +
                'Last modified : ' + str(pcb_mtime) +
                '; Last Created : ' + str(outf_mtime))
    dxffile = pcb.conv_pcb2dxf(
        os.path.join(configfile.projectfolder, 'pcb', gpf.pcbfile + '.pcb'),
        configfile.configdata['pcbname']
    )
    return dxffile


def gen_pcbpricing(projfolder, namebase, force=False):
    """
    Generates a PDF file with the pricing of the (bare) PCB provided by the
    gEDA project.

    The pcb file is the one listed in the gEDA project file, and the
    pcbname is the one specified in the
    :mod:`tendril.gedaif.conffile.ConfigsFile`. The pricing information is
    read out from the PCB's ``sourcing.yaml`` file, which in turn is intended
    to be created by sourcing modules.

    .. todo:: This function presently uses
              :func:`tendril.dox.render.render_lineplot`, which is marked for
              deprecation. It should be rewritten to use the
              :func:`tendril.dox.render.make_graph` route instead.

    :param projfolder: The gEDA project folder.
    :type projfolder: str
    :param namebase: The project name.
    :type namebase: str
    :return: The output file path.

    .. rubric:: Paths

    * Output File :  ``<project_doc_folder>/<namebase>-pricing.pdf``
    * Source Files : ``<projectfolder>/pcb/sourcing.yaml``

    """
    gpf = projfile.GedaProjectFile(projfolder)
    pcbpricingfp = os.path.join(
        gpf.configsfile.projectfolder, 'pcb', 'sourcing.yaml'
    )
    pcbpricing_mtime = fsutils.get_file_mtime(pcbpricingfp)

    if not os.path.exists(pcbpricingfp):
        return None

    docfolder = get_project_doc_folder(projfolder)
    plotfile = path.join(docfolder, namebase + '-pricing.pdf')
    outf_mtime = fsutils.get_file_mtime(plotfile, fs=refdoc_fs)

    if not force and outf_mtime is not None and outf_mtime > pcbpricing_mtime:
        logger.debug('Skipping up-to-date ' + pcbpricingfp)
        return pcbpricingfp

    logger.info('Regnerating ' + plotfile + os.linesep +
                'Last modified : ' + str(pcbpricing_mtime) +
                '; Last Created : ' + str(outf_mtime))

    with open(pcbpricingfp, 'r') as f:
        data = yaml.load(f)

    workspace_outpath = workspace_fs.getsyspath(plotfile)
    workspace_folder = workspace_fs.getsyspath(path.dirname(plotfile))
    workspace_fs.makedir(path.dirname(plotfile),
                         recursive=True, allow_recreate=True)

    plot1file = os.path.join(workspace_folder, namebase + '-1pricing.pdf')
    plot2file = os.path.join(workspace_folder, namebase + '-2pricing.pdf')

    pltnote = "This pricing refers to the bare PCB only. " \
              "See the corresponding Config Docs for Card Pricing"

    plt1data = {key: data['pricing'][key]
                for key in data['pricing'].keys() if key <= 10}
    plt1title = gpf.configsfile.configdata['pcbname']
    plt1title += " PCB Unit Price vs Order Quantity (Low Quantity)"
    plot1file = render.render_lineplot(
        plot1file, plt1data, plt1title, pltnote
    )

    if max(data['pricing'].keys()) > 10:
        plt2data = {key: data['pricing'][key]
                    for key in data['pricing'].keys() if key > 10}
        plt2title = gpf.configsfile.configdata['pcbname']
        plt2title += " PCB Unit Price vs Order Quantity (Production Quantity)"
        plot2file = render.render_lineplot(
            plot2file, plt2data, plt2title, pltnote
        )
        pdf.merge_pdf([plot1file, plot2file], workspace_outpath)
        os.remove(plot2file)
    else:
        shutil.copyfile(plot1file, workspace_outpath)
    os.remove(plot1file)
    copyfile(workspace_fs, plotfile, refdoc_fs, plotfile, overwrite=True)
    return plotfile


def generate_docs(projfolder, force=False):
    """
    Generates all the docs for a specified gEDA project.

    :param projfolder: The gEDA project folder.
    :type projfolder: str
    :return: The output file path.

    .. rubric:: Paths

    * Output File :  ``<project_doc_folder>/confdocs/<configname>-doc.pdf``
    * Source Files : The project's schematic folder.

    .. rubric:: Generated Documents

    * Master Doc, generated by :func:`gen_masterdoc`
    * Cobom CSV, generated by :func:`gen_cobom_csv`
    * PCB PDF, generated by :func:`gen_pcb_pdf`
    * PCB Gerber, generated by :func:`gen_pcb_gbr`
    * PCB DXF, generated by :func:`gen_pcb_dxf`
    * PCB Pricing, generated by :func:`gen_pcbpricing`

    """
    configfile = conffile.ConfigsFile(projfolder)
    try:
        namebase = configfile.configdata['pcbname']
    except KeyError:
        logger.error("pcbname Key Not Found in configs.yaml, skipping")
        return
    if namebase is None:
        try:
            namebase = configfile.configdata['cblname']
        except KeyError:
            logger.error("Project does not have a known identifier. "
                         "Skipping : " + projfolder)
            return
    gen_masterdoc(projfolder, namebase, force)
    gen_cobom_csv(projfolder, namebase, force)
    if configfile.configdata['pcbname'] is not None:
        gen_pcb_pdf(projfolder, force)
        gen_pcb_gbr(projfolder, force)
        gen_pcb_dxf(projfolder, force)
        gen_pcbpricing(projfolder, namebase, force)


def get_docs_list(projfolder, cardname=None):
    configfile = conffile.ConfigsFile(projfolder)
    namebase = configfile.configdata['pcbname']
    is_cable = False
    if namebase is None:
        try:
            namebase = configfile.configdata['cblname']
            is_cable = True
        except KeyError:
            logger.error("Project does not have a known identifier. "
                         "Skipping : " + projfolder)
            return
    project_doc_folder = get_project_doc_folder(projfolder)
    if not project_doc_folder:
        return []
    if not cardname:
        # Get all docs linked to the project
        rval = [ExposedDocument('Project Master Doc',
                                path.join(project_doc_folder,
                                          namebase + '-masterdoc.pdf'),
                                refdoc_fs),
                ExposedDocument(namebase + ' Schematic (Full)',
                                path.join(project_doc_folder,
                                          namebase + '-schematic.pdf'),
                                refdoc_fs),
                ExposedDocument('Composite Bom (All Configs)',
                                path.join(project_doc_folder,
                                          'confdocs',
                                          'conf-boms.csv'),
                                refdoc_fs),
                ]
        if is_cable:
            return rval
        gpf = projfile.GedaProjectFile(configfile.projectfolder)
        rval.extend([ExposedDocument(namebase + ' PCB Layers',
                                     path.join(project_doc_folder,
                                               namebase + '-pcb.pdf'),
                                     refdoc_fs),
                     ExposedDocument(namebase + ' PCB Pricing',
                                     path.join(project_doc_folder,
                                               namebase + '-pricing.pdf'),
                                     refdoc_fs),
                     # TODO This needs to be fixed.
                     ExposedDocument(namebase + ' PCB DXF',
                                     path.join(projfolder, 'pcb',
                                               gpf.pcbfile + '.dxf'),
                                     refdoc_fs),
                     # TODO This needs to be fixed.
                     ExposedDocument(namebase + ' PCB Gerber',
                                     path.join(projfolder,
                                               gpf.pcbfile + '-gerber.zip'),
                                     refdoc_fs),
                     ])
        return rval
    else:
        cardname = cardname.strip()
        rval = [ExposedDocument(cardname + ' Doc',
                                path.join(project_doc_folder,
                                          'confdocs', cardname + '-doc.pdf'),
                                refdoc_fs),
                ExposedDocument(cardname + ' Reference BOM',
                                path.join(project_doc_folder,
                                          'confdocs', cardname + '-bom.pdf'),
                                refdoc_fs),
                ExposedDocument(cardname + ' Schematic (Full)',
                                path.join(project_doc_folder,
                                          namebase + '-schematic.pdf'),
                                refdoc_fs),
                ExposedDocument('Composite Bom (All Configs)',
                                path.join(project_doc_folder,
                                          'confdocs',
                                          'conf-boms.csv'),
                                refdoc_fs),
                ExposedDocument('Project Master Doc',
                                path.join(project_doc_folder,
                                          namebase + '-masterdoc.pdf'),
                                refdoc_fs),
                ]
        return rval
