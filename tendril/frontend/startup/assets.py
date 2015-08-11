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

import os

from flask_assets import Bundle, Environment
from tendril.frontend.app import app

from tendril.utils.config import INSTANCE_CACHE


bundles = {
    'base_css': Bundle(
        'css/normalize.css',
        'css/foundation.css',
        'css/foundation-icons.css',
        'css/responsive-tables.css',
        'css/colors.css',
        'css/tendril.css',
        output='gen/base.css',
        filters='cssmin'),

    'base_js': Bundle(
        'js/vendor/modernizr.js',
        'js/vendor/jquery.js',
        output='gen/base.js',
        filters='jsmin'),

    'foundation_js': Bundle(
        'js/foundation/foundation.js',
        'js/foundation/foundation.topbar.js',
        'js/foundation/foundation.dropdown.js',
        'js/foundation/foundation.magellan.js',
        'js/foundation/foundation.equalizer.js',
        'js/foundation/foundation.alert.js',
        'js/vendor/stickyFooter.js',
        'js/vendor/responsive-tables.js',
        'js/vendor/jquery.textfill.js',
        output='gen/foundation.js',
        filters='jsmin')
}


assets = Environment(app)
assets.cache = os.path.join(INSTANCE_CACHE, 'flaskassetcache')
assets.register(bundles)
