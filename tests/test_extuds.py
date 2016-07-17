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

import unittest

try:
    from unittest.mock import Mock
except ImportError:
    from mock import Mock
from pyds.extuds import ExtendedUDS, NegativeResponseException
import uds


class UDS(object):
    pass


class ExtendedUDS_Test(unittest.TestCase):
    def check_output(self, udsChannel, output, msgType=uds.UDSMessage):
        message = msgType(output)
        udsChannel.send = Mock(side_effect=[message])
        return message

    def check_input(self, udsChannel, input):
        (data, timeout), dummy = udsChannel.send.call_args
        self.assertEqual(data.getData(), input)
        return data

    def test_send_rdbi(self):
        # Prepare
        udsChannel = UDS()
        extUdsChannel = ExtendedUDS(udsChannel, False, False)

        # Check output
        message = self.check_output(udsChannel, bytearray([0x62, 0xDE, 0x01, 0x00, 0x38, 0x10, 0xA0, 0x50]))
        self.assertEqual(message.getServiceID(), 0x62)

        # Send
        de01Data = extUdsChannel.send_rdbi(0xde01, 2000)

        # Check input
        self.check_input(udsChannel, bytearray([0x22, 0xDE, 0x01]))
        self.assertEqual(de01Data, bytearray([0x00, 0x38, 0x10, 0xA0, 0x50]))

    def test_initial_hs(self):
        # Prepare
        udsChannel = UDS()
        extUdsChannel = ExtendedUDS(udsChannel, False, False)

        # RDBI 1
        message = self.check_output(udsChannel, bytearray([0x7F, 0x22, 0x31]), uds.UDSNegativeResponseMessage)
        with self.assertRaises(NegativeResponseException) as context:
            extUdsChannel.send_rdbi(0xf183, 2000)
        self.assertEqual(context.exception.getReply(), message)
        self.check_input(udsChannel, bytearray([0x22, 0xF1, 0x83]))

    def test_initial_ms(self):
        # Prepare
        udsChannel = UDS()
        extUdsChannel = ExtendedUDS(udsChannel, False, False)

        # RDBI 1
        self.check_output(udsChannel, bytearray([0x62, 0x02, 0x02, 0x00]))
        extUdsChannel.send_rdbi(0x0202, 2000)
        self.check_input(udsChannel, bytearray([0x22, 0x02, 0x02]))

        # RDTCI 1
        self.check_output(udsChannel, bytearray([0x59, 0x02, 0xCA]))
        extUdsChannel.send_rdtci(uds.UDS_RDTCI_TYPES_BY_STATUS_MASK, 0x8f, 2000)
        self.check_input(udsChannel, bytearray([0x19, 0x02, 0x8F]))

        # RDBI 2
        self.check_output(udsChannel, bytearray([0x62, 0x02, 0x02, 0x00]))
        extUdsChannel.send_rdbi(0x0202, 2000)
        self.check_input(udsChannel, bytearray([0x22, 0x02, 0x02]))

        # RDTCI 2
        self.check_output(udsChannel, bytearray([0x59, 0x02, 0xCA, 0xC1, 0x55, 0x00, 0x08]))
        extUdsChannel.send_rdtci(uds.UDS_RDTCI_TYPES_BY_STATUS_MASK, 0x8f, 2000)
        self.check_input(udsChannel, bytearray([0x19, 0x02, 0x8F]))

        # RDBI 3
        self.check_output(udsChannel, bytearray(
            [0x62, 0xDE, 0x00, 0x45, 0x50, 0x00, 0x06, 0xA1, 0xA5, 0x0C, 0x43, 0x00, 0x08, 0x00, 0x38, 0x92, 0x10]))
        extUdsChannel.send_rdbi(0xde00, 2000)
        self.check_input(udsChannel, bytearray([0x22, 0xDE, 0x00]))

        # RDBI 4
        self.check_output(udsChannel, bytearray([0x62, 0xDE, 0x01, 0x00, 0x38, 0x10, 0xA0, 0x50]))
        extUdsChannel.send_rdbi(0xde01, 2000)
        self.check_input(udsChannel, bytearray([0x22, 0xDE, 0x01]))
