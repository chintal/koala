"""
Production Dox module documentation (:mod:`dox.production`)
============================================================
"""


import boms.electronics
import render
import os


def gen_pcb_am(projfolder, configname, outpath=None, sno=None):
    if sno is None:
        # TODO Generate real S.No. here
        sno = 1
    else:
        # TODO Verify S.no. is correct and create if needed
        pass

    if outpath is None:
        # TODO Generate correct outpath here
        outpath = os.path.normpath(projfolder + '/am-' + configname + '-' + str(sno) + '.pdf')

    bom = boms.electronics.import_pcb(projfolder)
    obom = bom.create_output_bom(configname)

    stage = {'configname': obom.descriptor.configname,
             'pcbname': obom.descriptor.pcbname,
             'sno': sno,
             'lines': obom.lines}

    for config in obom.descriptor.configurations.configurations:
        if config['configname'] == configname:
            stage['desc'] = config['desc']

    template = 'pcb-assem-manifest.tex'

    render.render_pdf(stage, template, outpath)

