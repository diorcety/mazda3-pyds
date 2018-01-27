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
from __future__ import print_function, division, absolute_import

__author__ = "Yann Diorcet"
__license__ = "GPL"
__version__ = "0.0.1"

try:
    input = raw_input
except NameError:
    input = input

import logging

import j2534
import uds

import pyds.secalgo
import pyds.extuds
import pyds.types

try:
    from peak.util.proxies import ObjectWrapper
except ImportError:
    from objproxies import ObjectWrapper

from enum import Enum
from cmd2 import Cmd

from pyds.structs import CanBus, SecurityType
from pyds.data import Vehicles, Mazda3_2015, vehicles_data
from pyds.actions import unlock_rbcm_features, unlock_ic_features

logger = logging.getLogger(__name__)


#
# Helpers
#


class Modes(Enum):
    normal = "Support MS-CAN & HS-CAN"
    hack = "Support MS-CAN as HS-CAN"

    def __str__(self):
        return self.name


def get_uds_channel(device, bus, mode, speed, tester, ecu):
    if bus == CanBus.MS:
        m = j2534.ISO15765_PS if mode == Modes.normal else j2534.ISO15765
        channel = device.connect(m, j2534.CAN_ID_BOTH, speed)
        if mode == Modes.normal:
            channel.setJ1962Pins(0x030B)
    else:
        if mode != Modes.normal:
            raise Exception("You can't use standard CAN bus with in the hack mode")
        channel = device.connect(j2534.ISO15765, j2534.CAN_ID_BOTH, speed)
    uds_j2534 = uds.UDS_J2534(channel, tester, ecu, j2534.ISO15765, j2534.ISO15765_FRAME_PAD)
    channel = pyds.extuds.ExtendedUDS(uds_j2534, False)
    return channel


class ModuleExtendedUDS(ObjectWrapper):
    def __init__(self, ob, vehicle, module):
        super(ModuleExtendedUDS, self).__init__(ob)
        self._vehicle = vehicle
        self._module = module

    @property
    def vehicle(self):
        return self._vehicle

    @property
    def module(self):
        return self._module


def get_module_channel(device, mode, vehicle, module):
    vd = vehicles_data[vehicle]
    md = vd.modules[module]
    bus = md.bus
    speed = vd.buses[bus]
    addr = module.value
    channel = get_uds_channel(device, bus, mode, speed, addr + 8, addr)
    return ModuleExtendedUDS(channel, vehicle, module)


def change_session(channel, conf=None):
    vd = vehicles_data[channel.vehicle]
    md = vd.modules[channel.module]
    if conf:
        security = md.security
        algo = security.algorithm
        conf = security.configurations[conf]
        session = conf.session
        level = conf.level
        key = conf.key

        # DSC
        channel.send_dsc(session)

        # SA
        if level:
            seed = channel.send_sa(level, bytearray())
            key = pyds.secalgo.get_security_algorithm(algo, key).compute(seed)
            channel.send_sa(level + 1, key)
    else:
        channel.send_dsc(uds.UDS_DSC_TYPES_DEFAULT_SESSION)
    return channel


#
# Actions
#

class PydsApp(Cmd):

    def __init__(self, device, mode):
        Cmd.__init__(self)
        self._device = device
        self._mode = mode

    # Disable optparse from original code
    def cmdloop(self, intro=None):
        # Always run the preloop first
        self.preloop()

        # If an intro was supplied in the method call, allow it to override the default
        if intro is not None:
            self.intro = intro

        # Print the intro, if there is one, right after the preloop
        if self.intro is not None:
            self.stdout.write(str(self.intro) + "\n")

        self._cmdloop()

        # Run the postloop() no matter what
        self.postloop()

    def get_module_channel(self, vehicle, module):
        return get_module_channel(self._device, self._mode, vehicle, module)

    def do_listen(self, args, vehicle, bus):
        vd = vehicles_data[vehicle]
        speed = vd.buses[bus]
        if bus == CanBus.MS:
            m = j2534.CAN_PS if self._mode == 'normal' else j2534.CAN
            channel = self._device.connect(m, j2534.CAN_ID_BOTH, speed)
            if self._mode == Modes.normal:
                channel.setJ1962Pins(0x030B)
        else:
            if self._mode != Modes.normal:
                raise Exception("You can't use standard CAN bus with in the hack mode")
            channel = self._device.connect(j2534.CAN, j2534.CAN_ID_BOTH, speed)
        vector = j2534.vector_passthru_msg()
        vector.resize(16)
        while True:
            read = channel.readMsgs(vector, 2000)
            print('Read %d messages' % (read))

    def do_info(self, args):
        channel = self.get_module_channel(Vehicles.Mazda3_2015, Mazda3_2015.RBCM)

        rbcm_de00_data = channel.send_rdbi(0xde00, 2000)
        print("RBCM 0xDE00 data(As-Built Data): %s" % (" ".join(['%02x' % (k) for k in rbcm_de00_data])))
        rbcm_de01_data = channel.send_rdbi(0xde01, 2000)
        print("RBCM 0xDE01 data(Configuration): %s" % (" ".join(['%02x' % (k) for k in rbcm_de01_data])))
        rbcm_dd01_data = channel.send_rdbi(0xdd01, 2000)
        print("RBCM 0xDD01 data(Millage): %s" % (" ".join(['%02x' % (k) for k in rbcm_dd01_data])))

        channel = self.get_module_channel(Vehicles.Mazda3_2015, Mazda3_2015.IC)
        ic_de00_data = channel.send_rdbi(0xde00, 2000)
        print("IC 0xDE00 ?: %s" % (" ".join(['%02x' % (k) for k in ic_de00_data])))
        ic_de01_data = channel.send_rdbi(0xde01, 2000)
        print("IC 0xDE01 ?: %s" % (" ".join(['%02x' % (k) for k in ic_de01_data])))
        ic_de02_data = channel.send_rdbi(0xde02, 2000)
        print("IC 0xDE02 ?: %s" % (" ".join(['%02x' % (k) for k in ic_de02_data])))
        ic_f106_data = channel.send_rdbi(0xf106, 2000)
        print("IC 0xF106 ?: %s" % (" ".join(['%02x' % (k) for k in ic_f106_data])))

    def do_unlock(self, args):
        def rbcm():
            channel = self.get_module_channel(Vehicles.Mazda3_2015, Mazda3_2015.RBCM)

            data = {
                0xde00: pyds.types.Normal(channel.send_rdbi(0xde00, 2000)),
                0xde01: pyds.types.MCP_BCE_2(channel.send_rdbi(0xde01, 2000))
            }

            channel = change_session(channel, SecurityType.Config)

            modified_data = unlock_rbcm_features(data)

            for did, diddata in modified_data.items():
                byte_array = diddata.to_bytearray()
                if data[did].to_bytearray() != byte_array:
                    channel.send_wdbi(did, byte_array, 500)

            channel.reset(uds.UDS_ER_TYPES_HARD_RESET)

        def ic():
            channel = self.get_module_channel(Vehicles.Mazda3_2015, Mazda3_2015.IC)

            data = {
                0xf106: pyds.types.Normal(channel.send_rdbi(0xf106, 2000)),
            }

            channel = change_session(channel, SecurityType.Config)

            modified_data = data
            #modified_data = unlock_ic_features(data)

            for did, diddata in modified_data.items():
                byte_array = diddata.to_bytearray()
                if True or data[did].to_bytearray() != byte_array:
                    channel.send_wdbi(did, byte_array, 500)

            channel.reset(uds.UDS_ER_TYPES_HARD_RESET)

        #rbcm()
        ic()

        print("Unlocks done!")

    def do_test(self, args):
        channel = self.get_module_channel(Vehicles.Mazda3_2015, Mazda3_2015.RBCM)

        data = {
            0xde00: pyds.types.Normal(channel.send_rdbi(0xde00, 2000)),
            0xde01: pyds.types.MCP_BCE_2(channel.send_rdbi(0xde01, 2000))
        }

        channel = change_session(channel, SecurityType.Config)

        # channel.send_wdbi(0xde00, bytearray([0x45, 0x50, 0x00, 0x06, 0xA1, 0xA5, 0x0C, 0x43, 0x00, 0x08, 0x00, 0x38, 0x92, 0x10]), 500)

        channel.reset(uds.UDS_ER_TYPES_HARD_RESET)

    def do_play(self, args):
        channel = self.get_module_channel(Vehicles.Mazda3_2015, Mazda3_2015.RBCM)
        channel = change_session(channel, SecurityType.IOControl)

        print("Will lock the doors")
        input("Press Enter to continue...")
        da70_obj_osc = pyds.types.Read(bytearray([0x0, 0x0, 0x0, 0x0, 0x0, 0x0, 0x0]))
        da70_obj_osc.set_value(16, 255, 4)  # Lock
        da70_mod_data = da70_obj_osc.to_bytearray()
        channel.send_iocbi(0xda70, uds.UDS_IOCBI_PARAMETERS_SHORT_TERM_ADJUSTMENT, da70_mod_data)
        channel.send_iocbi(0xda70, uds.UDS_IOCBI_PARAMETERS_RETURN_CONTROL_TO_ECU, bytearray([]))

        print("Will unlock the doors")
        input("Press Enter to continue...")
        da70_obj_osc = pyds.types.Read(bytearray([0x0, 0x0, 0x0, 0x0, 0x0, 0x0, 0x0]))
        da70_obj_osc.set_value(16, 255, 32)  # Unlock
        da70_mod_data = da70_obj_osc.to_bytearray()
        channel.send_iocbi(0xda70, uds.UDS_IOCBI_PARAMETERS_SHORT_TERM_ADJUSTMENT, da70_mod_data)
        channel.send_iocbi(0xda70, uds.UDS_IOCBI_PARAMETERS_RETURN_CONTROL_TO_ECU, bytearray([]))

        channel = change_session(channel, Mazda3_2015.RBCM)

    def do_dump(self, args):
        channel = self.get_module_channel(Vehicles.Mazda3_2015, Mazda3_2015.PCM)
        channel = change_session(channel, SecurityType.IOControl)

        # CDTCS Off
        channel.send_cdtcs(uds.UDS_CDTCS_ACTIONS_OFF)

        # Disable Rx and TX
        channel.send_cc(uds.UDS_CC_TYPES_DISABLE_RX_AND_TX, 0x1)

        # DSC
        channel = change_session(channel, SecurityType.Reprog)

        data = channel.upload((0xFFF88800, 4), (0x200000, 4))
        with open("c:\\temp\\dump.bin", 'wb') as file:
            file.write(data)

        channel = change_session(channel, SecurityType.IOControl)

        # DSC
        channel.send_dsc(uds.UDS_DSC_TYPES_EXTENDED_DIAGNOSTIC_SESSION)

        # CDTCS Off
        channel.send_cdtcs(uds.UDS_CDTCS_ACTIONS_ON)

        # Enable Rx and TX
        channel.send_cc(uds.UDS_CC_TYPES_ENABLE_RX_AND_TX, 0x1)

        channel = change_session(channel)
