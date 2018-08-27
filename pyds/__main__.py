#!/usr/bin/env python
# coding=utf8

from __future__ import print_function, division, absolute_import

import sys
import os

import j2534

import argparse
import logging

from pyds import PydsApp, Modes

logger = logging.getLogger(__name__)


def cmdloop(app, args=None):
    if args is not None and len(args):
        if hasattr(app, 'run_commands_at_invocation'):
            return app.run_commands_at_invocation([str.join(' ', args)])
        else:
            app.debug = True
            app.cmdqueue.extend([str.join(' ', args), 'eos', 'quit'])
            return app.cmdloop()
    else:
        return app.cmdloop()


def get_mode(mode):
    if mode in Modes:
        return mode

    print("")
    while True:
        index = 0
        for mode, description in [(x.name, x.value) for x in list(Modes)]:
            print("%d - %s" % (index, description))
            index = index + 1
        mode_index_str = input("Select your mode: ")
        try:
            mode_index = int(mode_index_str)
            if mode_index < 0 or mode_index >= len(Modes):
                raise Exception("Invalid index")
            mode = list(Modes)[mode_index]
            print("")
            return mode
        except Exception as e:
            print("Invalid selection")


#
# For Windows platforms
#
class WinDiscover:
    def __init__(self):
        try:
            import winreg
            self.winreg = winreg
        except ImportError:
            import _winreg
            self.winreg = _winreg

    def list_pass_thru_devices(self):
        devices = []
        try:
            pass_thru_key = self.winreg.OpenKey(self.winreg.HKEY_LOCAL_MACHINE, r'SOFTWARE\\PassThruSupport.04.04', 0,
                                                self.winreg.KEY_READ | self.winreg.KEY_ENUMERATE_SUB_KEYS)
            i = 0
            while True:
                devices.append(self.winreg.EnumKey(pass_thru_key, i))
                i += 1
        except WindowsError:
            pass
        return devices

    def get_pass_thru_device_library(self, device):
        pass_thru_device_key = self.winreg.OpenKey(self.winreg.HKEY_LOCAL_MACHINE,
                                                   r'SOFTWARE\\PassThruSupport.04.04\\' + device, 0,
                                                   self.winreg.KEY_READ | self.winreg.KEY_ENUMERATE_SUB_KEYS)
        return self.winreg.QueryValueEx(pass_thru_device_key, r'FunctionLibrary')[0]

    def get_library(self, device):
        devices = self.list_pass_thru_devices()
        if device is None:
            if len(devices) == 1:
                device = devices[0]
            elif len(devices) > 1:
                print("")
                while True:
                    index = 0
                    for device in devices:
                        print("%d - %s" % (index, device))
                        index = index + 1
                    dev_index_str = input("Select your device: ")
                    try:
                        dev_index = int(dev_index_str)
                        if dev_index < 0 or dev_index >= len(devices):
                            raise Exception("Invalid index")
                        device = devices[dev_index]
                        print("")
                        break
                    except Exception:
                        print("Invalid selection")
            if device is None:
                raise Exception("No J2534 device available")
        print("Device:           %s" % (device))
        try:
            return self.get_pass_thru_device_library(device).encode('utf-8')
        except WindowsError:
            raise Exception("Device \"%s\" not found" % (device))


def _main(argv):
    print(
        "###############################################################################" + "\n" +
        "# This program is distributed in the hope that it will be useful, but WITHOUT #" + "\n" +
        "# ANY WARRANTY; without even the implied warranty of MERCHANTABILITY or       #" + "\n" +
        "# FITNESS FOR A PARTICULAR PURPOSE.  See the GNU General Public License for   #" + "\n" +
        "# more details.                                                               #" + "\n" +
        "###############################################################################" + "\n"
    )
    logging.basicConfig(stream=sys.stderr, level=logging.DEBUG,
                        format='%(asctime)s - %(threadName)s - %(name)s - %(levelname)s - %(message)s')

    parser = argparse.ArgumentParser(prog=argv[0], description="PYthon iDS tool",
                                     formatter_class=argparse.ArgumentDefaultsHelpFormatter)
    parser.add_argument('-v', '--verbose', dest='verbose_count', action='count', default=0,
                        help="increases log verbosity for each occurrence.")
    parser.add_argument('-l', '--library', help="Library to use")
    # Add parameter for Windows platforms
    if sys.platform == 'win32':
        parser.add_argument('-d', '--device', help="Device to use")
    parser.add_argument('-m', '--mode', type=lambda m: Modes[m], choices=list(Modes), help="Library mode")
    parser.add_argument('commands', nargs='*',
                        help='list of commands to execute')

    # Parse
    args, unknown_args = parser.parse_known_args(argv[1:])
    
    # Set logging level
    logging.getLogger().setLevel(max(3 - args.verbose_count, 0) * 10)

    # Library
    library_path = args.library
    if library_path is None:
        if sys.platform == 'win32':
            discover = WinDiscover()
            device = args.device
            library_path = discover.get_library(device)
    if library_path is None:
        raise Exception("No library or device provided")

    # Mode
    mode = get_mode(args.mode)

    # Print information
    print("Library Path:     %s" % (library_path))
    library = j2534.J2534Library(library_path)
    device = library.open(None)
    (firmware_version, dll_version, api_version) = device.readVersion()
    print("Firmware version: %s" % (firmware_version))
    print("DLL version:      %s" % (dll_version))
    print("API version:      %s" % (api_version))
    print("Mode:             %s" % (mode))
    print("\n\n")

    # Create shell
    app = PydsApp(device, mode)
    return cmdloop(app, args.commands + unknown_args)


def main():
    # Change sys.stdin so it provides universal newline support.
    if sys.hexversion < 0x03000000:
        sys.stdin = os.fdopen(sys.stdin.fileno(), 'rU', 0)
    else:
        sys.stdin = open(sys.stdin.fileno(), 'r', newline=None)
    try:
        sys.exit(_main(sys.argv))
    except Exception as e:
        logger.exception(e)
        sys.exit(-1)
    finally:
        logging.shutdown()


if __name__ == "__main__":
    main()
