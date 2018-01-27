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

import sys
import re
from pyds.structs import Algorithm

# Fix Python 2.x.
try:
    input = raw_input
except NameError:
    input = input


class FordCommon14229Security(object):
    initialValue = 0x00C541A9
    v1 = 0x00109028
    v2 = 0xFFEF6FD7

    def __init__(self, vehicle_seed):
        self.vehicle_seed = vehicle_seed
        assert len(vehicle_seed) == 6

    def compute(self, session_seed):
        assert len(session_seed) == 3

        challenge = bytearray(8)
        challenge[0:3] = session_seed[0:3]
        challenge[3:8] = self.vehicle_seed[0:5]
        buff = self.initialValue

        for b in challenge:
            for j in range(0, 8):
                temp_buffer = 0
                if (b ^ buff) & 0x1:
                    buff = buff | 0x1000000
                    temp_buffer = self.v1
                b = b >> 1
                temp_buffer = temp_buffer ^ (buff >> 1)
                temp_buffer = temp_buffer & (self.v1)
                temp_buffer = temp_buffer | (self.v2 & (buff >> 1))
                buff = temp_buffer & 0xffffff

        return bytearray([(buff >> 4 & 0xff), ((buff >> 20) & 0x0f) + ((buff >> 8) & 0xf0),
                          ((buff << 4) & 0xff) + ((buff >> 16) & 0x0f)])


def get_security_algorithm(algo, *data):
    if algo == Algorithm.Ford:
        return FordCommon14229Security(*data)
    else:
        raise Exception("Invalid SecurityAlgorithm %s" % (str(algo)))


####################
####################
####################

def main(argv):
    str_vs = input("Enter the vehicule seed: ")
    vs = bytearray.fromhex(re.sub('\s+', '', str_vs))
    if not isinstance(vs, bytearray) or len(vs) != 5:
        raise ValueError("The vehicule seed must be a array of 5 bytes")
    str_ss = input("Enter the session seed: ")
    ss = bytearray.fromhex(re.sub('\s+', '', str_ss))
    if not isinstance(ss, bytearray) or len(ss) != 3:
        raise ValueError("The session seed must be a array of 3 bytes")
    fs = FordCommon14229Security()
    key = fs.compute(vs, ss)
    print("The session key: %s" % ("".join(["%02X" % x for x in key])))


if __name__ == "__main__":
    main(sys.argv)
