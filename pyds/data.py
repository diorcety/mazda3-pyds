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

import uds

from enum import Enum
from pyds.structs import *


class Mazda3_2015(Enum):
    FSC = 0x706
    IC = 0x720
    EPS = 0x730
    SSU = 0x731
    EATC = 0x733
    RCM = 0x737
    PSM = 0x736
    ICA = 0x793
    RBCM = 0x7B7
    PCM = 0x7E0


class Vehicles(Enum):
    Mazda3_2015 = 0


vehicles_data = {
    Vehicles.Mazda3_2015: Vehicle(
        {
            CanBus.HS: 500000,
            CanBus.MS: 125000,
        },
        {
            Mazda3_2015.RBCM: Module(CanBus.MS, Security(Algorithm.Ford, {
                SecurityType.SelfTest: SecurityData(
                    0,
                    uds.UDS_DSC_TYPES_EXTENDED_DIAGNOSTIC_SESSION,
                    [0, 0, 0, 0, 0, 0]
                ),
                SecurityType.Config: SecurityData(
                    uds.UDS_SA_TYPES_SEED_2,
                    uds.UDS_DSC_TYPES_EXTENDED_DIAGNOSTIC_SESSION,
                    [75, 48, 50, 49, 54, 0]
                ),
                SecurityType.IOControl: SecurityData(
                    uds.UDS_SA_TYPES_SEED_2,
                    uds.UDS_DSC_TYPES_EXTENDED_DIAGNOSTIC_SESSION,
                    [75, 48, 50, 49, 54, 0]
                ),
            })),
            Mazda3_2015.PSM: Module(CanBus.MS, Security(Algorithm.Ford, {
                SecurityType.SelfTest: SecurityData(
                    0,
                    uds.UDS_DSC_TYPES_EXTENDED_DIAGNOSTIC_SESSION,
                    [0, 0, 0, 0, 0, 0]
                ),
                SecurityType.Config: SecurityData(
                    0,
                    uds.UDS_DSC_TYPES_EXTENDED_DIAGNOSTIC_SESSION,
                    [0, 0, 0, 0, 0, 0]
                ),
                SecurityType.IOControl: SecurityData(
                    0,
                    uds.UDS_DSC_TYPES_EXTENDED_DIAGNOSTIC_SESSION,
                    [0, 0, 0, 0, 0, 0]
                ),
            })),
            Mazda3_2015.EATC: Module(CanBus.MS, Security(Algorithm.Ford, {
                SecurityType.SelfTest: SecurityData(
                    0,
                    uds.UDS_DSC_TYPES_EXTENDED_DIAGNOSTIC_SESSION,
                    [0, 0, 0, 0, 0, 0]
                ),
                SecurityType.Config: SecurityData(
                    0,
                    uds.UDS_DSC_TYPES_EXTENDED_DIAGNOSTIC_SESSION,
                    [0, 0, 0, 0, 0, 0]
                ),
                SecurityType.IOControl: SecurityData(
                    0,
                    uds.UDS_DSC_TYPES_EXTENDED_DIAGNOSTIC_SESSION,
                    [0, 0, 0, 0, 0, 0]
                ),
            })),

            Mazda3_2015.EPS: Module(CanBus.HS, Security(Algorithm.Ford, {
                SecurityType.SelfTest: SecurityData(
                    0,
                    uds.UDS_DSC_TYPES_EXTENDED_DIAGNOSTIC_SESSION,
                    [0, 0, 0, 0, 0, 0]
                ),
                SecurityType.Config: SecurityData(
                    0,
                    uds.UDS_DSC_TYPES_EXTENDED_DIAGNOSTIC_SESSION,
                    [0, 0, 0, 0, 0, 0]
                ),
                SecurityType.IOControl: SecurityData(
                    0,
                    uds.UDS_DSC_TYPES_EXTENDED_DIAGNOSTIC_SESSION,
                    [0, 0, 0, 0, 0, 0]
                ),
            })),
            Mazda3_2015.ICA: Module(CanBus.HS, Security(Algorithm.Ford, {
                SecurityType.SelfTest: SecurityData(
                    0,
                    uds.UDS_DSC_TYPES_EXTENDED_DIAGNOSTIC_SESSION,
                    [0, 0, 0, 0, 0, 0]
                ),
                SecurityType.Config: SecurityData(
                    0,
                    uds.UDS_DSC_TYPES_EXTENDED_DIAGNOSTIC_SESSION,
                    [0, 0, 0, 0, 0, 0]
                ),
                SecurityType.IOControl: SecurityData(
                    0,
                    uds.UDS_DSC_TYPES_EXTENDED_DIAGNOSTIC_SESSION,
                    [0, 0, 0, 0, 0, 0]
                ),
            })),
            Mazda3_2015.RCM: Module(CanBus.HS, Security(Algorithm.Ford, {
                SecurityType.SelfTest: SecurityData(
                    0,
                    uds.UDS_DSC_TYPES_EXTENDED_DIAGNOSTIC_SESSION,
                    [0, 0, 0, 0, 0, 0]
                ),
                SecurityType.Config: SecurityData(
                    uds.UDS_SA_TYPES_SEED_2,
                    uds.UDS_DSC_TYPES_EXTENDED_DIAGNOSTIC_SESSION,
                    [74, 54, 49, 67, 70, 0]
                ),
                SecurityType.IOControl: SecurityData(
                    0,
                    uds.UDS_DSC_TYPES_EXTENDED_DIAGNOSTIC_SESSION,
                    [0, 0, 0, 0, 0, 0]
                ),
            })),
            Mazda3_2015.FSC: Module(CanBus.HS, Security(Algorithm.Ford, {
                SecurityType.SelfTest: SecurityData(
                    0,
                    uds.UDS_DSC_TYPES_EXTENDED_DIAGNOSTIC_SESSION,
                    [0, 0, 0, 0, 0, 0]
                ),
                SecurityType.Config: SecurityData(
                    uds.UDS_SA_TYPES_SEED_2,
                    uds.UDS_DSC_TYPES_EXTENDED_DIAGNOSTIC_SESSION,
                    [8, 8, 1, 3, 1, 0]
                ),
                SecurityType.IOControl: SecurityData(
                    0,
                    uds.UDS_DSC_TYPES_EXTENDED_DIAGNOSTIC_SESSION,
                    [0, 0, 0, 0, 0, 0]
                ),
            })),
            Mazda3_2015.IC: Module(CanBus.HS, Security(Algorithm.Ford, {
                SecurityType.SelfTest: SecurityData(
                    0,
                    uds.UDS_DSC_TYPES_EXTENDED_DIAGNOSTIC_SESSION,
                    [0, 0, 0, 0, 0, 0]
                ),
                SecurityType.Config: SecurityData(
                    uds.UDS_SA_TYPES_SEED_2,
                    uds.UDS_DSC_TYPES_EXTENDED_DIAGNOSTIC_SESSION,
                    [78, 83, 89, 78, 83, 0]
                ),
                SecurityType.IOControl: SecurityData(
                    uds.UDS_SA_TYPES_SEED_2,
                    uds.UDS_DSC_TYPES_EXTENDED_DIAGNOSTIC_SESSION,
                    [78, 83, 89, 78, 83, 0]
                ),
            })),
            Mazda3_2015.PCM: Module(CanBus.HS, Security(Algorithm.Ford, {
                SecurityType.Reprog: SecurityData(
                    uds.UDS_SA_TYPES_SEED,
                    uds.UDS_DSC_TYPES_PROGRAMMING_SESSION,
                    [73, 118, 102, 101, 82, 0]
                ),
                SecurityType.SelfTest: SecurityData(
                    0,
                    uds.UDS_DSC_TYPES_EXTENDED_DIAGNOSTIC_SESSION,
                    [0, 0, 0, 0, 0, 0]
                ),
                SecurityType.Config: SecurityData(
                    uds.UDS_SA_TYPES_SEED,
                    uds.UDS_DSC_TYPES_PROGRAMMING_SESSION,
                    [73, 118, 102, 101, 82, 0]
                ),
                SecurityType.IOControl: SecurityData(
                    uds.UDS_SA_TYPES_SEED_2,
                    uds.UDS_DSC_TYPES_EXTENDED_DIAGNOSTIC_SESSION,
                    [77, 97, 122, 100, 65, 0]
                ),
            })),
            Mazda3_2015.SSU: Module(CanBus.HS, Security(Algorithm.Ford, {
                SecurityType.SelfTest: SecurityData(
                    0,
                    uds.UDS_DSC_TYPES_EXTENDED_DIAGNOSTIC_SESSION,
                    [0, 0, 0, 0, 0, 0]
                ),
                SecurityType.Config: SecurityData(
                    uds.UDS_SA_TYPES_SEED,
                    uds.UDS_DSC_TYPES_PROGRAMMING_SESSION,
                    [84, 117, 188, 78, 104, 0]
                ),
                SecurityType.IOControl: SecurityData(
                    uds.UDS_SA_TYPES_SEED_2,
                    uds.UDS_DSC_TYPES_EXTENDED_DIAGNOSTIC_SESSION,
                    [84, 117, 188, 78, 104, 0]
                ),
            })),
        }
    )
}
