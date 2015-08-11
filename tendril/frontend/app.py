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

from flask import Flask
from flask_sqlalchemy import SQLAlchemy


# This is the WSGI compliant web application object
app = Flask(__name__)


# This is an SQLAlchemy ORM object.
#
# For the moment it points to a separate DB holding only app specific information, i.e., access control
# mechanisms only. The fundamental difference between this db instance and the one provided by utils.db
# is that this relies on Flask-SQLAlchemy provided db.Model and it's session management. The app should
# filter and do whatever it needs to based on the app DB and then pass whatever information is necessary
# to the underlying core via traditional function calls.
#
# This should be revisited at some point to reintegrate the DBs, either by switching to the correct Base
# within the Flask-SQLAlchemy (and sorting out the consequences to session management, as well as ensuring
# that the Base is compatible with what Flask plugins expect), or rewriting the Flask plugins to work with
# the vanilla Base.
db = SQLAlchemy(app)
