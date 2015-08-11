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

from flask import redirect, render_template
from flask import request, url_for
from flask_user import current_user, login_required
from flask_user.forms import ChangePasswordForm
from flask_user.forms import ChangeUsernameForm

from tendril.frontend.app import app, db
from tendril.frontend.users.forms import UserProfileForm


@app.route('/user/profile', methods=['GET', 'POST'])
@login_required
def user_profile_page():
    # Initialize form
    form = UserProfileForm(request.form, current_user)
    change_username_form = ChangeUsernameForm()
    change_password_form = ChangePasswordForm()
    # Process valid POST
    if request.method == 'POST' and form.validate():

        # Copy form fields to user_profile fields
        form.populate_obj(current_user)

        # Save user_profile
        db.session.commit()

        # Redirect to home page
        return redirect(url_for('home_page'))

    # Process GET or invalid POST
    return render_template('users/user_profile_page.html',
                           form=form,
                           change_username_form=change_username_form,
                           change_password_form=change_password_form,
                           current_user=current_user,
                           pagetitle="User Profile"
                           )
