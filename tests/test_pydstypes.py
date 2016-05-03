#!/usr/bin/env python

# Fix Python 2.x.
from __future__ import print_function

_author__ = "Yann Diorcet"
__license__ = "GPL"
__version__ = "0.0.1"

import unittest
from pyds.pydstypes import MCP_BCE_2


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
    def test_coming_light(self):
        mod = bytearray([0x10, 0x38, 0x10, 0xa0, 0x50])
        bs = MCP_BCE_2(mod)
        self.assertEqual(bs.get_value(0, 15), 0x1)  # disabled
        bs = MCP_BCE_2(bytearray([0x00, 0x38, 0x10, 0xa0, 0x50]))
        self.assertEqual(bs.get_value(0, 15), 0x0)  # not adopted
        bs.set_value(0, 15, 0x1)
        self.assertEqual(bs.to_bytearray(), mod)


if __name__ == "__main__":
    suite = unittest.defaultTestLoader.loadTestsFromTestCase(MCP_BCE_2_Test)
    unittest.TextTestRunner().run(suite)
