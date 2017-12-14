#!/usr/bin/env python

from __future__ import print_function

"""
J2534 log to pcap file
"""

import os
import sys
import argparse
import re

from construct import *
from calendar import timegm
from datetime import datetime

class MicrosecAdapter(Adapter):
    def _decode(self, obj, context):
        return datetime.utcfromtimestamp(obj[0] + (obj[1] / 1000000.0))

    def _encode(self, obj, context):
        sec = timegm(obj.utctimetuple())
        usec = obj.microsecond
        return (sec, usec)


can_packet = Struct(
    "id" / Int32ub,
    "dlc" / Int8ul,
    Padding(3),
    "data" / Bytes(lambda ctx: ctx.dlc),
)

cap_packet = Struct(
    MicrosecAdapter(
        "time" / Sequence(
            "sec" / Int32ul,
            "usec" / Int32ul,
        )
    ),
    "inc_length" / Int32ul,
    "orig_length" / Int32ul,
    "data" / Bytes(lambda ctx: ctx.inc_length),
)

cap_file = Struct(
    "magic_number" / Const(0xa1b2c3d4, Int32ul),
    "version_major" / Const(0x2, Int16ul),
    "version_minor" / Const(0x4, Int16ul),
    "thiszone" / Int32sl,
    "sigfigs" / Int32ul,
    "snaplen" / Int32ul,
    "network" / Const(0xe3, Int32ul),
    "packets" / GreedyRange(cap_packet),
)


def parse_can_date(date):
    return datetime.strptime(date, '%m/%d/%Y at %H:%M:%S.%f')


def parse_can_data(line):
    entries = [int(x, 16) for x in line.split()]
    assert len(entries) >= 4
    id = (entries[0] << 24) + (entries[1] << 16) + (entries[2] << 8) + (entries[3])
    return can_packet.build(Container(
        id=id,
        dlc=len(entries) - 4,
        data=bytearray(entries[4:]),
    ))


def main(argv):
    parser = argparse.ArgumentParser(description="J2534 logs parser")
    parser.add_argument('-c', '--channel', help="channel to select")
    parser.add_argument('file', nargs='?', help="file to read")
    args = parser.parse_args(argv[1:])
    selectedChannel = args.channel
    allpackets = {}

    if args.file:
        with open(args.file, 'rb') as f:
            data = ''.join(f.readlines())
        ostream = open(os.path.splitext(args.file)[0] + '.pcap', 'wb')
    else:
        data = ""
        for line in sys.stdin:
            data += line
        ostream = sys.stdout

    data = data.replace('\r\n', '\n')

    groups = data.split('\n\n\n')

    regex = re.compile(
        "On ([^,]+), (\w+?) O:.*" + "\s*ChannelID:\s*(\d+)\s*\n" + ".*" + "\s*RxStatus:\s*([^\n]*)\s*\n" + ".*" + "\s*Data \[\w+\]:\s*(.*)\s*\n\n" + ".*",
        re.DOTALL | re.MULTILINE)

    def add(channelId, date, data):
        data = parse_can_data(data)
        date = parse_can_date(date)
        if channelId not in allpackets:
            allpackets[channelId] = []
            print("%s" % (channelId), file=sys.stderr)
        allpackets[channelId].append(Container(
            time=date,
            inc_length=len(data),
            orig_length=len(data),
            data=data,
        ))

    for g in groups:
        for r in regex.findall(g):
            date = r[0]
            act = r[1]
            channel = r[2]
            rxflags = r[3]
            data = r[4]
            if act == 'PassThruReadMsgs':
                if rxflags == 'No Flags Set':
                    add(channel, date, data)
            if act == 'PassThruWriteMsgs':
                add(channel, date, data)

    if selectedChannel is None:
        if len(allpackets) != 1:
            raise Exception("Not only one channel available: %s" % (
                ", ".join(["%s[%d]" % (k, len(allpackets[k])) for k in allpackets])))
        packets = allpackets.itervalues().next()
    else:
        if selectedChannel not in allpackets:
            raise Exception("Invalid channel %s: %s" % (
                selectedChannel, ", ".join(["%s[%d]" % (k, len(allpackets[k])) for k in allpackets])))
        packets = allpackets[selectedChannel]

    data = Container(
        magic_number=0xa1b2c3d4,
        version_major=0x2,
        version_minor=0x4,
        network=0xe3,
        thiszone=0,
        sigfigs=0,
        snaplen=0xfffff,
        packets=packets
    )
    cap_file.build_stream(data, ostream)


if __name__ == "__main__":
    main(sys.argv)
