#!/usr/bin/env python

# Fix Python 2.x.
from __future__ import print_function

try:
    input = raw_input
except NameError:
    input = input

import argparse
import sys
import j2534
import uds
import struct
import seedkey
import math


##
## For Windows platforms
##
class WinDiscover:
    def __init__(self):
        try:
            import winreg
            self.winreg = winreg
        except ImportError:
            import _winreg
            self.winreg = _winreg

    def listPassThruDevices(self):
        devices = []
        passThruKey = self.winreg.OpenKey(self.winreg.HKEY_LOCAL_MACHINE, r'SOFTWARE\\PassThruSupport.04.04', 0,
                                          self.winreg.KEY_READ | self.winreg.KEY_ENUMERATE_SUB_KEYS)
        try:
            i = 0
            while True:
                devices.append(self.winreg.EnumKey(passThruKey, i))
                i += 1
        except WindowsError:
            pass
        return devices

    def getPassThruDeviceLibrary(self, device):
        passThruDeviceKey = self.winreg.OpenKey(self.winreg.HKEY_LOCAL_MACHINE,
                                                r'SOFTWARE\\PassThruSupport.04.04\\' + device, 0,
                                                self.winreg.KEY_READ | self.winreg.KEY_ENUMERATE_SUB_KEYS)
        return self.winreg.QueryValueEx(passThruDeviceKey, r'FunctionLibrary')[0]

    def getLibrary(self, device):
        devices = self.listPassThruDevices()
        if device is None:
            if len(devices) == 1:
                device = devices[0]
            else:
                while True:
                    index = 0
                    for device in devices:
                        print("%d - %s" % (index, device))
                        index = index + 1
                    dev_index_str = input("Select your device: ")
                    try:
                        dev_index = int(dev_index_str)
                        if dev_index < 0 or dev_index >= len(devices):
                            raise Exception("Invalid index")
                        device = devices[dev_index]
                        break
                    except Exception:
                        print("Invalid selection")
            if device is None:
                raise Exception("No J2534 device available")
        print("Device:           %s" % (device))
        try:
            return self.getPassThruDeviceLibrary(device).encode('utf-8')
        except WindowsError:
            raise Exception("Device \"%s\" not found" % (device))


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

    def grant_security_access(self, vehicleSeed):
        type = bytearray([uds.UDS_SA_TYPES_SEED_2])
        seed_reply = self.send(uds.UDS_SERVICE_SA, type)
        seed_reply_data = seed_reply.getData()
        reply_type = self.slice_data(seed_reply_data, uds, 'UDS_SA_TYPE')
        if type != reply_type:
            raise Exception("Invalid type %d for a request of type %d" % (type[0], reply_type[0]))
        sessionSeed = seed_reply_data[uds.UDS_SA_SEED_OFFSET:]
        key = seedkey.calculateKey(vehicleSeed, sessionSeed)
        type = bytearray([uds.UDS_SA_TYPES_KEY_2])
        key_reply = self.send(uds.UDS_SERVICE_SA, type + key)
        key_reply_data = key_reply.getData()
        reply_type = self.slice_data(key_reply_data, uds, 'UDS_SA_TYPE')
        if type != reply_type:
            raise Exception("Invalid type %d for a request of type %d" % (type[0], reply_type[0]))


def check():
    data = [0x00, 0x38, 0x08, 0xa0, 0x50]
    assert BitStream._bitarraytobytearray(BitStream._bytearraytobitarray(data)) == data

    # 3 Flash Turn
    mod = [0x00, 0x38, 0x08, 0xa0, 0x50]
    bs = BitStream(bytearray(mod))
    assert bs.get_value(19, 3) == 0x1  # Off
    bs = BitStream(bytearray([0x00, 0x38, 0x10, 0xa0, 0x50]))
    assert bs.get_value(19, 3) == 0x2  # On
    bs.set_value(19, 3, 0x1)
    assert bs.to_bytearray() == mod

    # Head light
    mod = [0x00, 0x38, 0x10, 0xa8, 0x50]
    bs = BitStream(bytearray(mod))
    assert bs.get_value(26, 7) == 0x5  # Light
    bs = BitStream(bytearray([0x00, 0x38, 0x10, 0xa0, 0x50]))
    assert bs.get_value(26, 7) == 0x4  # Medium Light
    bs.set_value(26, 7, 0x5)
    assert bs.to_bytearray() == mod

    # Head light off timer
    mod = [0x00, 0x38, 0x50, 0xa0, 0x50]
    bs = BitStream(bytearray(mod))
    assert bs.get_value(16, 7) == 0x2  # 30s
    bs = BitStream(bytearray([0x00, 0x38, 0x10, 0xa0, 0x50]))
    assert bs.get_value(16, 7) == 0x0  # Not adopted
    bs.set_value(16, 7, 0x2)
    assert bs.to_bytearray() == mod

    # Rain wiper
    mod = [0x00, 0x38, 0x10, 0x60, 0x50]
    bs = BitStream(bytearray(mod))
    assert bs.get_value(24, 3) == 0x1  # Off
    bs = BitStream(bytearray([0x00, 0x38, 0x10, 0xa0, 0x50]))
    assert bs.get_value(24, 3) == 0x2  # On
    bs.set_value(24, 3, 0x1)
    assert bs.to_bytearray() == mod

    # Interior light door open
    mod = [0x00, 0x28, 0x10, 0xa0, 0x50]
    bs = BitStream(bytearray(mod))
    assert bs.get_value(11, 3) == 0x1  # 30 mins
    bs = BitStream(bytearray([0x00, 0x38, 0x10, 0xa0, 0x50]))
    assert bs.get_value(11, 3) == 0x3  # 10 mins
    bs.set_value(11, 3, 0x1)
    assert bs.to_bytearray() == mod

    # Coming light
    mod = [0x00, 0x38, 0x10, 0xa0, 0x70]
    bs = BitStream(bytearray(mod))
    assert bs.get_value(32, 7) == 0x3  # 30 mins
    bs = BitStream(bytearray([0x00, 0x38, 0x10, 0xa0, 0x50]))
    assert bs.get_value(32, 7) == 0x2  # 10 mins
    bs.set_value(32, 7, 0x3)
    assert bs.to_bytearray() == mod


def main(argv):
    check()

    parser = argparse.ArgumentParser(description="J2534 tool.")
    parser.add_argument('-library', '--library', help="Library to use")
    # Add parameter for Windows platforms
    if sys.platform == 'win32':
        parser.add_argument('-device', '--device', help="Device to use")
    args = parser.parse_args(argv[1:])

    libraryPath = args.library
    if libraryPath is None:
        if sys.platform == 'win32':
            discover = WinDiscover()
            device = args.device
            libraryPath = discover.getLibrary(device)
    if libraryPath is None:
        raise Exception("No library or device provided")

    # Print information
    print("Library Path:     %s" % (libraryPath))
    library = j2534.J2534Library(libraryPath)
    device = library.open(None)
    (firmwareVersion, dllVersion, apiVersion) = device.readVersion()
    print("Firmware version: %s" % (firmwareVersion))
    print("DLL version:      %s" % (dllVersion))
    print("API version:      %s" % (apiVersion))
    print("\n\n")

    vehicleSeed = bytearray([0x4B, 0x30, 0x32, 0x31, 0x36])
    channel = device.connect(j2534.ISO15765, j2534.CAN_ID_BOTH, 125000)
    udsChannel = ExtendedUDS(uds.UDS_J2534(channel, 0x7BF, 0x07B7, j2534.ISO15765, j2534.ISO15765_FRAME_PAD))
    de01Data = udsChannel.send_rdbi(0xde01, 2000)
    print("0xDE01 data: %s" % (" ".join(['%02x' % (k) for k in de01Data])))

    return


if __name__ == "__main__":
    main(sys.argv)
