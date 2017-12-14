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

import copy
import logging

logger = logging.getLogger(__name__)


def unlock_headlightofftimer(data):
    locked = False

    assert len(data[0xde00]) == (14 * 8)
    assert len(data[0xde01]) == (5 * 8)

    if data[0xde00].get_value(0xB * 8 + 4, 1) != 0x0:
        locked = True
        data[0xde00].set_value(0xB * 8 + 4, 1, 0x0)

    if locked:
        logger.info("Unlock \"head light off timer\"")
        if data[0xde01].get_value(16, 7) == 0:
            logger.info("Set \"head light off timer\" default value (30s)")
            # 30s
            data[0xde01].set_value(16, 7, 0x2)
    else:
        logger.info("\"head light off timer\" seems already unlocked")


def unlock_autodoorlock(data):
    locked = False

    assert len(data[0xde00]) == (14 * 8)
    assert len(data[0xde01]) == (5 * 8)

    if data[0xde00].get_value(0x1 * 8 + 7, 1) != 0x1:
        locked = True
        data[0xde00].set_value(0x1 * 8 + 7, 1, 0x1)

    if data[0xde00].get_value(0x9 * 8 + 3, 1) != 0x0:
        locked = True
        data[0xde00].set_value(0x9 * 8 + 3, 1, 0x0)

    if data[0xde00].get_value(0x9 * 8 + 4, 7) != 0x2:
        locked = True
        data[0xde00].set_value(0x9 * 8 + 4, 7, 0x2)

    if locked:
        logger.info("Unlock \"auto door lock\"")
        if data[0xde01].get_value(0, 15) == 0:
            logger.info("Set \"auto door lock\" default value (Disabled)")
            # Disable
            data[0xde01].set_value(0, 15, 0x1)
    else:
        logger.info("\"auto door lock\" seems already unlocked")


def unlock_rbcm_features(data):
    data = copy.deepcopy(data)
    unlock_autodoorlock(data)
    # unlock_headlightofftimer(data) # Not working, something missing
    return data


def enable_scbs_r(data):
    def get_address(line, column):
        return (((line - 1) * 5) + column) * 8

    def compute_checksum(data):
        checksum = sum(data)
        low = checksum & 0xff
        high = (checksum >> 8) & 0xff
        return (low << 8) + high

    disabled = False
    a_16_b2 = get_address(16, 2)
    if data[0xf106].get_value(a_16_b2 + 6, 1) != 0x1:
        disabled = True
        data[0xf106].set_value(a_16_b2 + 6, 1, 0x1)

    if data[0xf106].get_value(a_16_b2 + 5, 1) != 0x0:
        disabled = True
        data[0xf106].set_value(a_16_b2 + 5, 1, 0x0)

    # Compute the checksum
    data[0xf106].set_value(0, 65535, compute_checksum(data[0xf106].to_bytearray()[2:]))

    if disabled:
        logger.info("Enable \"SCBS-R\"")
    else:
        logger.info("\"SCBS-R\" seems already enabled")


def unlock_ic_features(data):
    data = copy.deepcopy(data)
    enable_scbs_r(data)
    return data