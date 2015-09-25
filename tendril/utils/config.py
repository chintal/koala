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
The Config Module (:mod:`tendril.utils.config`)
===============================================

This module provides the core configuration for Tendril.

The Tendril configuration file is itself a Python file, and is imported from
it's default location.

This module performs the import using the :func:`tendril.utils.fs.import_`
function and the :mod:`imp` module, following which all the recognized *and*
expected configuration options are imported from the instance configuration
module into this namespace.

.. todo:: The present implementation is fairly silly and tedious. A better
          implementation is necessary.

.. todo:: The actual configuration options themselves need to be documented.

"""

import os
import inspect
from fsutils import import_


CONFIG_PATH = os.path.abspath(inspect.getfile(inspect.currentframe()))
TENDRIL_ROOT = os.path.normpath(
    os.path.join(CONFIG_PATH, os.pardir, os.pardir)
)
INSTANCE_ROOT = os.path.join(os.path.expanduser('~chintal'), '.tendril')
INSTANCE_CONFIG_FILE = os.path.join(INSTANCE_ROOT, 'instance_config.py')
DOX_TEMPLATE_FOLDER = os.path.join(TENDRIL_ROOT, 'dox/templates')

INSTANCE_CONFIG = import_(INSTANCE_CONFIG_FILE)

AUDIT_PATH = INSTANCE_CONFIG.AUDIT_PATH
PROJECTS_ROOT = INSTANCE_CONFIG.PROJECTS_ROOT
SVN_ROOT = INSTANCE_CONFIG.SVN_ROOT
INSTANCE_CACHE = INSTANCE_CONFIG.INSTANCE_CACHE

DOCUMENT_WALLET_ROOT = INSTANCE_CONFIG.DOCUMENT_WALLET_ROOT
DOCSTORE_ROOT = INSTANCE_CONFIG.DOCSTORE_ROOT
REFDOC_ROOT = INSTANCE_CONFIG.REFDOC_ROOT

DOCUMENT_WALLET_PREFIX = INSTANCE_CONFIG.DOCUMENT_WALLET_PREFIX
DOCSTORE_PREFIX = INSTANCE_CONFIG.DOCSTORE_PREFIX
REFDOC_PREFIX = INSTANCE_CONFIG.REFDOC_PREFIX

DOCUMENT_WALLET = INSTANCE_CONFIG.DOCUMENT_WALLET
PRINTER_NAME = INSTANCE_CONFIG.PRINTER_NAME

# gEDA Configuration
GEDA_SCHEME_DIR = INSTANCE_CONFIG.GEDA_SCHEME_DIR
USE_SYSTEM_GAF_BIN = INSTANCE_CONFIG.USE_SYSTEM_GAF_BIN
GAF_BIN_ROOT = INSTANCE_CONFIG.GAF_BIN_ROOT

GAF_ROOT = INSTANCE_CONFIG.GAF_ROOT
GEDA_SYMLIB_ROOT = INSTANCE_CONFIG.GEDA_SYMLIB_ROOT


# Network Configuration
NETWORK_PROXY_TYPE = INSTANCE_CONFIG.NETWORK_PROXY_TYPE
NETWORK_PROXY_IP = INSTANCE_CONFIG.NETWORK_PROXY_IP
NETWORK_PROXY_PORT = INSTANCE_CONFIG.NETWORK_PROXY_PORT
NETWORK_PROXY_USER = INSTANCE_CONFIG.NETWORK_PROXY_USER
NETWORK_PROXY_PASS = INSTANCE_CONFIG.NETWORK_PROXY_PASS
ENABLE_REDIRECT_CACHING = INSTANCE_CONFIG.ENABLE_REDIRECT_CACHING

TRY_REPLICATOR_CACHE_FIRST = INSTANCE_CONFIG.TRY_REPLICATOR_CACHE_FIRST
REPLICATOR_PROXY_TYPE = INSTANCE_CONFIG.REPLICATOR_PROXY_TYPE
REPLICATOR_PROXY_IP = INSTANCE_CONFIG.REPLICATOR_PROXY_IP
REPLICATOR_PROXY_PORT = INSTANCE_CONFIG.REPLICATOR_PROXY_PORT
REPLICATOR_PROXY_USER = INSTANCE_CONFIG.REPLICATOR_PROXY_USER
REPLICATOR_PROXY_PASS = INSTANCE_CONFIG.REPLICATOR_PROXY_PASS

# Database Configuration
DATABASE_HOST = INSTANCE_CONFIG.DATABASE_HOST
DATABASE_PORT = INSTANCE_CONFIG.DATABASE_PORT
DATABASE_USER = INSTANCE_CONFIG.DATABASE_USER
DATABASE_PASS = INSTANCE_CONFIG.DATABASE_PASS
DATABASE_DB = INSTANCE_CONFIG.DATABASE_DB

DB_URI = 'postgresql://' + \
         DATABASE_USER + ":" + DATABASE_PASS + "@" + \
         DATABASE_HOST + ':' + DATABASE_PORT + '/' + \
         DATABASE_DB

# Mail Configuration
MAIL_USERNAME = INSTANCE_CONFIG.MAIL_USERNAME
MAIL_PASSWORD = INSTANCE_CONFIG.MAIL_PASSWORD
MAIL_DEFAULT_SENDER = INSTANCE_CONFIG.MAIL_DEFAULT_SENDER
MAIL_SERVER = INSTANCE_CONFIG.MAIL_SERVER
MAIL_PORT = INSTANCE_CONFIG.MAIL_PORT
MAIL_USE_SSL = INSTANCE_CONFIG.MAIL_USE_SSL
MAIL_USE_TLS = INSTANCE_CONFIG.MAIL_USE_TLS

# Default Admin Configuration
ADMIN_USERNAME = INSTANCE_CONFIG.ADMIN_USERNAME
ADMIN_FULLNAME = INSTANCE_CONFIG.ADMIN_FULLNAME
ADMIN_EMAIL = INSTANCE_CONFIG.ADMIN_EMAIL
ADMIN_PASSWORD = INSTANCE_CONFIG.ADMIN_PASSWORD

# Security Configuration
SECRET_KEY = INSTANCE_CONFIG.SECRET_KEY

# Currency Configuration
BASE_CURRENCY = INSTANCE_CONFIG.BASE_CURRENCY
BASE_CURRENCY_SYMBOL = INSTANCE_CONFIG.BASE_CURRENCY_SYMBOL
CURRENCYLAYER_API_KEY = INSTANCE_CONFIG.CURRENCYLAYER_API_KEY

# Company Configuration
COMPANY_LOGO_PATH = INSTANCE_CONFIG.COMPANY_LOGO_PATH
COMPANY_BLACK_LOGO_PATH = INSTANCE_CONFIG.COMPANY_BLACK_LOGO_PATH
COMPANY_PO_LCO_PATH = INSTANCE_CONFIG.COMPANY_PO_LCO_PATH
COMPANY_GOVT_POINT = INSTANCE_CONFIG.COMPANY_GOVT_POINT
COMPANY_PO_POINT = INSTANCE_CONFIG.COMPANY_PO_POINT
COMPANY_NAME = INSTANCE_CONFIG.COMPANY_NAME
COMPANY_NAME_SHORT = INSTANCE_CONFIG.COMPANY_NAME_SHORT
COMPANY_EMAIL = INSTANCE_CONFIG.COMPANY_EMAIL
COMPANY_ADDRESS_LINE = INSTANCE_CONFIG.COMPANY_ADDRESS_LINE
COMPANY_IEC = INSTANCE_CONFIG.COMPANY_IEC

# Inventory Details
INVENTORY_LOCATIONS = INSTANCE_CONFIG.INVENTORY_LOCATIONS
ELECTRONICS_INVENTORY_DATA = INSTANCE_CONFIG.ELECTRONICS_INVENTORY_DATA

# Vendor Details
vendor_map_audit_folder = INSTANCE_CONFIG.vendor_map_audit_folder
PRICELISTVENDORS_FOLDER = INSTANCE_CONFIG.PRICELISTVENDORS_FOLDER
CUSTOMSDEFAULTS_FOLDER = INSTANCE_CONFIG.CUSTOMSDEFAULTS_FOLDER
VENDORS_DATA = INSTANCE_CONFIG.VENDORS_DATA
