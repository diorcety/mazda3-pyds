# Fix Python 2.x.
from __future__ import print_function

_author__ = "Yann Diorcet"
__license__ = "GPL"
__version__ = "0.0.1"

import struct
import uds

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
    def __init__(self, udsChannel, step_by_step=True, debug=True):
        self.step_by_step = step_by_step
        self.debug = debug
        self.udsChannel = udsChannel

    @staticmethod
    def int16tobytes(number):
        return struct.pack(">H", number)

    @staticmethod
    def bytestoint16(bytes):
        return struct.unpack(">H", bytes)[0]

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
        reply = self.buildMessage(self.udsChannel.send(message, timeout))
        if self.debug:
            print("Received: %s" % (" ".join(['%02x' % (k) for k in reply.getData()])))
        if isinstance(reply, uds.UDSNegativeResponseMessage):
            raise NegativeResponseException(reply)
        if reply.getServiceID() != (sid | uds.UDS_REPLY_MASK):
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
        reply = self.send(uds.UDS_SERVICES_IOCBI, self.int16tobytes(did)+ bytearray([parameter]) + state, timeout)
        data = reply.getData()
        rdid = self.bytestoint16(self.slice_data(data, uds, 'UDS_IOCBI_DATA_IDENTIFIER'))
        if rdid != did:
            raise Exception("Invalid dataIdentifier %x for a request of type %x" % (rdid, did))
        return data[uds.UDS_IOCBI_DATA_RECORD_OFFSET:]

    def change_diagnostic_session(self, sessionType):
        type = bytearray([sessionType])
        reply = self.send(uds.UDS_SERVICES_DSC, type)
        reply_data = reply.getData()
        reply_type = self.slice_data(reply_data, uds, 'UDS_DSC_TYPE')
        if type != reply_type:
            raise Exception("Invalid type %x for a request of type %x" % (type[0], reply_type[0]))

    def grant_security_access(self, algo):
        type = bytearray([uds.UDS_SA_TYPES_SEED_2])
        seed_reply = self.send(uds.UDS_SERVICES_SA, type)
        seed_reply_data = seed_reply.getData()
        reply_type = self.slice_data(seed_reply_data, uds, 'UDS_SA_TYPE')
        if type != reply_type:
            raise Exception("Invalid type %x for a request of type %x" % (type[0], reply_type[0]))
        sessionSeed = seed_reply_data[uds.UDS_SA_SEED_OFFSET:]
        key = algo.compute(sessionSeed)
        type = bytearray([uds.UDS_SA_TYPES_KEY_2])
        key_reply = self.send(uds.UDS_SERVICES_SA, type + key)
        key_reply_data = key_reply.getData()
        reply_type = self.slice_data(key_reply_data, uds, 'UDS_SA_TYPE')
        if type != reply_type:
            raise Exception("Invalid type %d for a request of type %d" % (type[0], reply_type[0]))
