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


import logging
from logging.handlers import SMTPHandler
from urllib2 import quote, unquote

from flask_mail import Mail
from flask_user import UserManager, SQLAlchemyAdapter


def init_app(app, db):
    """
    Initialize Flask applicaton
    """
    # Initialize app config settings
    app.config.from_object('tendril.frontend.startup.settings')
    if app.testing:
        app.config['WTF_CSRF_ENABLED'] = False              # Disable CSRF checks while testing

    # Initialize Assets
    from tendril.frontend.startup import assets  # noqa

    # Create Filters

    def unicode_filter(s):
        return unicode(s, 'utf-8')
    app.jinja_env.filters['unicode'] = unicode_filter

    def quote_filter(s):
        return quote(s)
    app.jinja_env.filters['quote'] = quote_filter

    def unquote_filter(s):
        return unquote(s)
    app.jinja_env.filters['unquote'] = unquote_filter

    def strip(s):
        return s.strip()
    app.jinja_env.filters['strip'] = strip

    # Setup Flask-Mail
    mail = Mail(app)  # noqa

    # Setup an error-logger to send emails to app.config.ADMINS
    init_error_logger_with_email_handler(app)

    # Setup Flask-User to handle user account related forms
    from tendril.frontend.users.models import UserAuth, User
    from tendril.frontend.users.forms import MyRegisterForm
    from tendril.frontend.users.views import user_profile_page
    db_adapter = SQLAlchemyAdapter(db, User,
                                   UserAuthClass=UserAuth)
    user_manager = UserManager(db_adapter, app,  # noqa
                               register_form=MyRegisterForm,
                               user_profile_view_function=user_profile_page,
                               )

    # Load all models.py files to register db.Models with SQLAlchemy
    from tendril.frontend.users import models  # noqa

    # Load all views.py files to register @app.routes() with Flask
    from tendril.frontend.pages import views  # noqa
    from tendril.frontend.users import views  # noqa

    # Register blueprints
    from tendril.frontend.blueprints.doc import doc
    app.register_blueprint(doc, url_prefix='/doc')

    from tendril.frontend.blueprints.gsymlib import gsymlib
    app.register_blueprint(gsymlib, url_prefix='/gsymlib')

    from tendril.frontend.blueprints.entityhub import entityhub
    app.register_blueprint(entityhub, url_prefix='/entityhub')

    from tendril.frontend.blueprints.conventions import conventions
    app.register_blueprint(conventions, url_prefix='/conventions')

    return app


def init_error_logger_with_email_handler(app):
    """
    Initialize a logger to send emails on error-level messages.
    Unhandled exceptions will now send an email message to app.config.ADMINS.
    """
    if app.debug:
        return                        # Do not send error emails while developing

    # Retrieve email settings from app.config
    host = app.config['MAIL_SERVER']
    port = app.config['MAIL_PORT']
    from_addr = app.config['MAIL_DEFAULT_SENDER']
    username = app.config['MAIL_USERNAME']
    password = app.config['MAIL_PASSWORD']
    secure = () if app.config.get('MAIL_USE_TLS') else None

    # Retrieve app settings from app.config
    to_addr_list = app.config['ADMINS']
    subject = app.config.get('APP_SYSTEM_ERROR_SUBJECT_LINE', 'System Error')

    # Setup an SMTP mail handler for error-level messages
    mail_handler = SMTPHandler(
        mailhost=(host, port),                  # Mail host and port
        fromaddr=from_addr,                     # From address
        toaddrs=to_addr_list,                   # To address
        subject=subject,                        # Subject line
        credentials=(username, password),       # Credentials
        secure=secure,
    )
    mail_handler.setLevel(logging.ERROR)
    app.logger.addHandler(mail_handler)

    # Log errors using: app.logger.error('Some error message')
