#!/usr/bin/env python

# Fix Python 2.x.
from __future__ import print_function

_author__ = "Yann Diorcet"
__license__ = "GPL"
__version__ = "0.0.1"

try:
    input = raw_input
except NameError:
    input = input

import argparse
import sys
import j2534
import uds
import secalgo
import extuds
import ids

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

def main(argv):
    parser = argparse.ArgumentParser(description="PYthon iDS tool")
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
    udsChannel = extuds.ExtendedUDS(uds.UDS_J2534(channel, 0x7BF, 0x07B7, j2534.ISO15765, j2534.ISO15765_FRAME_PAD))
    de01Data = udsChannel.send_rdbi(0xde01, 2000)
    print("0xDE01 data: %s" % (" ".join(['%02x' % (k) for k in de01Data])))

    return


if __name__ == "__main__":
    main(sys.argv)
