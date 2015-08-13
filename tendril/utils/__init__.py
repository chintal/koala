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
The Utils Package (:mod:`tendril.utils`)
========================================

The :mod:`utils` package contains various Utils modules which provide
functionality that is either :

- Logically independent of the main Tendril functionality.
- Used by multiple Tendril's packages, either due to generic nature of the
  functionality, or because it defines the structure that functionality should
  take within Tendril.

These modules typically expose specific functionality of third-party or
built-in Python modules and simplify access by restricting the ways in which
these modules can be used. For instance, various options are preselected
within the Utils module, meaning application code does not have to bother
about it. This comes at the cost of reducing the flexibility available when
using this functionality in application code.

The intent of the :mod:`tendril.utils` package and it's modules is to attempt to
create a consistent structure throughout the :mod:`tendril` codebase. The
:mod:`tendril.utils` module, in effect, specifies the preferred way to do certain
common things. Tendril application code which makes use of the functionality of
this module is expected to benefit in the form of consistency, relative
ease in honoring user-provided parameters (across the codebase), and not need
to deal with the underlying libraries and the wide range of usage options
available for the most common cases.

It is expected that this structure will be critical to being able to easily
adapt the Tendril codebase to new environments and for making more flexibility
accessible to administrators of Tendril instances.

Many of the modules provided here can be re-implemented to use different
underlying implementations, while preserving the interface they present to
Tendril application code.

.. warning:: It is possible that this approach will soon reach the point of
             diminishing returns.

.. rubric:: The Utility Modules

.. toctree::

    tendril.utils.progressbar
    tendril.utils.types
    tendril.utils.colors
    tendril.utils.config
    tendril.utils.db
    tendril.utils.fs
    tendril.utils.libreoffice
    tendril.utils.log
    tendril.utils.pdf
    tendril.utils.state
    tendril.utils.www

"""
