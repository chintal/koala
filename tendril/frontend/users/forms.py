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


from flask_user.forms import RegisterForm
from flask_wtf import Form
from wtforms import StringField, SubmitField, validators


# Define the User registration form
# It augments the Flask-User RegisterForm with additional fields
class MyRegisterForm(RegisterForm):
    full_name = StringField('Full name', validators=[validators.DataRequired('Full name is required')])


# Define the User profile form
class UserProfileForm(Form):
    full_name = StringField('Full name', validators=[validators.DataRequired('Full name is required')])
    submit = SubmitField('Save')
