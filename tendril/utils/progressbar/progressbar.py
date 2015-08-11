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
:mod:`progressbar.progressbar`
------------------------------

Draws an animated terminal progress bar.

.. rubric: Usage

>>> p = ProgressBar("blue")
>>> p.render(percentage, message)

"""

import terminal
import sys


class ProgressBar(object):
    """ Terminal progress bar class

        :param color: Color name (BLUE GREEN CYAN RED MAGENTA YELLOW WHITE BLACK)
        :type color: str
        :param width: Bar width (optional)
        :type width: numbers.Number
        :param block: Progress display character
        :type block: char
        :param empty: Bar display character (default ' ')
        :type empty: char

    """

    TEMPLATE = (
        '%(percent)-2s%% %(color)s%(progress)s%(normal)s%(empty)s %(message)s\n'
    )
    PADDING = 7

    def __init__(self, color=None, width=None, block='█', empty=' '):
        if color:
            self.color = getattr(terminal, color.upper())
        else:
            self.color = ''
        if width and width < terminal.COLUMNS - self.PADDING:
            self.width = width
        else:
            # Adjust to the width of the terminal
            self.width = terminal.COLUMNS - self.PADDING
        self.block = block
        self.empty = empty
        self.progress = None
        self.lines = 0

    def render(self, percent, message=''):
        """
        Print the progress bar.

        :param percent: The progress percentage (0-100)
        :type percent: int
        :param message: Message string (optional)
        :type message: str
        """
        inline_msg_len = 0
        if message:
            # The length of the first line in the message
            inline_msg_len = len(message.splitlines()[0])
        if inline_msg_len + self.width + self.PADDING > terminal.COLUMNS:
            # The message is too long to fit in one line.
            # Adjust the bar width to fit.
            bar_width = terminal.COLUMNS - inline_msg_len - self.PADDING
        else:
            bar_width = self.width

        # Check if render is called for the first time
        if self.progress is not None:
            self.clear()
        self.progress = (bar_width * percent) / 100
        data = self.TEMPLATE % {
            'percent': percent,
            'color': self.color,
            'progress': self.block * self.progress,
            'normal': terminal.NORMAL,
            'empty': self.empty * (bar_width - self.progress),
            'message': message
        }
        sys.stdout.write(data)
        sys.stdout.flush()
        # The number of lines printed
        self.lines = len(data.splitlines())

    def clear(self):
        """ Clear all printed lines """
        sys.stdout.write(
            self.lines * (terminal.UP + terminal.BOL + terminal.CLEAR_EOL)
        )
