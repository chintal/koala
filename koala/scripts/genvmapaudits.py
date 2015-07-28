"""
This file is part of koala
See the COPYING, README, and INSTALL files for more information
"""

import koala.sourcing.electronics


for vendor in koala.sourcing.electronics.vendor_list:
    koala.sourcing.electronics.export_vendor_map_audit(vendor)
