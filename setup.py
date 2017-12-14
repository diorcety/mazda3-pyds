#!/usr/bin/env python

import sys
from setuptools import setup

if sys.version_info[0] == 2:
    proxy = "ProxyTypes"
else:
    proxy = "objproxies"

setup(
    name='pyds',
    version='0.1',
    author='Diorcet Yann',
    author_email='diorcet.yann@gmail.com',
    license='GPL',
    packages=['pyds'],
    entry_points={
        'console_scripts': ['pyds=pyds.__main__:main'],
    },
    install_requires=['mock', 'enum34', 'cmd2', proxy],
)
