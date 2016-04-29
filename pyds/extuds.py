#!/usr/bin/env python

# Fix Python 2.x.
from __future__ import print_function

_author__ = "Yann Diorcet"
__license__ = "GPL"
__version__ = "0.0.1"

import math
import struct
import uds

class BitStream(object):
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
        return bytes

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
        bits[offset:(offset + bit_l)] = BitStream._value_to_bits(value, bit_l)

    @staticmethod
    def _get_value(bits, offset, mask):
        bit_l = math.log(mask + 1, 2)
        if not bit_l.is_integer():
            raise Exception("Invalid mask %x" % (mask))
        bit_l = int(bit_l)
        return BitStream._bits_to_value(bits[offset:(offset + bit_l)])

    def __init__(self, bytes):
        self.bits = self._bytearraytobitarray(bytes)

    def to_bytearray(self):
        return self._bitarraytobytearray(self.bits)

    def get_value(self, offset, mask):
        return self._get_value(self.bits, offset, mask)

    def set_value(self, offset, mask, value):
        self._set_value(self.bits, offset, mask, value)


class NegativeResponseException(Exception):
    def __init__(self, reply):
        self.reply = reply

    def __str__(self):
        return "Error %d for service %d" % (self.reply.getErrorCode(), self.reply.getRequestServiceID())

class ExtendedUDS(object):
    def __init__(self, udsChannel, step_by_step=True, debug=True):
        self.step_by_step = True
        self.debug = debug
        self.udsChannel = udsChannel

    @staticmethod
    def int16tobytes(number):
        return struct.pack("<H", number)

    @staticmethod
    def bytestoint16(bytes):
        return struct.unpack("<H", bytes)[0]

    def slice_data(data, module, field, offset_str='_OFFSET', len_str='_LEN'):
        offset = getattr(module, field + offset_str)
        len = getattr(module, field + len_str)
        return data[offset:(offset + len)]

    def send(self, sid, data, timeout=2000):
        fdata = bytearray([sid])
        fdata.extend(data)
        message = uds.UDSMessage(fdata)
        if self.step_by_step:
            print("Will send: %s" % (" ".join(['%02x' % (k) for k in fdata])))
            response = input("Are you sure to send this? ")
            if response != 'YES':
                raise Exception("Interrupted by the user")
        if self.debug:
            print("Sending: %s" % (" ".join(['%02x' % (k) for k in fdata])))
        reply = self.udsChannel.send(message, timeout)
        if self.debug:
            print("Received: %s" % (" ".join(['%02x' % (k) for k in reply.getData()])))
        if isinstance(reply, uds.UDSNegativeResponseMessage):
            raise NegativeResponseException(reply)
        if reply.getServiceID() != (sid | uds.UDS_REPLY_MASK):
            raise Exception("Invalid reply %d for a request of type %d" % (reply.getServiceID(), sid))
        return reply

    def send_rdbi(self, did, timeout=2000):
        reply = self.send(uds.UDS_SERVICE_RDBI, self.int16tobytes(did), timeout)
        data = reply.getData()
        rdid = self.bytestoint16(self.slice_data(data, uds, 'UDS_RDBI_DATA_IDENTIFIER'))
        if rdid != did:
            raise Exception("Invalid dataIdentifier %d for a request of type %d" % (rdid, did))
        return data[uds.UDS_RDBI_DATA_RECORD_OFFSET:]

    def send_wdbi(self, did, data, timeout=2000):
        reply = self.send(uds.UDS_SERVICE_WDBI, self.int16tobytes(did) + data, timeout)
        data = reply.getData()
        rdid = self.bytestoint16(self.slice_data(data, uds, 'UDS_WDBI_DATA_IDENTIFIER'))
        if rdid != did:
            raise Exception("Invalid dataIdentifier %d for a request of type %d" % (rdid, did))
        return data[uds.UDS_RDBI_DATA_RECORD_OFFSET:]

    def change_diagnostic_session(self, sessionType):
        type = bytearray([sessionType])
        reply = self.send(uds.UDS_SERVICE_DSC, type)
        reply_data = reply.getData()
        reply_type = self.slice_data(reply_data, uds, 'UDS_DSC_SESSION_TYPE')
        if type != reply_type:
            raise Exception("Invalid type %d for a request of type %d" % (type[0], reply_type[0]))

    def grant_security_access(self, algo):
        type = bytearray([uds.UDS_SA_TYPES_SEED_2])
        seed_reply = self.send(uds.UDS_SERVICE_SA, type)
        seed_reply_data = seed_reply.getData()
        reply_type = self.slice_data(seed_reply_data, uds, 'UDS_SA_TYPE')
        if type != reply_type:
            raise Exception("Invalid type %d for a request of type %d" % (type[0], reply_type[0]))
        sessionSeed = seed_reply_data[uds.UDS_SA_SEED_OFFSET:]
        key = algo.compute(sessionSeed)
        type = bytearray([uds.UDS_SA_TYPES_KEY_2])
        key_reply = self.send(uds.UDS_SERVICE_SA, type + key)
        key_reply_data = key_reply.getData()
        reply_type = self.slice_data(key_reply_data, uds, 'UDS_SA_TYPE')
        if type != reply_type:
            raise Exception("Invalid type %d for a request of type %d" % (type[0], reply_type[0]))