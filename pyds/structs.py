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

from enum import Enum


class Algorithm(Enum):
    Ford = 70


class SecurityType(Enum):
    Config = 0
    SelfTest = 1
    IOControl = 2
    Reprog = 3


class SecurityData(object):
    def __init__(self, level, session, key):
        super(SecurityData, self).__init__()
        self._level = level
        self._session = session
        self._key = key

    @property
    def level(self):
        return self._level

    @property
    def session(self):
        return self._session

    @property
    def key(self):
        return self._key


class Security(object):
    def __init__(self, algorithm, configurations):
        super(Security, self).__init__()
        self._algorithm = algorithm
        self._configurations = configurations

    @property
    def algorithm(self):
        return self._algorithm

    @property
    def configurations(self):
        return self._configurations


class CanBus(Enum):
    HS = 0
    MS = 1


class Vehicle(object):
    def __init__(self, buses, modules):
        super(Vehicle, self).__init__()
        self._buses = buses
        self._modules = modules

    @property
    def buses(self):
        return self._buses

    @property
    def modules(self):
        return self._modules


class Module(object):
    def __init__(self, bus, security):
        super(Module, self).__init__()
        self._bus = bus
        self._security = security

    @property
    def bus(self):
        return self._bus

    @property
    def security(self):
        return self._security
