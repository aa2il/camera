################################################################################
#
# Params.py - Rev 1.0
# Copyright (C) 2024-6 by Joseph B. Attili, joe DOT aa2il AT gmail DOT com
#
# Command line param parser for camera
#
################################################################################
#
# This program is free software: you can redistribute it and/or modify
# it under the terms of the GNU General Public License as published by
# the Free Software Foundation, either version 3 of the License, or
# (at your option) any later version.
#
# This program is distributed in the hope that it will be useful,
# but WITHOUT ANY WARRANTY; without even the implied warranty of
# MERCHANTABILITY or FITNESS FOR A PARTICULAR PURPOSE.  See the
# GNU General Public License for more details.
#
################################################################################

import argparse
import os
import sys
import json

################################################################################

# Function to read camera config rc file
def read_camerarc(fname):
    rcfile=os.path.expanduser(fname)
    with open(rcfile) as json_data_file:
        cams = json.load(json_data_file)

        pretty_cams = json.dumps(cams, indent=4)
        print(pretty_cams)
        print(len(cams))

        SETTINGS={}
        for cam in cams:
            print(cam['NAME'])
            SETTINGS[cam['NAME']] = cam

    return SETTINGS

################################################################################

# Structure to contain processing params
class PARAMS:
    def __init__(self):

        # Process command line args
        arg_proc = argparse.ArgumentParser()
        arg_proc.add_argument("-cam", help="Camera Name",
                              type=str,default=None,nargs='*')
        arg_proc.add_argument("-download", help="Download videos for given date YYYYMMDD",
                              type=str,default=None,nargs="*")
        arg_proc.add_argument('-settings', action='store_true',
                              help='Update Camera Settings')
        args = arg_proc.parse_args()

        self.CAMS            = args.cam
        self.DOWNLOAD        = args.download
        self.UPDATE_SETTINGS = args.settings
        
        # Handle resource file (settings) - there is a single rc file for all cams
        self.SETTINGS = read_camerarc("~/.camerarc")

        # Expand camera group
        if len( self.CAMS )==1 and "GROUP" in self.SETTINGS[self.CAMS[0]]:
            self.CAMS=self.SETTINGS[self.CAMS[0]]["GROUP"]
