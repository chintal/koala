#!/usr/bin/env python
# encoding: utf-8

# Copyright (c) 2015, Chintalagiri Shashank
# Copyright (c) 2009, Nadia Alramli
# All rights reserved.
#
# BSD License:
#
# Redistribution and use in source and binary forms, with or without
# modification, are permitted provided that the following conditions are met:
#
# * Redistributions of source code must retain the above copyright notice, this
#   list of conditions and the following disclaimer.
#
# * Redistributions in binary form must reproduce the above copyright notice,
#   this list of conditions and the following disclaimer in the documentation
#   and/or other materials provided with the distribution.
#
# * Neither the name of the project nor the names of its
#   contributors may be used to endorse or promote products derived from
#   this software without specific prior written permission.
#
# THIS SOFTWARE IS PROVIDED BY THE COPYRIGHT HOLDERS AND CONTRIBUTORS "AS IS"
# AND ANY EXPRESS OR IMPLIED WARRANTIES, INCLUDING, BUT NOT LIMITED TO, THE
# IMPLIED WARRANTIES OF MERCHANTABILITY AND FITNESS FOR A PARTICULAR PURPOSE ARE
# DISCLAIMED. IN NO EVENT SHALL THE COPYRIGHT HOLDER OR CONTRIBUTORS BE LIABLE
# FOR ANY DIRECT, INDIRECT, INCIDENTAL, SPECIAL, EXEMPLARY, OR CONSEQUENTIAL
# DAMAGES (INCLUDING, BUT NOT LIMITED TO, PROCUREMENT OF SUBSTITUTE GOODS OR
# SERVICES; LOSS OF USE, DATA, OR PROFITS; OR BUSINESS INTERRUPTION) HOWEVER
# CAUSED AND ON ANY THEORY OF LIABILITY, WHETHER IN CONTRACT, STRICT LIABILITY,
# OR TORT (INCLUDING NEGLIGENCE OR OTHERWISE) ARISING IN ANY WAY OUT OF THE USE
# OF THIS SOFTWARE, EVEN IF ADVISED OF THE POSSIBILITY OF SUCH DAMAGE.

"""
:mod:`progressbar.terminal`
---------------------------

Terminal controller module

.. rubric: Usage

>>> print BG_BLUE + 'Text on blue background' + NORMAL
>>> print BLUE + UNDERLINE + 'Blue underlined text' + NORMAL
>>> print BLUE + BG_YELLOW + BOLD + 'text' + NORMAL

"""

import sys
import os

# The current module
MODULE = sys.modules[__name__]

COLORS = "BLUE GREEN CYAN RED MAGENTA YELLOW WHITE BLACK".split()
# List of terminal controls, you can add more to the list.
CONTROLS = {
    'BOL': 'cr', 'UP': 'cuu1', 'DOWN': 'cud1', 'LEFT': 'cub1', 'RIGHT': 'cuf1',
    'CLEAR_SCREEN': 'clear', 'CLEAR_EOL': 'el', 'CLEAR_BOL': 'el1',
    'CLEAR_EOS': 'ed', 'BOLD': 'bold', 'BLINK': 'blink', 'DIM': 'dim',
    'REVERSE': 'rev', 'UNDERLINE': 'smul', 'NORMAL': 'sgr0',
    'HIDE_CURSOR': 'cinvis', 'SHOW_CURSOR': 'cnorm'
}

# List of numeric capabilities
VALUES = {
    'COLUMNS': 'cols',  # Width of the terminal (None for unknown)
    'LINES': 'lines',  # Height of the terminal (None for unknown)
    'MAX_COLORS': 'colors',
}


def default():
    """Set the default attribute values"""
    for color in COLORS:
        setattr(MODULE, color, '')
        setattr(MODULE, 'BG_%s' % color, '')
    for control in CONTROLS:
        setattr(MODULE, control, '')
    for value in VALUES:
        setattr(MODULE, value, None)


def setup():
    """Set the terminal control strings"""
    # Initializing the terminal
    curses.setupterm()
    # Get the color escape sequence template or '' if not supported
    # setab and setaf are for ANSI escape sequences
    bgColorSeq = curses.tigetstr('setab') or curses.tigetstr('setb') or ''
    fgColorSeq = curses.tigetstr('setaf') or curses.tigetstr('setf') or ''

    for color in COLORS:
        # Get the color index from curses
        colorIndex = getattr(curses, 'COLOR_%s' % color)
        # Set the color escape sequence after filling the template with index
        setattr(MODULE, color, curses.tparm(fgColorSeq, colorIndex))
        # Set background escape sequence
        setattr(
            MODULE, 'BG_%s' % color, curses.tparm(bgColorSeq, colorIndex)
        )
    for control in CONTROLS:
        # Set the control escape sequence
        setattr(MODULE, control, curses.tigetstr(CONTROLS[control]) or '')
    for value in VALUES:
        # Set terminal related values
        setattr(MODULE, value, curses.tigetnum(VALUES[value]))


def render(text):
    """Helper function to apply controls easily

    .. rubric: Example for a bold green text

        apply("%(GREEN)s%(BOLD)stext%(NORMAL)s")

    """
    return text % MODULE.__dict__


# Ugly fix for pyCharm
try:
    dummy = os.environ['TERMINFO']
except KeyError:
    os.environ['TERM'] = 'linux'
    os.environ['TERMINFO'] = '/etc/terminfo'

try:
    import curses
    setup()
except Exception, e:
    # There is a failure; set all attributes to default
    print 'Warning: %s' % e
    default()
