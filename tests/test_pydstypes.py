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
from pyds.pydstypes import MCP_BCE_2, Read

class Read_Test(unittest.TestCase):
    # Byte array to bit array to byte array
    def test_byte_bit_array(self):
        data = bytearray([0x45, 0x50, 0x00, 0x06, 0xA1, 0xA5, 0x0C, 0x43, 0x00, 0x08, 0x00, 0x38, 0x92, 0x10])
        self.assertEqual(Read._bitarraytobytearray(Read._bytearraytobitarray(data)), data)

    # Bit array to bytes array to bit array
    def test_bit_bytes_array(self):
        data = [0x1, 0x0, 0x1, 0x1, 0x1, 0x0, 0x1, 0x1]
        self.assertEqual(MCP_BCE_2._bytearraytobitarray(MCP_BCE_2._bitarraytobytearray(data)), data)

    def test_sanity(self):
        mod = bytearray([0x00, 0x00, 0x00])
        bs = Read(mod)
        bs.set_value(5, 0x3, 2)
        bs2 = Read(mod)
        bs2.set_value(6, 0x1, 1)
        self.assertEqual(bs.to_bytearray(), bs2.to_bytearray())

    def test_door(self):
        mod = bytearray([0x00, 0xa7, 0x00, 0x00, 0x00, 0x20, 0x020])
        bs = Read(mod)
        self.assertEqual(bs.get_value(4, 0x1), 0x0)  # Driver Side Door Lock Link Switch (Lock Side) OFF
        self.assertEqual(bs.get_value(5, 0x1), 0x1)  # Driver Side Door Lock Link Switch (Unlock Side) ON
        self.assertEqual(bs.get_value(14, 0x1), 0x0)  # All Door CLOSE
        self.assertEqual(bs.get_value(15, 0x1), 0x0)  # Driver Door CLOSE
        mod = bytearray([0x00, 0xa7, 0x00, 0x00, 0x00, 0xe0, 0x020])
        bs = Read(mod)
        self.assertEqual(bs.get_value(4, 0x1), 0x0)  # Driver Side Door Lock Link Switch (Lock Side) OFF
        self.assertEqual(bs.get_value(5, 0x1), 0x1)  # Driver Side Door Lock Link Switch (Unlock Side) ON
        self.assertEqual(bs.get_value(14, 0x1), 0x1)  # All Door OPEN
        self.assertEqual(bs.get_value(15, 0x1), 0x1)  # Driver Door OPEN
        mod = bytearray([0x00, 0xa7, 0x00, 0x00, 0x00, 0x20, 0x010])
        bs = Read(mod)
        self.assertEqual(bs.get_value(4, 0x1), 0x1)  # Driver Side Door Lock Link Switch (Lock Side) ON
        self.assertEqual(bs.get_value(5, 0x1), 0x0)  # Driver Side Door Lock Link Switch (Unlock Side) OFF
        self.assertEqual(bs.get_value(14, 0x1), 0x0)  # All Door CLOSE
        self.assertEqual(bs.get_value(15, 0x1), 0x0)  # Driver Door CLOSE

class MCP_BCE_2_Test(unittest.TestCase):
    # Byte array to bit array to byte array
    def test_byte_bit_array(self):
        data = bytearray([0x00, 0x38, 0x08, 0xa0, 0x50])
        self.assertEqual(MCP_BCE_2._bitarraytobytearray(MCP_BCE_2._bytearraytobitarray(data)), data)

    # Bit array to bytes array to bit array
    def test_bit_bytes_array(self):
        data = [0x1, 0x0, 0x1, 0x1, 0x1, 0x0, 0x1, 0x1]
        self.assertEqual(MCP_BCE_2._bytearraytobitarray(MCP_BCE_2._bitarraytobytearray(data)), data)

    # 3 Flashs Turn
    def test_3_flashs_turn(self):
        mod = bytearray([0x00, 0x38, 0x08, 0xa0, 0x50])
        bs = MCP_BCE_2(mod)
        self.assertEqual(bs.get_value(19, 3), 0x1)  # Off
        bs = MCP_BCE_2(bytearray([0x00, 0x38, 0x10, 0xa0, 0x50]))
        self.assertEqual(bs.get_value(19, 3), 0x2)  # On
        bs.set_value(19, 3, 0x1)
        self.assertEqual(bs.to_bytearray(), mod)

    # Head light
    def test_head_light(self):
        mod = bytearray([0x00, 0x38, 0x10, 0xa8, 0x50])
        bs = MCP_BCE_2(mod)
        self.assertEqual(bs.get_value(26, 7), 0x5)  # Light
        bs = MCP_BCE_2(bytearray([0x00, 0x38, 0x10, 0xa0, 0x50]))
        self.assertEqual(bs.get_value(26, 7), 0x4)  # Medium Light
        bs.set_value(26, 7, 0x5)
        self.assertEqual(bs.to_bytearray(), mod)

    # Head light off timer
    def test_head_light_off_timer(self):
        mod = bytearray([0x00, 0x38, 0x50, 0xa0, 0x50])
        bs = MCP_BCE_2(mod)
        self.assertEqual(bs.get_value(16, 7), 0x2)  # 30s
        bs = MCP_BCE_2(bytearray([0x00, 0x38, 0x10, 0xa0, 0x50]))
        self.assertEqual(bs.get_value(16, 7), 0x0)  # Not adopted
        bs.set_value(16, 7, 0x2)
        self.assertEqual(bs.to_bytearray(), mod)

    # Rain wiper
    def test_rain_wiper(self):
        mod = bytearray([0x00, 0x38, 0x10, 0x60, 0x50])
        bs = MCP_BCE_2(mod)
        self.assertEqual(bs.get_value(24, 3), 0x1)  # Off
        bs = MCP_BCE_2(bytearray([0x00, 0x38, 0x10, 0xa0, 0x50]))
        self.assertEqual(bs.get_value(24, 3), 0x2)  # On
        bs.set_value(24, 3, 0x1)
        self.assertEqual(bs.to_bytearray(), mod)

    # Interior light door open
    def test_interior_light_door_open(self):
        mod = bytearray([0x00, 0x28, 0x10, 0xa0, 0x50])
        bs = MCP_BCE_2(mod)
        self.assertEqual(bs.get_value(11, 3), 0x1)  # 30 mins
        bs = MCP_BCE_2(bytearray([0x00, 0x38, 0x10, 0xa0, 0x50]))
        self.assertEqual(bs.get_value(11, 3), 0x3)  # 10 mins
        bs.set_value(11, 3, 0x1)
        self.assertEqual(bs.to_bytearray(), mod)

    # Interior light door close
    def test_interior_light_door_close(self):
        mod = bytearray([0x00, 0x58, 0x10, 0xa0, 0x50])
        bs = MCP_BCE_2(mod)
        self.assertEqual(bs.get_value(8, 7), 0x2)  # 7.5s
        bs = MCP_BCE_2(bytearray([0x00, 0x38, 0x10, 0xa0, 0x50]))
        self.assertEqual(bs.get_value(8, 7), 0x1)  # 15 sec
        bs.set_value(8, 7, 0x2)
        self.assertEqual(bs.to_bytearray(), mod)

    # Coming light
    def test_coming_light(self):
        mod = bytearray([0x00, 0x38, 0x10, 0xa0, 0x70])
        bs = MCP_BCE_2(mod)
        self.assertEqual(bs.get_value(32, 7), 0x3)  # 30 mins
        bs = MCP_BCE_2(bytearray([0x00, 0x38, 0x10, 0xa0, 0x50]))
        self.assertEqual(bs.get_value(32, 7), 0x2)  # 10 mins
        bs.set_value(32, 7, 0x3)
        self.assertEqual(bs.to_bytearray(), mod)

    # Auto door lock
    def test_auto_door_lock(self):
        mod = bytearray([0x10, 0x38, 0x10, 0xa0, 0x50])
        bs = MCP_BCE_2(mod)
        self.assertEqual(bs.get_value(0, 15), 0x1)  # disabled
        bs = MCP_BCE_2(bytearray([0x00, 0x38, 0x10, 0xa0, 0x50]))
        self.assertEqual(bs.get_value(0, 15), 0x0)  # not adopted
        bs.set_value(0, 15, 0x1)
        self.assertEqual(bs.to_bytearray(), mod)

    # Leaving home light
    def test_leaving_home_light(self):
        mod = bytearray([0x00, 0x38, 0x10, 0xa0, 0x48])
        bs = MCP_BCE_2(mod)
        self.assertEqual(bs.get_value(35, 3), 0x1)  # off
        bs = MCP_BCE_2(bytearray([0x00, 0x38, 0x10, 0xa0, 0x50]))
        self.assertEqual(bs.get_value(35, 3), 0x2)  # on
        bs.set_value(35, 3, 0x1)
        self.assertEqual(bs.to_bytearray(), mod)