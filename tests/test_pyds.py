#!/usr/bin/env python
#
# Copyright (C) 2016 Yann Diorcet
#
# This file is part of PYDS.  PYDS is free software: you can
# redistribute it and/or modify it under the terms of the GNU General Public
# License as published by the Free Software Foundation, version 2.
#
# This program is distributed in the hope that it will be useful, but WITHOUT
# ANY WARRANTY; without even the implied warranty of MERCHANTABILITY or FITNESS
# FOR A PARTICULAR PURPOSE.  See the GNU General Public License for more
# details.
#
# You should have received a copy of the GNU General Public License along with
# this program; if not, write to the Free Software Foundation, Inc., 51
# Franklin Street, Fifth Floor, Boston, MA 02110-1301 USA.
#

# Fix Python 2.x.
from __future__ import print_function

__author__ = "Yann Diorcet"
__license__ = "GPL"
__version__ = "0.0.1"

import unittest
from pyds.types import Normal, MCP_BCE_2
from pyds.actions import unlock_rbcm_features


class Pyds_Test(unittest.TestCase):

    def test_unlock_rbcm(self):
        de00data = bytearray([0x45, 0x50, 0x00, 0x06, 0xA1, 0xA5, 0x0C, 0x43, 0x00, 0x08, 0x00, 0x38, 0x92, 0x10])
        de00data_mod = bytearray([0x45, 0xD0, 0x00, 0x06, 0xA1, 0xA5, 0x0C, 0x43, 0x00, 0x20, 0x00, 0x38, 0x92, 0x10])
        de01data = bytearray([0x00, 0x38, 0x10, 0xa0, 0x70])
        de01data_mod = bytearray([0x10, 0x38, 0x10, 0xa0, 0x70])

        de00data_obj = Normal(de00data)
        de01data_obj = MCP_BCE_2(de01data)

        ret = unlock_rbcm_features({0xde00: de00data_obj, 0xde01: de01data_obj})
        self.assertEqual(ret[0xde00].to_bytearray(), de00data_mod)
        self.assertEqual(ret[0xde01].to_bytearray(), de01data_mod)

    def test_enable_scbs_r(self):
        pass
