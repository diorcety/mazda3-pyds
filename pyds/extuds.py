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

import struct
import uds
import logging

logger = logging.getLogger(__name__)

try:
    input = raw_input
except NameError:
    input = input


class NegativeResponseException(Exception):
    def __init__(self, reply):
        self.reply = reply

    def getReply(self):
        return self.reply

    def __str__(self):
        return "Error %x for service %x" % (self.reply.getErrorCode(), self.reply.getRequestServiceID())


class ExtendedUDS(object):
    def __init__(self, uds_channel, step_by_step=True):
        self.step_by_step = step_by_step
        self._uds_channel = uds_channel

    @staticmethod
    def int16tobytes(number):
        return struct.pack(">H", number)

    @staticmethod
    def int32tobytes(number):
        return struct.pack(">I", number)

    @staticmethod
    def bytestoint16(bytes):
        return struct.unpack(">H", bytes)[0]

    @staticmethod
    def bytestoint32(bytes):
        return struct.unpack(">I", bytes)[0]

    @staticmethod
    def slice_data(data, module, field, offset_str='_OFFSET', len_str='_LEN'):
        offset = getattr(module, field + offset_str)
        len = getattr(module, field + len_str)
        return data[offset:(offset + len)]

    @staticmethod
    def buildMessage(reply):
        # Work around SWIG issue
        if (reply.getServiceID() & uds.UDS_REPLY_MASK) == uds.UDS_SERVICES_ERR:
            return uds.UDSNegativeResponseMessage(reply.getData())
        else:
            return reply

    def send(self, sid, data, timeout=2000):
        timeout_multiplier = 1
        fdata = bytearray([sid])
        fdata.extend(data)
        message = uds.UDSMessage(fdata)
        if self.step_by_step:
            print("Will send: %s" % (" ".join(['%02x' % (k) for k in fdata])))
            response = input("Are you sure to send this? ")
            if response != 'YES':
                raise Exception("Interrupted by the user")
        logger.debug("Sending: %s" % (" ".join(['%02x' % (k) for k in fdata])))

        while True:
            reply = self.buildMessage(self._uds_channel.send(message, timeout * timeout_multiplier))
            message = None
            logger.debug("Received: %s" % (" ".join(['%02x' % (k) for k in reply.getData()])))
            if isinstance(reply, uds.UDSNegativeResponseMessage):
                raise NegativeResponseException(reply)
            if reply.getServiceID() == (uds.UDS_SERVICES_ERR | uds.UDS_REPLY_MASK):
                data = reply.getData()
                srdid, error = tuple(data[uds.UDS_ERR_SID_OFFSET:])
                if srdid != sid or error != uds.UDS_RESPONSE_CODES_RCRRP:
                    raise Exception("Invalid reply %x for a request of type %x" % (reply.getServiceID(), sid))
                logger.debug("Response delayed")
                timeout_multiplier *= 2
                continue
            elif reply.getServiceID() != (sid | uds.UDS_REPLY_MASK):
                raise Exception("Invalid reply %x for a request of type %x" % (reply.getServiceID(), sid))
            return reply

    def send_dsc(self, type, timeout=2000):
        reply = self.send(uds.UDS_SERVICES_DSC, bytearray([type]), timeout)
        data = reply.getData()
        rtype = self.slice_data(data, uds, 'UDS_DSC_TYPE')[0]
        if rtype != type:
            raise Exception("Invalid dataIdentifier %x for a request of type %x" % (rtype, type))
        return data[uds.UDS_DSC_PARAMETER_RECORD_OFFSET:]

    def send_sa(self, type, data, timeout=2000):
        reply = self.send(uds.UDS_SERVICES_SA, bytearray([type]) + data, timeout)
        data = reply.getData()
        rtype = self.slice_data(data, uds, 'UDS_SA_TYPE')[0]
        if rtype != type:
            raise Exception("Invalid dataIdentifier %x for a request of type %x" % (rtype, type))
        return data[uds.UDS_SA_KEY_OFFSET:]

    def send_rdbi(self, did, timeout=2000):
        reply = self.send(uds.UDS_SERVICES_RDBI, self.int16tobytes(did), timeout)
        data = reply.getData()
        rdid = self.bytestoint16(self.slice_data(data, uds, 'UDS_RDBI_DATA_IDENTIFIER'))
        if rdid != did:
            raise Exception("Invalid dataIdentifier %x for a request of type %x" % (rdid, did))
        return data[uds.UDS_RDBI_DATA_RECORD_OFFSET:]

    def send_rdtci(self, type, data, timeout=2000):
        reply = self.send(uds.UDS_SERVICES_RDTCI, bytearray([type, data]), timeout)
        data = reply.getData()
        rtype = self.slice_data(data, uds, 'UDS_RDTCI_TYPE')[0]
        if rtype != type:
            raise Exception("Invalid type %x for a request of type %x" % (rtype, type))
        return data[uds.UDS_RDTCI_RECORD_OFFSET:]

    def send_wdbi(self, did, data, timeout=2000):
        reply = self.send(uds.UDS_SERVICES_WDBI, self.int16tobytes(did) + data, timeout)
        data = reply.getData()
        rdid = self.bytestoint16(self.slice_data(data, uds, 'UDS_WDBI_DATA_IDENTIFIER'))
        if rdid != did:
            raise Exception("Invalid dataIdentifier %x for a request of type %x" % (rdid, did))
        return data[uds.UDS_RDBI_DATA_RECORD_OFFSET:]

    def send_iocbi(self, did, parameter, state, timeout=2000):
        reply = self.send(uds.UDS_SERVICES_IOCBI, self.int16tobytes(did) + bytearray([parameter]) + state, timeout)
        data = reply.getData()
        rdid = self.bytestoint16(self.slice_data(data, uds, 'UDS_IOCBI_DATA_IDENTIFIER'))
        if rdid != did:
            raise Exception("Invalid dataIdentifier %x for a request of type %x" % (rdid, did))
        return data[uds.UDS_IOCBI_STATE_OFFSET:]

    def send_cdtcs(self, func, timeout=2000):
        reply = self.send(uds.UDS_SERVICES_CDTCS, bytearray(func), timeout)
        data = reply.getData()
        rfunc = self.slice_data(data, uds, 'UDS_CDTCS_TYPE')[0]
        if rfunc != func:
            raise Exception("Invalid func %x for a request of type %x" % (rfunc, func))

    def send_cc(self, func, type, timeout=2000):
        reply = self.send(uds.UDS_SERVICES_CC, bytearray(func, type), timeout)
        data = reply.getData()
        rfunc = self.slice_data(data, uds, 'UDS_CC_SUB_FUNCTION')[0]
        if rfunc != func:
            raise Exception("Invalid func %x for a request of type %x" % (rfunc, func))

    def reset(self, resetType, timeout=2000):
        type = bytearray([resetType])
        reply = self.send(uds.UDS_SERVICES_ER, type, timeout)
        reply_data = reply.getData()
        reply_type = self.slice_data(reply_data, uds, 'UDS_ER_TYPE')
        if type != reply_type:
            raise Exception("Invalid type %x for a request of type %x" % (type[0], reply_type[0]))

    def change_diagnostic_session(self, sessionType, timeout=2000):
        type = bytearray([sessionType])
        reply = self.send(uds.UDS_SERVICES_DSC, type, timeout)
        reply_data = reply.getData()
        reply_type = self.slice_data(reply_data, uds, 'UDS_DSC_TYPE')
        if type != reply_type:
            raise Exception("Invalid type %x for a request of type %x" % (type[0], reply_type[0]))

    def grant_security_access(self, algo, timeout=2000):
        type = bytearray([uds.UDS_SA_TYPES_SEED_2])
        seed_reply = self.send(uds.UDS_SERVICES_SA, type, timeout)
        seed_reply_data = seed_reply.getData()
        reply_type = self.slice_data(seed_reply_data, uds, 'UDS_SA_TYPE')
        if type != reply_type:
            raise Exception("Invalid type %x for a request of type %x" % (type[0], reply_type[0]))
        sessionSeed = seed_reply_data[uds.UDS_SA_SEED_OFFSET:]
        key = algo.compute(sessionSeed)
        type = bytearray([uds.UDS_SA_TYPES_KEY_2])
        key_reply = self.send(uds.UDS_SERVICES_SA, type + key, timeout)
        key_reply_data = key_reply.getData()
        reply_type = self.slice_data(key_reply_data, uds, 'UDS_SA_TYPE')
        if type != reply_type:
            raise Exception("Invalid type %d for a request of type %d" % (type[0], reply_type[0]))

    def upload(self, addr_tuple, size_tuple, timeout=2000):
        addr, addr_s = addr_tuple
        size, size_s = size_tuple
        compression = 0
        encryption = 0
        dfi(0x0F & compression) << 0 | (0x0F & encryption) << 4
        alfi = (0x0F & addr_s) << 0 | (0x0F & size_s) << 4
        mem_addr = int32tobytes(addr)[0:addr_s]
        mem_size = int32tobytes(size)[0:size_s]

        # Request for upload
        ba = bytearray([dfi, alfi, mem_addr, mem_size])
        upload_reply_data = self.send(uds.UDS_SERVICES_RU, ba, timeout)
        data = reply.getData()
        lfi = self.slice_data(upload_reply_data, uds, 'UDS_RU_LENGTH_FORMAT_IDENTIFIER')[0]
        max_number_block_length = upload_reply_data[
                                  UDS_RU_MAX_NUMBER_OF_BLOCK_LENGTH_OFFSET:UDS_RU_MAX_NUMBER_OF_BLOCK_LENGTH_OFFSET + lfi]

        sbsc = 1
        data = bytearray()
        while size > len(data):
            # Ask for data
            ba = bytearray([sbsc])
            td_reply = self.send(uds.UDS_SERVICES_TD, ba, timeout)
            td_reply_data = td_reply.getData()

            # Check the reply
            rbsc = self.slice_data(td_reply_data, uds, 'UDS_TD_BLOCK_SEQUENCE_COUNTER')[0]
            if rbsc != sbsc:
                raise Exception("Invalid block sequence counter value %d for a request of value %d" % (rbsc, sbsc))
            if len(td_reply_data) >= max_number_block_length:
                raise Exception("Invalid data length")

            # Append
            packet_data = td_reply_data[UDS_TD_TRANSFER_PARAMETER_RECORD_OFFSET:]
            data.extend(packet_data)
            print("Progression %.0f (%d of %d)" % ((len(data) * 100) / size, len(data), size),
                  sep='\r', end='', flush=True)

            # Increment
            sbsc = (sbsc + 1) % 256

        # End of transfer
        self.send(uds.UDS_SERVICES_RTE, bytearray([]), timeout)
        print("End of the transfer")
