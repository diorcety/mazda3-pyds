# Fix Python 2.x.
from __future__ import print_function

_author__ = "Yann Diorcet"
__license__ = "GPL"
__version__ = "0.0.1"

import math


class MCP_BCE_2(object):
    @staticmethod
    def _bytearraytobitarray(bytes):
        bits = []
        for x in bytes:
            for l in range(7, -1, -1):
                bits.append(x >> l & 0x1)
        return bits

    @staticmethod
    def _bitarraytobytearray(bits):
        # Add padding
        q = len(bits) % 8
        if q != 0:
            bits = bits[:]
            for i in range(0, q):
                bits.append(0)

        bytes = []
        byte = 0
        i = 0
        for x in bits:
            byte = (byte << 1) | (x & 0x1)
            i = i + 1
            if i == 8:
                i = 0
                bytes.append(byte)
                byte = 0
        return bytearray(bytes)

    @staticmethod
    def _value_to_bits(value, length):
        bits = []
        for x in range(length - 1, -1, -1):
            bits.append((value >> x) & 0x1)
        return bits

    @staticmethod
    def _bits_to_value(bits):
        value = 0
        for x in bits:
            value = (value << 1) | (x & 0x1)
        return value

    @staticmethod
    def _set_value(bits, offset, mask, value):
        bit_l = math.log(mask + 1, 2)
        if not bit_l.is_integer():
            raise Exception("Invalid mask %x" % (mask))
        bit_l = int(bit_l)
        bits[offset:(offset + bit_l)] = MCP_BCE_2._value_to_bits(value, bit_l)

    @staticmethod
    def _get_value(bits, offset, mask):
        bit_l = math.log(mask + 1, 2)
        if not bit_l.is_integer():
            raise Exception("Invalid mask %x" % (mask))
        bit_l = int(bit_l)
        return MCP_BCE_2._bits_to_value(bits[offset:(offset + bit_l)])

    def __init__(self, bytes):
        self.bits = self._bytearraytobitarray(bytes)

    def to_bytearray(self):
        return self._bitarraytobytearray(self.bits)

    def get_value(self, offset, mask):
        return self._get_value(self.bits, offset, mask)

    def set_value(self, offset, mask, value):
        self._set_value(self.bits, offset, mask, value)


def getObject(type, data):
    if type == 'MCP_BCE_2':
        return MCP_BCE_2(data)
    else:
        raise Exception("Invalid Type %d" % (type))
