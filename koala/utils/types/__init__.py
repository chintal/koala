# Copyright (C) 2015 Chintalagiri Shashank
#
# This file is part of Koala.
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
The Types Module (:mod:`koala.utils.types`)
===========================================

The :mod:`koala.utils.types` module, like all the :mod:`koala.utils` modules,
includes code that ideally resides outside of Koala itself, perhaps using some
standard or third-party package. In the case of :mod:`koala.utils.types`, this
module provides various submodules and consequently classes to handle special
data types - usually data structures and units. These use cases are more
thoroughly and effectively handled by various third-party modules, and it's
existence in Koala is largely due to a combination of the *Not Invented Here*
syndrome, as well as the overwhelming number of possible options available,
none of which seem to be ideal drop in replacements for Koala core's
requirements.

While you can use the units and data structures from :mod:`koala.utils.types`
independent of the rest of Koala, you probably should not. The code itself
should function, but it lacks the thoroughness of type-checking or the
efficiency of more full fledged implementations. Even when using Koala units
to handle data generated by one of the Koala submodules, I strongly recommend
using a full-fledged unit package instead. If you'd like to use them anyway,
well, you have been warned.

Converters from Koala types to other forms should be reasonably
straightforward to write, and over time some these converters and/or
re-implementations using an established types/units package will hopefully
find their way into the classes defined within :mod:`koala.utils.types`.

The general principles of design used for the units defined within this module
are as follows :

- If there is an obvious good-fit python package available to provide the units
  or data structures required, use that instead and simply proxy to that
  package within this module. Data-structures are relatively more complex beasts,
  so the remaining principles don't apply to them. They follow more of a *use your
  best judgement* type of development principle.

- The fundamental nature of unit instantiation must remain stable and consistent
  within the various units defined. The underlying implementation isn't
  important as long as it provides the functionality required via the accessors
  Koala expects. More importantly, changing the underlying implementation
  should not change the way application code uses the units.

- In most cases, primary unit instantiation is using a string containing the
  value the object should hold as well as the unit. Units can also be
  instantiated using a :class:`numbers.Number` instance, but application code
  should avoid doing this. This interface is provided largely to support
  arithmetic operations defined between units.

- For each 'simple' unit class, unless provided by an external library, the
  core information should be a number in the "canonical" unit of that class.
  The class should also store the original string.

- Wherever possible, the numbers stored should be :class:`decimal.Decimal`
  instances and not floats. Number of significant digits should ideally be
  tracked, but presently is not.

- The unit classes should support the bare-minimum set of valid operations.
  As far as possible, the simple mathematical operations performed with two
  elements of the same unitclass should produce a valid result (if
  physically meaningful)

- The unit classes should not produce physically meaningless results. This is
  not something that's tested all that much, so it's likely corner cases have
  slipped through the cracks.

- Be unafraid to throw exceptions. If application code misuses the units, the
  application is asking to be penalized.

.. warning::
  No effort is made to have a complete set of units, or even a complete set of
  units of the same dimensionality as the supported units. Addition of new
  types is done on a lazy basis, as are type conversions, inter-unit arithmetic,
  and other ranges. This policy is likely to change only if this module is
  pulled out of Koala into it's own units library, and maintaining that isn't
  something I'm likely to do alone.


.. rubric:: Submodules

.. toctree::

   koala.utils.types.currency
   koala.utils.types.time
   koala.utils.types.lengths
   koala.utils.types.cartesian
   koala.utils.types.unitbase
   koala.utils.types.electromagnetic
   koala.utils.types.thermodynamic
   koala.utils.types.signalbase

.. rubric:: Inheritance Diagram

.. inheritance-diagram::
   koala.utils.types
   koala.utils.types.cartesian
   koala.utils.types.currency
   koala.utils.types.electromagnetic
   koala.utils.types.thermodynamic
   koala.utils.types.lengths
   koala.utils.types.time
   koala.utils.types.signalbase
   koala.utils.types.unitbase

"""
