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


import os

APP_NAME = "Tendril"

# Flask settings
from tendril.utils.config import SECRET_KEY  # noqa

# SQLAlchemy settings
from tendril.utils.config import INSTANCE_ROOT
SQLALCHEMY_DATABASE_URI = 'sqlite:///' + os.path.join(INSTANCE_ROOT, 'db', 'auth.db')

# Flask-Mail settings
from tendril.utils.config import MAIL_DEFAULT_SENDER  # noqa
from tendril.utils.config import MAIL_PASSWORD  # noqa
from tendril.utils.config import MAIL_PORT  # noqa
from tendril.utils.config import MAIL_SERVER  # noqa
from tendril.utils.config import MAIL_USE_SSL  # noqa
from tendril.utils.config import MAIL_USE_TLS  # noqa
from tendril.utils.config import MAIL_USERNAME  # noqa

# Disable E-mail
USER_ENABLE_EMAIL = True
USER_ENABLE_LOGIN_WITHOUT_CONFIRM = True
USER_ENABLE_CONFIRM_EMAIL = False
USER_SEND_USERNAME_CHANGED_EMAIL = False
USER_SEND_PASSWORD_CHANGED_EMAIL = False
USER_SEND_REGISTERED_EMAIL = False
USER_ENABLE_FORGOT_PASSWORD = False
USER_ENABLE_MULTIPLE_EMAILS = False
USER_REQUIRE_INVITATION = False

from tendril.utils.config import ADMIN_EMAIL
ADMINS = [ADMIN_EMAIL]

# Application settings
APP_SYSTEM_ERROR_SUBJECT_LINE = APP_NAME + " system error"

# Flask settings
CSRF_ENABLED = True

# Flask-User settings
USER_APP_NAME = APP_NAME
USER_LOGIN_TEMPLATE = 'flask_user/login_or_register.html'
USER_REGISTER_TEMPLATE = 'flask_user/login_or_register.html'
USER_AFTER_CHANGE_PASSWORD_ENDPOINT = 'user.profile'
USER_AFTER_CHANGE_USERNAME_ENDPOINT = 'user.profile'
