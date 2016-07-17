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
import copy
from collections import OrderedDict


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
                print("")
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
                        print("")
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

modes = OrderedDict()
modes['normal'] = "Support MS-CAN & HS-CAN"
modes['hack'] = "Support MS-CAN as HS-CAN"

def getMode(mode):
    if mode in modes:
        return mode

    print("")
    while True:
        index = 0
        for mode, description in modes.items():
            print("%d - %s" % (index, description))
            index = index + 1
        mode_index_str = input("Select your mode: ")
        try:
            mode_index = int(mode_index_str)
            if mode_index < 0 or mode_index >= len(modes):
                raise Exception("Invalid index")
            mode = modes.keys()[mode_index]
            print("")
            return mode
        except Exception as e:
            print("Invalid selection")

def listen(device, mode):
    channel = device.connect(j2534.CAN_PS if mode == 'normal' else j2534.CAN, j2534.CAN_ID_BOTH, 125000)
    if mode == 'normal':
        channel.setJ1962Pins(0x030B)
    vector = j2534.vector_passthru_msg()
    vector.resize(16)
    while True:
        read = channel.readMsgs(vector, 2000)
        print('Read %d messages' % (read))

def unlock_features(data):
    data = copy.deepcopy(data)
    unlock_autodoorlock(data)
    #unlock_healightofftimer(data) # Not working, something missing
    return data

def unlock_healightofftimer(data):
    locked = False
    
    assert len(data[0xde00]) == (14 * 8)
    assert len(data[0xde01]) == (5 * 8)

    if data[0xde00].get_value(0xB*8 + 4, 1) != 0x0:
        locked = True
        data[0xde00].set_value(0xB*8 + 4, 1, 0x0)

    if locked:
        print("Unlock \"head light off timer\"")
        if data[0xde01].get_value(16, 7) == 0:
            print("Set \"head light off timer\" default value (30s)")
            # 30s
            data[0xde01].set_value(16, 7, 0x2)
    else:
        print("\"head light off timer\" seems already unlocked")

def unlock_autodoorlock(data):
    locked = False
    
    assert len(data[0xde00]) == (14 * 8)
    assert len(data[0xde01]) == (5 * 8)

    if data[0xde00].get_value(0x1*8 + 7, 1) != 0x1:
        locked = True
        data[0xde00].set_value(0x1*8 + 7, 1, 0x1)

    if data[0xde00].get_value(0x9*8 + 3, 1) != 0x0:
        locked = True
        data[0xde00].set_value(0x9*8 + 3, 1, 0x0)

    if data[0xde00].get_value(0x9*8 + 4, 7) != 0x2:
        locked = True
        data[0xde00].set_value(0x9*8 + 4, 7, 0x2)

    if locked:
        print("Unlock \"auto door lock\"")
        if data[0xde01].get_value(0, 15) == 0:
            print("Set \"auto door lock\" default value (Disabled)")
            # Disable
            data[0xde01].set_value(0, 15, 0x1)
    else:
        print("\"auto door lock\" seems already unlocked")

def getUdsChannel(device, mode, speed, tester, ecu):
    channel = device.connect(j2534.ISO15765_PS if mode == 'normal' else j2534.ISO15765, j2534.CAN_ID_BOTH, speed)
    if mode == 'normal':
        channel.setJ1962Pins(0x030B)
    udsChannel = extuds.ExtendedUDS(uds.UDS_J2534(channel, tester, ecu, j2534.ISO15765, j2534.ISO15765_FRAME_PAD), False, False)
    return udsChannel

def info(device, mode):
    udsChannel = getUdsChannel(device, mode, 125000, 0x7BF, 0x7B7)

    de00Data = udsChannel.send_rdbi(0xde00, 2000)
    print("0xDE00 data(As-Built Data): %s" % (" ".join(['%02x' % (k) for k in de00Data])))
    de01Data = udsChannel.send_rdbi(0xde01, 2000)
    print("0xDE01 data(Configuration): %s" % (" ".join(['%02x' % (k) for k in de01Data])))
    dd01Data = udsChannel.send_rdbi(0xdd01, 2000)
    print("0xDD01 data(Millage): %s" % (" ".join(['%02x' % (k) for k in dd01Data])))

def unlock(device, mode):
    udsChannel = getUdsChannel(device, mode, 125000, 0x7BF, 0x7B7)

    data = {}
    data[0xde00] = pydstypes.Normal(udsChannel.send_rdbi(0xde00, 2000))
    data[0xde01] = pydstypes.MCP_BCE_2(udsChannel.send_rdbi(0xde01, 2000))

    # DSC
    udsChannel.send_dsc(uds.UDS_DSC_TYPES_EXTENDED_DIAGNOSTIC_SESSION)

    # SA
    vehicleSeed = bytearray([0x4B, 0x30, 0x32, 0x31, 0x36])
    seed = udsChannel.send_sa(uds.UDS_SA_TYPES_SEED_2, bytearray())
    key = secalgo.getSecurityAlgorithm(70, vehicleSeed).compute(seed)
    udsChannel.send_sa(uds.UDS_SA_TYPES_KEY_2, key)

    modified_data = unlock_features(data)

    for did, diddata in modified_data.items():
        byte_array = diddata.to_bytearray()
        if data[did].to_bytearray() != byte_array:
            udsChannel.send_wdbi(did, byte_array, 500)

    udsChannel.reset(uds.UDS_ER_TYPES_HARD_RESET)
    print("Unlocks done!")
    
    
def test(device, mode):
    udsChannel = getUdsChannel(device, mode, 125000, 0x7BF, 0x7B7)

    data = {}
    data[0xde00] = pydstypes.Normal(udsChannel.send_rdbi(0xde00, 2000))
    data[0xde01] = pydstypes.MCP_BCE_2(udsChannel.send_rdbi(0xde01, 2000))

    # DSC
    udsChannel.send_dsc(uds.UDS_DSC_TYPES_EXTENDED_DIAGNOSTIC_SESSION)

    # SA
    vehicleSeed = bytearray([0x4B, 0x30, 0x32, 0x31, 0x36])
    seed = udsChannel.send_sa(uds.UDS_SA_TYPES_SEED_2, bytearray())
    key = secalgo.getSecurityAlgorithm(70, vehicleSeed).compute(seed)
    udsChannel.send_sa(uds.UDS_SA_TYPES_KEY_2, key)

    udsChannel.send_wdbi(0xde00, bytearray([0x45, 0x50, 0x00, 0x06, 0xA1, 0xA5, 0x0C, 0x43, 0x00, 0x08, 0x00, 0x38, 0x92, 0x10]), 500)

    udsChannel.reset(uds.UDS_ER_TYPES_HARD_RESET)

def play(device, mode):
    udsChannel = getUdsChannel(device, mode, 125000, 0x7BF, 0x7B7)

    # DSC
    udsChannel.send_dsc(uds.UDS_DSC_TYPES_EXTENDED_DIAGNOSTIC_SESSION)

    # SA
    vehicleSeed = bytearray([0x4B, 0x30, 0x32, 0x31, 0x36])
    seed = udsChannel.send_sa(uds.UDS_SA_TYPES_SEED_2, bytearray())
    key = secalgo.getSecurityAlgorithm(70, vehicleSeed).compute(seed)
    udsChannel.send_sa(uds.UDS_SA_TYPES_KEY_2, key)

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

def main(argv):
    print(
        "###############################################################################" + "\n" +
        "# This program is distributed in the hope that it will be useful, but WITHOUT #" + "\n" +
        "# ANY WARRANTY; without even the implied warranty of MERCHANTABILITY or       #" + "\n" +
        "# FITNESS FOR A PARTICULAR PURPOSE.  See the GNU General Public License for   #" + "\n" +
        "# more details.                                                               #" + "\n" +
        "###############################################################################" + "\n"
    )
    parser = argparse.ArgumentParser(description="PYthon iDS tool")
    parser.add_argument('action', choices=['l', 'i', 'u', 'p', 't'], help="Action to do")
    parser.add_argument('-l', '--library', help="Library to use")
    # Add parameter for Windows platforms
    if sys.platform == 'win32':
        parser.add_argument('-d', '--device', help="Device to use")
    parser.add_argument('-m', '--mode', choices=modes.keys(), help="Library mode")
    args = parser.parse_args(argv[1:])

    # Library
    libraryPath = args.library
    if libraryPath is None:
        if sys.platform == 'win32':
            discover = WinDiscover()
            device = args.device
            libraryPath = discover.getLibrary(device)
    if libraryPath is None:
        raise Exception("No library or device provided")

    # Mode
    mode = getMode(args.mode)

    # Print information
    print("Library Path:     %s" % (libraryPath))
    library = j2534.J2534Library(libraryPath)
    device = library.open(None)
    (firmwareVersion, dllVersion, apiVersion) = device.readVersion()
    print("Firmware version: %s" % (firmwareVersion))
    print("DLL version:      %s" % (dllVersion))
    print("API version:      %s" % (apiVersion))
    print("Mode:             %s" % (modes[mode]))
    print("\n\n")

    if args.action == 'l':
        listen(device, mode)
    elif args.action == 'i':
        info(device, mode)
    elif args.action == 'u':
        unlock(device, mode)
    elif args.action == 'p':
        play(device, mode)
    elif args.action == 't':
        test(device, mode)
    else:
        parser.print_help()
        sys.exit(1)

if __name__ == "__main__":
    main(sys.argv)
