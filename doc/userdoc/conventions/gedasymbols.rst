

gEDA Symbol Conventions
=======================

gEDA Symbols contain the primary data used by the scripts. As such, these
symbols need to contain the necessary attributes in the correct format.

The conventions listed here are in addition to the standard guidelines and
conventions listed on the gEDA wiki at
`gEDA/gaf Symbol Creation <http://wiki.geda-project.org/geda:gschem_symbol_creation>`_.
In the few instances where the conventions listed here conflict with the
standard guidelines, the conventions listed here should take precedence.

Some attributes listed here are not standard gEDA/gschem attributes, and as
such will cause errors with ``gsymcheck``. This is, unfortunately, unavoidable
without introducing overly unwieldy annotation schemes.

Symbol Attributes
*****************

   :refdes: As per standard gEDA usage.
   :device: This is used as a device class field, with a restricted set of allowed values. See `Device Classes`_.
   :value: The content of this field is Device Class dependent. See `Values`_ for details.
   :footprint: As per standard gEDA usage. This should ideally be a standard footprint name, though at present the scripts don't care.
   :description: ``(Optional)`` Description string, usually the title of the datasheet.
   :symversion: As per standard gEDA usage.
   :status: ``(Optional)`` Defines the status of the symbol. The absence of the attribute entirely is interpreted as ``Active``. See `Symbol Status`_ for more information.
   :fillstatus: ``(Optional)`` Defines if a component is soldered or not. The symbol should not contain this attribute. The attribute should be added as needed in the schematic. ``DNP`` means Do Not Populate. Absence of the attribute altogether indicate normal usage.
   :group: ``(Optional)`` Defines the group of components in the schematic in which the component is included. The symbol should not contain this attribute. The attribute should be added as needed in the schematic. The absence of the attribute entirely is interpreted as the component being in the ``default`` group. See `Component Groups`_ for an introduction to component groups.
   :motif: ``(Optional)`` Identifier for the motif the component is part of (`Motifs`_).
   :package: ``(Optional)`` Defines the package of the component. This should be the JEDEC package nomenclature for the component. This is intended to be used for 3D model generation.

Device Classes
**************

The following are the allowed values for the Device Attributes. More should be added as needed.

.. documentedlist::
    :listobject: tendril.conventions.electronics.DEVICE_CLASSES_DOC


Values
******

General
~~~~~~~

For the general case, value should include the manufacturer part number. The part number should be the minimal
string necessary to uniquely locate components with all paramenters of interest, including Grade, Package, etc.

Unless otherwise specified, canonical representation for each class is constructed as ``DEVICE VALUE FOOTPRINT``.

Resistors
~~~~~~~~~

- Applies to ``RES SMD``, ``RES THRU``, ``RES POWER``, ``RES ARRAY THRU``, ``RES ARRAY SMD``, ``POT TRIM``.
- The value contains the actual resistance value in a standard form.
- Order specifiers to be used are m, E, K, M, G. The ``Ohm`` symbol is excluded.
- The numerical part of the value should be greater than 1 (820E instead of 0.82K)
- For special cases, the full manufacturer part number can be used in place of the reistance value.
- Wattage can optionally (preferably) be specified within value, separated from the resistance value with a ``/``.
- Tolerance, Temperature Coefficient, etc. can also be added similarly to Wattage if needed. If so, the conventions should be amended to reflect the correct order as well as code modifications to any relevent `Script Dependencies`_.
- No spaces should be used.

Examples for Resistor Values :
    * 10m/1W
    * 10E/0.25W
    * 10K/1W
    * 10M/0.125W
    * 10G/0.25W
    * 8K2
    * 8.2K (prefered)
    * PTF561K0000BZEB

Capacitors
~~~~~~~~~~

- Applies to ``CAP CER SMD``, ``CAP TANT SMD``, ``CAP CER THRU``, ``CAP ELEC THRU``, ``CAP POLY THRU``, ``CAP PAPER THRU``.
- The value contains the actual capacitance value in a standard form.
- Order specifiers to be used are p, n, u. The ``F`` symbol is included. (``pF, nF, uF``)
- The numerical part of the value should be greater than 1 (100nF instead of 0.1uF)
- For special cases, the full manufacturer part number can be used in place of the capacitance value.
- Voltage can optionally (preferably) be specified within value, separated from the capacitance value with a ``/``. This voltage is interpreted as the minimum voltage necessary.
- If the ``Voltage`` is not specified, the voltage is assumed to be the ``stdvoltage`` parameter in the generator file, if any.
- For now, the ``Voltage`` should be specified to what is to be purchased (and not the minimum required).
- Tolerance, Temperature, etc. can also be added similarly to Voltage if needed. If so, the conventions should be amended to reflect the correct order as well as code modifications to any relevent `Script Dependencies`_.
- No spaces should be used.

Examples for Capacitor Values :
    * 100nF/50V
    * 10uF/25V
    * 2.2uF/10V
    * 100nF
    * 4700uF/63V

Standard Voltages :

        +---------------------+-----+
        | CAP CER SMD 0805    | 50V |
        +---------------------+-----+
        | CAP TANT SMD TANT B | 25V |
        +---------------------+-----+
        | CAP TANT SMD TANT D | 25V |
        +---------------------+-----+

Diodes
~~~~~~

- Applies to ``DIODE THRU``, ``DIODE SMD``, ``ZENER THRU``, ``ZENER SMD``, ``LED THRU``, ``LED MODULE``, ``BRIDGE RECTIFIER``.
- The value contains the standard part number as far as possible.
- For LEDs, the value contains the Color. The size is determined by the footprint.
- LED Modules and other special LEDs have the necessary details in the value.
- Diodes not derived from standard part numbers should be manually handled in transform and map files.

Examples for Diode Idents :
    * DIODE THRU 1N4007 ALF400-120
    * DIODE THRU 1N5402 ALF600-200
    * LED THRU RED LED3
    * DIODE SMD LL4148 1206P
    * BRIDGE RECTIFIER MB6S TO269AA
    * ZENER SMD AZ23C3V6-7-F SOT23
    * DIODE SMD PGB102ST23 SOT23

Inductors
~~~~~~~~~

- Applies to ``INDUCTOR SMD``, ``INDUCTOR THRU``.
- Given the complexity of Inductor specifications and sourcing, Inductor values should be full manufacturer part numbers.
- For low-end inductors locally obtained, the value attribute can contain the inductance value.
- Order specifiers to be used are n, u, m, with the `H` symbol included (``nH, uH, mH``)
- Additional specifications can be added by using `/`. Spaces should be avoided.
- Further guidelines should be developed if inductors are used often.

Crystals
~~~~~~~~

- Applies to ``CRYSTAL AT``, ``CRYSTAL TF``, ``CRYSTAL OSC``.
- ``VALUE`` should contain the frequency of the crystal along with units. No spaces.
- For special cases, ``VALUE`` can be the full manufacturer part number.

Examples for Crystal Values:
    * 11.0592MHz
    * 16MHz
    * 32.768KHz

Connectors
~~~~~~~~~~

- ``DEVICE`` contains the connector family name as listed previously.
- ``VALUE`` contains the number of contacts, gender, direction (ST/RA), and any other parameters that may exist.
- ``VALUE`` can include spaces. However, every symbol for connectors of the same family should have a consistant structure.
- For highly specialized connectors, the ``VALUE`` attribute contains the manufacturer part number.
- ``FOOTPRINT`` almost always duplicates the information present in ``DEVICE`` and ``VALUE``, and is therefore excluded from the ident string.

Constructors for Connector Idents:
    * CONN INTERBOARD; ESQ-104-12-G-D
    * CONN BERG STRIP; ``2x05PIN 2R [ST/RA] [L?]``
    * CONN BERG STRIP; ``10PIN 1R [ST/RA] [L?]``
    * CONN FRC; ``10PIN [PM/CM] [ST/RA] [NL/WL]``
    * CONN SIP; ``10PIN [PM/CM] [ST/RA]``
    * CONN DTYPE; ``DB25 [PM/CM/WM] [ST/RA] [M/F]``
    * CONN MOLEX MINIFIT; ``10PIN [1R/2R] [M/F] [ST/RA]``
    * CONN MOLEX; ``04PIN PM RA``
    * CONN TERMINAL; ``02PIN [PM/CM] [ST/RA]``
    * CONN TERMINAL BLOCK; ``02PIN [ST/RA/ANG]``
    * CONN MINIDIN; ``04PIN PM [ST/RA]``
    * CONN MODULAR; SS-60000-009
    * CONN DF13; DF13A-5P-1.25H
    * CONN BARREL; 2.1MM PM RA
    * CONN STEREO; 6.3MM PM RA
    * CONN THC; PCC-SMP-K-R
    * CONN USB; B RA PM THRU
    * CONN USB; mB RA PM SMD

Component Groups
****************
HM


Motifs
******

Attribute Syntax Structure : ``[MOTIF_CLASS].[REFDES]-[MOTIF_ELEMENT]``

Examples : ``DLPF1.1:R1``, ``DLPF1.1:R2``, ``DLPF1.1:C1``, ``DLPF1.1:C2``, ``DLPF1.1:C3``

Symbol Status
*************
Symbol status determines how the symbol is handled by the scripts. The ``STATUS`` attribute, if any,
should be within the symbol and not added to the schematic. Within the schematic, the ``STATUS``
attribute should be visible or should be removed, depending on what the status is. (Details Follow).
``STATUS`` is, in some sense, an outer-loop version of gEDA's ``symversion`` attribute.

Allowed Status values:
 :Active: : If the ``STATUS`` attribute is ``Active`` or does not exist, then the scripts treat the symbol as ``Active``. This means the component is acceptable for normal use, and someone in the Company knows the details of procurement and usage of the component.
 :Experimental: If the ``STATUS`` is ``Experimental``, this means that the component is being considered for use. However, care should be taken because the symbol and footprint are likely untested, the component's sourcing details may not be finalized, so on.
 :Deprecated: If the ``STATUS`` is ``Deprecated``, this means a decision has been made to completely phase out use of this component. During redesign of any production PCB, the use of any ``Deprecated`` components should be looked at and removed if possible. Converting a ``Deprecated`` component back into ``Active`` use should involve a specific discussion of the relative merits. Under no circumstances should an Obsolete component be ``Active``.
 :Generator: The ``STATUS`` of ``Generator`` is a special case, indicating that the component represented by the symbol is not necessarily a real component. If such a symbol has a ``VALUE`` attribute, then the ``VALUE`` is the default value for the component and should be valid. The ``VALUE`` attribute of the symbol should be promoted to the schematic and set appropriately (or created if it does not exist in the symbol). Once the ``VALUE`` attribute is set, the ``STATUS=Generator`` attribute should be removed from the component in the schematic. The ``VALUE`` attribute of any symbol whose ``STATUS`` is not ``Generator`` should never be promoted / edited in the schematic under any circumstances.

Attribute Promotion
*******************
HM

Script Dependencies
*******************

At present, the scripts only depend on a subset of the full allowed range of
attribute strings. For the sake of consistency, quality control, and painless
additions of features to the scripts, the strings should follow the guidelines
listed in this document. The actual requirements are listed here for
information and to assist in a gradual migration plan.

:mod:`conventions.electronics`
~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~

Most of the strings listed here are defined in this module, along with string
dependent functions.

:func:`conventions.electronics.eln_ident_transform` :

    If the device string starts with any of the following, it's ident constructor leaves
    out the footprint.

        - ``CONN``
        - ``MODULE``
        - ``CRYSTAL 4PIN``

:mod:`sourcing.electronics`
~~~~~~~~~~~~~~~~~~~~~~~~~~~~

  :IC: If the device string begins with ``IC``, the ``value`` is assumed to be a
         reasonably complete Manufacturer Part Number.

:mod:`sourcing.digikey`
~~~~~~~~~~~~~~~~~~~~~~~~

Description

:func:`sourcing.digikey._search_preprocess` :

    Description

:func:`sourcing.digikey._get_device_catstrings` :

    Description

:func:`sourcing.digikey._tf_resistance_to_canonical` :

    Description
