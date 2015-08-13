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
The Log Utils Module (:mod:`tendril.utils.log`)
===============================================

This module provides utilities to deal with logging systems. The intent of
having this module instead of using :mod:`logging` directly is to allow the
injection of various default parameters and options into all the loggers
used from a central place, instead of littering them throughout the
modules.

At present, this module does nothing that is overly useful, except for
being able to set the default log level for all modules simultaneously.

.. rubric:: Usage Example

>>> from tendril.utils import log
>>> logger = log.get_logger(__name__, log.DEFAULT)

"""

import logging

#: Level for debug entries. High volume is ok
from logging import DEBUG  # noqa
#: Level for informational entires. Low volume
from logging import INFO # noqa
#: Warnings only, which inform of possible failure
from logging import WARNING # noqa
#: Errors only, which inform of high likelihood of failure
from logging import ERROR # noqa
#: Critical Errors, things which should halt execution entirely
from logging import CRITICAL # noqa


#: The default log level for all loggers created through this module,
#: unless otherwise specified at the time of instantiation.
DEFAULT = logging.INFO


def init():
    logging.basicConfig(level=logging.DEBUG)


def get_logger(name, level):
    """
    Get a logger with the specified ``name`` and an optional ``level``.

    The levels from the python :mod:`logging` module can be used directly.
    For convenience, these levels are imported into this module's namespace
    as well, along with the :data:`DEFAULT` level this module provides.

    See python :mod:`logging` documentation for information about log levels.

    :param name: The name of the logger
    :type name: str
    :param level: Log level of the logger to be used. Default : :data:`DEFAULT`.
    :type level: int
    :return: The logger instance
    """
    logger = logging.getLogger(name)
    if level is not None:
        logger.setLevel(level)
    else:
        logger.setLevel(DEFAULT)
    return logger


init()
