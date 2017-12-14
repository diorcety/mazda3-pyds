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
import logging

from collections import OrderedDict
from enum import Enum
from structs import CanBus, SecurityType
from data import Vehicles, Mazda3_2015, vehicles_data
from actions import unlock_rbcm_features

logger = logging.getLogger(__name__)


class Modes(Enum):
    normal = "Support MS-CAN & HS-CAN"
    hack = "Support MS-CAN as HS-CAN"

    def __str__(self):
        return self.value


def get_uds_channel(device, bus, mode, speed, tester, ecu):
    if bus == CanBus.MS:
        channel = device.connect(j2534.ISO15765_PS if mode == Modes.normal else j2534.ISO15765, j2534.CAN_ID_BOTH,
                                 speed)
        if mode == Modes.normal:
            channel.setJ1962Pins(0x030B)
    else:
        if mode != Modes.normal:
            raise Exception("You can't use standard CAN bus with in the hack mode")
        channel = device.connect(j2534.ISO15765, j2534.CAN_ID_BOTH, speed)
    uds_j2534 = uds.UDS_J2534(channel, tester, ecu, j2534.ISO15765, j2534.ISO15765_FRAME_PAD)
    uds_channel = extuds.ExtendedUDS(uds_j2534, False)
    return uds_channel


def get_module_channel(device, mode, vehicle, module):
    vd = vehicles_data[vehicle]
    md = vd.modules[module]
    bus = md.bus
    speed = vd.buses[bus]
    addr = module
    channel = get_uds_channel(device, bus, mode, speed, addr + 8, addr)
    return channel


def change_session(channel, vehicle, module, conf=None):
    vd = vehicles_data[vehicle]
    md = vd.modules[module]
    if conf:
        algo = md.algo
        conf = md.conf[conf]
        session = conf.session
        level = conf.level
        key = conf.key

        # DSC
        channel.send_dsc(session)

        # SA
        if level:
            seed = uds_channel.send_sa(level, bytearray())
            key = secalgo.getSecurityAlgorithm(algo, key).compute(seed)
            channel.send_sa(level + 1, key)
    else:
        channel.send_dsc(uds.UDS_DSC_TYPES_DEFAULT_SESSION)
    return channel


def listen(device, ps, mode, speed):
    if ps:
        channel = device.connect(j2534.CAN_PS if mode == 'normal' else j2534.CAN, j2534.CAN_ID_BOTH, speed)
        if mode == 'normal':
            channel.setJ1962Pins(0x030B)
    else:
        if mode != 'normal':
            raise Exception("You can't use standard CAN bus with in the hack mode")
        channel = device.connect(j2534.CAN, j2534.CAN_ID_BOTH, speed)
    vector = j2534.vector_passthru_msg()
    vector.resize(16)
    while True:
        read = channel.readMsgs(vector, 2000)
        print('Read %d messages' % (read))


def info(device, mode):
    uds_channel = get_module_channel(device, mode, Vehicles.Mazda3_2015, Mazda3_2015.RBCM)

    rbcm_de00_data = uds_channel.send_rdbi(0xde00, 2000)
    print("RBCM 0xDE00 data(As-Built Data): %s" % (" ".join(['%02x' % (k) for k in rbcm_de00_data])))
    rbcm_de01_data = uds_channel.send_rdbi(0xde01, 2000)
    print("RBCM 0xDE01 data(Configuration): %s" % (" ".join(['%02x' % (k) for k in rbcm_de01_data])))
    rbcm_dd01_data = uds_channel.send_rdbi(0xdd01, 2000)
    print("RBCM 0xDD01 data(Millage): %s" % (" ".join(['%02x' % (k) for k in rbcm_dd01_data])))

    uds_channel = get_module_channel(device, mode, Vehicles.Mazda3_2015, Mazda3_2015.IC)
    ic_de00_data = uds_channel.send_rdbi(0xde00, 2000)
    print("IC 0xDE00 ?: %s" % (" ".join(['%02x' % (k) for k in ic_de00_data])))
    ic_de01_data = uds_channel.send_rdbi(0xde01, 2000)
    print("IC 0xDE01 ?: %s" % (" ".join(['%02x' % (k) for k in ic_de01_data])))
    ic_de02_data = uds_channel.send_rdbi(0xde02, 2000)
    print("IC 0xDE02 ?: %s" % (" ".join(['%02x' % (k) for k in ic_de02_data])))
    ic_f106_data = uds_channel.send_rdbi(0xf106, 2000)
    print("IC 0xF106 ?: %s" % (" ".join(['%02x' % (k) for k in ic_f106_data])))
    

def unlock_rbcm(device, mode):
    uds_channel = get_module_channel(device, mode, Vehicles.Mazda3_2015, Mazda3_2015.RBCM)

    data = {}
    data[0xde00] = pydstypes.Normal(uds_channel.send_rdbi(0xde00, 2000))
    data[0xde01] = pydstypes.MCP_BCE_2(uds_channel.send_rdbi(0xde01, 2000))

    uds_channel = change_session(uds_channel, Vehicles.Mazda3_2015, Mazda3_2015.RBCM, SecurityType.Config)

    modified_data = unlock_rbcm_features(data)

    for did, diddata in modified_data.items():
        byte_array = diddata.to_bytearray()
        if data[did].to_bytearray() != byte_array:
            uds_channel.send_wdbi(did, byte_array, 500)

    uds_channel.reset(uds.UDS_ER_TYPES_HARD_RESET)
    print("Unlocks done!")


def test(device, mode):
    uds_channel = get_module_channel(device, mode, Vehicles.Mazda3_2015, Mazda3_2015.RBCM)

    data = {}
    data[0xde00] = pydstypes.Normal(uds_channel.send_rdbi(0xde00, 2000))
    data[0xde01] = pydstypes.MCP_BCE_2(uds_channel.send_rdbi(0xde01, 2000))

    uds_channel = change_session(uds_channel, Vehicles.Mazda3_2015, Mazda3_2015.RBCM, SecurityType.Config)

    # uds_channel.send_wdbi(0xde00, bytearray([0x45, 0x50, 0x00, 0x06, 0xA1, 0xA5, 0x0C, 0x43, 0x00, 0x08, 0x00, 0x38, 0x92, 0x10]), 500)

    uds_channel.reset(uds.UDS_ER_TYPES_HARD_RESET)


def play(device, mode):
    uds_channel = get_module_channel(device, mode, Vehicles.Mazda3_2015, Mazda3_2015.RBCM)
    uds_channel = change_session(uds_channel, Vehicles.Mazda3_2015, Mazda3_2015.RBCM, SecurityType.IOControl)

    print("Will lock the doors")
    input("Press Enter to continue...")
    da70_obj_osc = pydstypes.Read(bytearray([0x0, 0x0, 0x0, 0x0, 0x0, 0x0, 0x0]))
    da70_obj_osc.set_value(16, 255, 4)  # Lock
    da70_mod_data = da70_obj_osc.to_bytearray()
    uds_channel.send_iocbi(0xda70, uds.UDS_IOCBI_PARAMETERS_SHORT_TERM_ADJUSTMENT, da70_mod_data)
    uds_channel.send_iocbi(0xda70, uds.UDS_IOCBI_PARAMETERS_RETURN_CONTROL_TO_ECU, bytearray([]))

    print("Will unlock the doors")
    input("Press Enter to continue...")
    da70_obj_osc = pydstypes.Read(bytearray([0x0, 0x0, 0x0, 0x0, 0x0, 0x0, 0x0]))
    da70_obj_osc.set_value(16, 255, 32)  # Unlock
    da70_mod_data = da70_obj_osc.to_bytearray()
    uds_channel.send_iocbi(0xda70, uds.UDS_IOCBI_PARAMETERS_SHORT_TERM_ADJUSTMENT, da70_mod_data)
    uds_channel.send_iocbi(0xda70, uds.UDS_IOCBI_PARAMETERS_RETURN_CONTROL_TO_ECU, bytearray([]))

    uds_channel = change_session(uds_channel, Vehicles.Mazda3_2015, Mazda3_2015.RBCM)


def dump(device, mode):
    uds_channel = get_module_channel(device, mode, Vehicles.Mazda3_2015, Mazda3_2015.PCM)
    uds_channel = change_session(uds_channel, Vehicles.Mazda3_2015, Mazda3_2015.PCM, SecurityType.IOControl)

    # CDTCS Off
    uds_channel.send_cdtcs(uds.UDS_CDTCS_ACTIONS_OFF)

    # Disable Rx and TX
    uds_channel.send_cc(uds.UDS_CC_TYPES_DISABLE_RX_AND_TX, 0x1)

    # DSC
    uds_channel = change_session(uds_channel, Vehicles.Mazda3_2015, Mazda3_2015.PCM, SecurityType.Reprog)

    data = uds_channel.upload((0xFFF88800, 4), (0x200000, 4))
    with open("c:\\temp\\dump.bin", 'wb') as file:
        file.write(data)

    uds_channel = change_session(uds_channel, Vehicles.Mazda3_2015, Mazda3_2015.PCM, SecurityType.IOControl)

    # DSC
    uds_channel.send_dsc(uds.UDS_DSC_TYPES_EXTENDED_DIAGNOSTIC_SESSION)

    # CDTCS Off
    uds_channel.send_cdtcs(uds.UDS_CDTCS_ACTIONS_ON)

    # Enable Rx and TX
    uds_channel.send_cc(uds.UDS_CC_TYPES_ENABLE_RX_AND_TX, 0x1)

    uds_channel = change_session(uds_channel, Vehicles.Mazda3_2015, Mazda3_2015.PCM)


#
# Cli
#

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
    parser.add_argument('-v', '--verbose', dest='verbose_count', action='count', default=0,
                        help="increases log verbosity for each occurrence.")
    parser.add_argument('action', choices=['l', 'm', 'i', 'u', 'p', 't', 'd'], help="Action to do")
    parser.add_argument('-l', '--library', help="Library to use")
    # Add parameter for Windows platforms
    if sys.platform == 'win32':
        parser.add_argument('-d', '--device', help="Device to use")
    parser.add_argument('-m', '--mode', type=Modes, choices=list(Modes), help="Library mode")
    args = parser.parse_args(argv[1:])

    # Set logging level
    logging.getLogger().setLevel(max(3 - args.verbose_count, 0) * 10)

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
        listen(device, True, mode, 125000)
    elif args.action == 'm':
        listen(device, False, mode, 500000)
    elif args.action == 'i':
        info(device, mode)
    elif args.action == 'u':
        unlock_rbcm(device, mode)
    elif args.action == 'p':
        play(device, mode)
    elif args.action == 't':
        test(device, mode)
    elif args.action == 'd':
        dump(device, mode)
    else:
        parser.print_help()
        return -1
    return 0


if __name__ == "__main__":
    try:
        sys.exit(main(sys.argv))
    except Exception as e:
        sys.exit(-1)
    finally:
        logging.shutdown()
