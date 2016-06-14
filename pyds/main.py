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
import pydstypes
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
        try:
            passThruKey = self.winreg.OpenKey(self.winreg.HKEY_LOCAL_MACHINE, r'SOFTWARE\\PassThruSupport.04.04', 0,
                                              self.winreg.KEY_READ | self.winreg.KEY_ENUMERATE_SUB_KEYS)
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
            elif len(devices) > 1:
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


def listen(device):
    channel = device.connect(j2534.CAN, j2534.CAN_ID_BOTH, 125000)
    vector = j2534.vector_passthru_msg()
    vector.resize(16)
    while True:
        read = channel.readMsgs(vector, 2000)
        print('Read %d messages' % (read))


def dummy(device):
    vehicleSeed = bytearray([0x4B, 0x30, 0x32, 0x31, 0x36])
    channel = device.connect(j2534.ISO15765, j2534.CAN_ID_BOTH, 125000)
    udsChannel = extuds.ExtendedUDS(uds.UDS_J2534(channel, 0x7BF, 0x7B7, j2534.ISO15765, j2534.ISO15765_FRAME_PAD), False, True)
    de00Data = udsChannel.send_rdbi(0xde00, 2000)
    print("0xDE00 data: %s" % (" ".join(['%02x' % (k) for k in de00Data])))
    de01Data = udsChannel.send_rdbi(0xde01, 2000)
    de01Obj = pydstypes.MCP_BCE_2(de01Data)
    print("0xDE01 data: %s" % (" ".join(['%02x' % (k) for k in de01Data])))

    dd01Data = udsChannel.send_rdbi(0xdd01, 2000)
    dd01Obj = pydstypes.Read(dd01Data)
    print("0xDD01 data(Millage): %s" % (" ".join(['%02x' % (k) for k in dd01Data])))

    da70Data = udsChannel.send_rdbi(0xda70, 2000)
    da70Obj = pydstypes.Read(da70Data)
    print("0xDA70 data(Door): %s" % (" ".join(['%02x' % (k) for k in da70Data])))

    da7cData = udsChannel.send_rdbi(0xda7c, 2000)
    da7cObj = pydstypes.Read(da7cData)
    print("0xDA7C data(Horn): %s" % (" ".join(['%02x' % (k) for k in da7cData])))

    print("Will enter in secure mode")
    input("Press Enter to continue...")

    
    # DSC

    udsChannel.send_dsc(uds.UDS_DSC_TYPES_EXTENDED_DIAGNOSTIC_SESSION)

    # SA

    seed = udsChannel.send_sa(uds.UDS_SA_TYPES_SEED_2, bytearray())
    key = secalgo.getSecurityAlgorithm(70, vehicleSeed).compute(seed)
    udsChannel.send_sa(uds.UDS_SA_TYPES_KEY_2, key)
    
    
    '''
    print("Will change As-Data configuration")
    input("Press Enter to continue...")
    de00ModData = bytearray([0x45, 0x50, 0x00, 0x06, 0xA1, 0xA5, 0x0C, 0x43, 0x00, 0x00, 0x00, 0x38, 0x92, 0x10])
    udsChannel.send_wdbi(0xde00, de00ModData, 500)

    udsChannel.reset(uds.UDS_ER_TYPES_HARD_RESET)
    '''
    

    '''
    print("Will lock the doors")
    input("Press Enter to continue...")
    da70ObjOsc = pydstypes.Read(bytearray([0x0, 0x0, 0x0, 0x0, 0x0, 0x0, 0x0]))
    da70ObjOsc.set_value(16, 255, 4) # Lock
    da70ModData = da70ObjOsc.to_bytearray()
    udsChannel.send_iocbi(0xda70, uds.UDS_IOCBI_PARAMETERS_SHORT_TERM_ADJUSTMENT, da70ModData)
    udsChannel.send_iocbi(0xda70, uds.UDS_IOCBI_PARAMETERS_RETURN_CONTROL_TO_ECU, bytearray([]))

    print("Will unlock the doors")
    input("Press Enter to continue...")
    da70ObjOsc = pydstypes.Read(bytearray([0x0, 0x0, 0x0, 0x0, 0x0, 0x0, 0x0]))
    da70ObjOsc.set_value(16, 255, 32) # Unlock
    da70ModData = da70ObjOsc.to_bytearray()
    udsChannel.send_iocbi(0xda70, uds.UDS_IOCBI_PARAMETERS_SHORT_TERM_ADJUSTMENT, da70ModData)
    udsChannel.send_iocbi(0xda70, uds.UDS_IOCBI_PARAMETERS_RETURN_CONTROL_TO_ECU, bytearray([]))
    '''

    # Default
    # de00ModData = bytearray([0x45, 0x50, 0x00, 0x06, 0xA1, 0xA5, 0x0C, 0x43, 0x00, 0x08, 0x00, 0x38, 0x92, 0x10])
    # Modified
    # de00ModData = bytearray([0x45, 0x50, 0x00, 0x06, 0xA1, 0xE5, 0x0C, 0x43, 0x00, 0x20, 0x00, 0x38, 0x92, 0x10])
    # udsChannel.send_wdbi(0xde00, de00ModData)

    # Default
    # de01ModData = bytearray([0x00, 0x38, 0x10, 0xa0, 0x50])
    # udsChannel.send_wdbi(0xde01, de01ModData)

    '''
    print("Will Set to light the headlight sensor")
    input("Press Enter to continue...")

    # Light
    de01Obj.set_value(26, 7, 0x5)
    de01ModData = de01Obj.to_bytearray()
    udsChannel.send_wdbi(0xde01, de01ModData)

    print("Will Set to medium light the headlight sensor")
    input("Press Enter to continue...")

    # Medium Light
    de01Obj.set_value(26, 7, 0x4)
    de01ModData = de01Obj.to_bytearray()
    udsChannel.send_wdbi(0xde01, de01ModData)
    '''

    '''
    print("Will disable 3 flash")
    input("Press Enter to continue...")

    # Disable
    de01Obj.set_value(19, 3, 0x1)
    de01ModData = de01Obj.to_bytearray()
    udsChannel.send_wdbi(0xde01, de01ModData)

    print("Will enable 3 flash")
    input("Press Enter to continue...")

    # Enable
    de01Obj.set_value(19, 3, 0x2)
    de01ModData = de01Obj.to_bytearray()
    udsChannel.send_wdbi(0xde01, de01ModData)
    '''

    
    print("Will disable autodoor lock")
    input("Press Enter to continue...")

    # Disable
    de01Obj.set_value(0, 15, 0x1)
    de01ModData = de01Obj.to_bytearray()
    udsChannel.send_wdbi(0xde01, de01ModData)
    
    


def main(argv):
    parser = argparse.ArgumentParser(description="PYthon iDS tool")
    parser.add_argument('-a', '--action', help="Action to do")
    parser.add_argument('-l', '--library', help="Library to use")
    # Add parameter for Windows platforms
    if sys.platform == 'win32':
        parser.add_argument('-d', '--device', help="Device to use")
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
    library = j2534.loadJ2534Library(libraryPath)
    device = library.open(None)
    (firmwareVersion, dllVersion, apiVersion) = device.readVersion()
    print("Firmware version: %s" % (firmwareVersion))
    print("DLL version:      %s" % (dllVersion))
    print("API version:      %s" % (apiVersion))
    print("\n\n")

    if args.action == 'l':
        listen(device)
    else:
        dummy(device)


if __name__ == "__main__":
    main(sys.argv)
