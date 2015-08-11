

gEDA Project Folder Structure
=============================

The scripts assume a very specific folder structure for gEDA projects, including a
set of minimally required files. It is strongly recommended that the project folders be
laid out exactly as defined here to ensure comaptibilty with present and future functionality.

gEDA Tools
**********

The minimal set of tools which the user should expect to interact with are :

    - ``gschem``, operating on schematics.
    - ``refdes_renum``, operating on schematics.
    - ``gsch2pcb``, operating on schematics to create / update the pcb.
    - ``pcb``, operating on pcb.

The ``gedaif`` package of tendril contains scripts that use these and other ``gEDA`` tools to perform
various functions, and assume a specific file and folder layout. Any deviation from the specified
layout is likely to result in anything from runtime errors to silent omissions from the resultant
data.

Some of the files documented in this section are standard ``gEDA`` files, while others are ``tendril``
specific files.

A gEDA Project
**************

A ``gEDA Project`` consists of exactly one PCB designed using ``gEDA`` tools. Note that this is different
from a ``product``, which can contain one or more ``projects`` (of the gEDA variety or other). The folder
structure listed here is for the standard ``Quazar`` SVN gEDA project.

Nomenclature
~~~~~~~~~~~~

gEDA projects use three levels of naming:

    :projname: Project Name is the base name of the PCB, not including hardware revision and configuration information.
    :pcbname: PCB Name is the actual name of the PCB for external fabrication, and therefore includes revision information but not configuration information.
    :confname: Conf Name or Card Name includes full hardware revision as well as configuration information.

The rationale for separation of PCBs by project, pcb, and configuration is inherently ambiguous, and the
developer / maintainer of a project and / or product line must use his / her discretion to make sure that
the basis used is reasonable. Some suggested guidelines are listed here for reference :

    - The ``Project Name`` can, in principle, exist for the entire duration of relevance of the Project itself.
      However, for the sake of simplicity, it is probably easier to change the project name at points where
      there is a significant change from the previous versions. Minimally, the ``Project Name`` should be
      sufficient to fully define the location of the project in the svn tree, which it does by specifying the
      folder name.
    - The ``PCB Name`` must change, without exception, at every change requiring update of ``gerber`` data,
      however minor the change may be. The ``PCB Name`` must be suffcient information to fully define the data set
      to be sent to a bare PCB fabricator as well as handle inventory checks, etc. This should be the name printed
      on the PCB Silk as well as used in Purchase Orders, Indents, etc.
    - The ``Conf Name`` must change along with ``PCB Name``. Besides this, ``conf names`` are expected to change
      asynchronously with general PCB development in the form of configurations added or removed. The ``Conf Name``
      should be suffcient to fully define the assembled PCB when read with information contained in the ``configs.yaml``
      file and other standard gEDA files.

General Structure of Names::

    [PROJECT-NAME-WITH-EMBEDDED-VARIABLES]-[HARDWARE-REVISION]-[SPECIAL-CONFIGURATION-FLAGS]
where:

        * ``PROJECT-NAME-WITH-EMBEDDED-VARIABLES``
                is a name including lower-case letters as placeholders for variable elements
                within the name. The variables may not be explicitly marked out, in which
                case the highest allowed value is the suggested representation.

                In the "Conf Name", the variables should all be completely resolved to
                the correct values.

                The ``PROJECT-NAME`` itself could generally be of the form::

                    [PRODUCT LINE]-[PRIMARY PCB FUNCTION]-[ADDITIONAL INFORMATION]
                Examples:
                 - ``X-TCON-L1`` for Xplore, Temperature Controller, Linear Design 1
                 - ``QASC-iSTRAIN`` for QDA, Active Signal Conditioner, Interactive Strain
                 - ``QDAL41xB`` for QDA, Low-end Data Acquisition Unit, 10^4 * 1Hz, x Channels, Type B

        * ``HARDWARE-REVISION``
                is a representation of the specific Hardware Revision of
                the PCB, generally represented as ``Rn``, where ``n`` is a number. Further
                information in the hardware revision is probably not a good idea.

        * ``SPECIAL-CONFIGURATION-FLAGS``
                is a list of configuration flags to specify parameters
                that aren't represented in the embedded variables (ex. ``-GR``). In the case
                of core circuit elements that are usually populated except in rare cases,
                the configuration flag can be a negation (ex. ``-NOHV``).

Project Folder Structure
~~~~~~~~~~~~~~~~~~~~~~~~
::

    [projname]
    `-- hardware
        |-- branches
        |-- tags
        |   |-- hR1
        |   |   `-- [full copy of trunk at a specific revision]
        |   ..
        `-- trunk
            |-- ChangeLog
            |-- gerber                          (all-generated-tendril)
            |   |-- [projname].[layer].gbr or cnc
            |   ..
            |-- [projname]-gerber.zip           (generated-tendril)
            |
            |-- pcb
            |   |-- [projname].cmd              (generated-gsch2pcb)
            |   |-- [projname].dxf              (generated-tendril)
            |   |-- [projname].net              (generated-gsch2pcb)
            |   |-- [projname].pcb
            |   `-- sourcing.yaml               (generated-tendril-manual)
            |
            |-- schematic
            |   |-- [schname-1].sch
            |   ..
            |   |-- [schname-n].sch
            |   |-- attribs                     (project-template)
            |   |-- [projname].proj             (project-template-manual)
            |   |-- readme.txt                  (project-template-manual)
            |   `-- configs.yaml                (project-template-manual)
            |
            `-- doc                             (all-generated-tendril)
                |-- [projname]-masterdoc.pdf
                |-- [projname]-configs.pdf
                |-- [projname]-schematic.pdf
                |-- [projname]-pcb.pdf
                `-- confboms
                    |-- [confname-1]-bom.pdf
                    ..
                    |-- [confname-m]-bom.pdf
                    `-- conf-boms.csv
