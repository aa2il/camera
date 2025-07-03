#! /usr/bin/python3 -u
############################################################################################
#
# tapoC500.py - Rev 0.1
# Copyright (C) 2024-5 by Joseph B. Attili, joe DOT aa2il AT gmail DOT com
#
# PTZ control for Tapo C500 Camera.  This camera is an ONVIF Profile S device.
#
# Notes:
#      - To change wifi network, use app to remove device which will allow you
#        to start from scratch
#      - May or may not need to install these:
#              pip3 install onvif_zeep
#              pip3 install opencv-python
#
# Useful websites for determining how to do this:
# https://www.onvif.org/onvif/ver20/util/operationIndex.html
# https://pkg.go.dev/github.com/use-go/onvif/ptz#pkg-functions
# https://github.com/quatanium/python-onvif
# https://github.com/RichardoMrMu/python-onvif
# https://carlrowan.wordpress.com/2018/12/23/ip-camera-control-using-python-via-onvif-for-opencv-image-processing/
# https://www.mjr19.org.uk/IT/seminar_cam/ptz.html
#
############################################################################################
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
############################################################################################

import sys
from time import sleep
import datetime
from onvif import ONVIFCamera

############################################################################################

class TapoC500():
    def __init__(self,IP,USER,PASSWORD,PORT=2020):

        # Camera params
        self.RTSP_URL = "rtsp://"+USER+":"+PASSWORD+"@"+IP+":554/stream1"
        self.ifov1=4.5/20       # 2 is a complete revolution (360-deg) and it takes about 4.5/20 steps to move an object from one side to the other (one FOV)
        self.ifov2=10/20         # A step of 2 is needed to go from max up to max down (114-deg) and about 10/20 steps to move an object from top to bottome (one FOV)
        
        # Open camera control port
        self.mycam = ONVIFCamera(IP,PORT,USER,PASSWORD)

        # Get Hostname
        resp = self.mycam.devicemgmt.GetHostname()
        print('Camera hostname= ' + str(resp.Name))

        # Get date and time
        dt = self.mycam.devicemgmt.GetSystemDateAndTime()
        tz = dt.TimeZone
        year = dt.UTCDateTime.Date.Year
        hour = dt.UTCDateTime.Time.Hour
        min  = dt.UTCDateTime.Time.Minute
        print('Camera date/time: tz=',tz,'\tyear=',year,'\thour=',hour,'\tmin=',min)
        
        # Create media service object
        self.media = self.mycam.create_media_service()
        self.media_profile = self.media.GetProfiles()[0]
        self.token = self.media_profile.token
        
        # Create ptz service object & check what services are available
        self.ptz = self.mycam.create_ptz_service()
        request = self.ptz.create_type('GetServiceCapabilities')
        Service_Capabilities = self.ptz.GetServiceCapabilities(request)
        print('Service_Capabilities=',Service_Capabilities)

        # GetStatus doesn't work - ugh!
        #status = self.ptz.GetStatus({'ProfileToken': self.token})

        # Get PTZ configuration options
        request = self.ptz.create_type('GetConfigurationOptions')
        print('PTZ request=',request)
        request.ConfigurationToken = self.media_profile.PTZConfiguration.token
        ptz_configuration_options = self.ptz.GetConfigurationOptions(request)
        print('\nrequest=',request)
        print('\nptz config options=',ptz_configuration_options)

        # Setup continuousMove request
        self.requestCont = self.ptz.create_type('ContinuousMove')
        self.requestCont.ProfileToken = self.media_profile.token
        #self.requestc.Velocity = self.ptz.GetStatus({'ProfileToken': self.media_profile.token}).Position
        self.requestCont.Velocity = {'PanTilt': {'x': 0, 'y': 0} , 'Zoom': {'x':0} }

        # Setup absoluteMove request
        self.requestAbs = self.ptz.create_type('AbsoluteMove')
        self.requestAbs.ProfileToken = self.media_profile.token
        self.requestAbs.Position = {'PanTilt': {'x': 0, 'y': 0} ,'Zoom': 0 }

        # Setup relativeMove request
        self.requestRel = self.ptz.create_type('RelativeMove')
        self.requestRel.ProfileToken = self.media_profile.token
        self.requestRel.Translation = {'PanTilt': {'x': 0, 'y': 0} ,'Zoom': 0 }

        # Setup other requests
        self.requests = self.ptz.create_type('Stop')
        self.requests.ProfileToken = self.media_profile.token
        self.requestp = self.ptz.create_type('SetPreset')
        self.requestp.ProfileToken = self.media_profile.token
        self.requestg = self.ptz.create_type('GotoPreset')
        self.requestg.ProfileToken = self.media_profile.token
        self.stop()

        # This shows how to parse various config options - should use thse eventually
        XMIN = ptz_configuration_options.Spaces.AbsolutePanTiltPositionSpace[0].XRange.Min
        XMAX = ptz_configuration_options.Spaces.AbsolutePanTiltPositionSpace[0].XRange.Max
        YMIN = ptz_configuration_options.Spaces.AbsolutePanTiltPositionSpace[0].YRange.Min
        YMAX = ptz_configuration_options.Spaces.AbsolutePanTiltPositionSpace[0].YRange.Max
        print('\nXMIN=',XMIN,'\tXMAX=',XMAX,'\tYMIN=',YMIN,'\tYMAX=',YMAX)

        # Create recording service object - doesn't work!
        #self.rec = self.mycam.create_recording_service()
        #self.rec = self.mycam.create_search_service()
        #self.rec = self.mycam.create_replay_service()
        #self.events = self.mycam.create_events_service()
        #e = self.events.GetEventProperties()
        #print(e)
        #e = self.events.GetServiceCapabilities()
        #print(e)
        #e = self.events.PullMessages()
        #print(e)
        #profiles = self.media.GetProfiles()
        #print('\nprofiles=',profiles)
        #uri = self.media.GetSnapshotUri({'ProfileToken': self.media_profile.token})
        #print('\nuri=',uri)
        #caps = self.mycam.devicemgmt.GetCapabilities()
        #print('\ncaps=',caps)
        #sys.exit(0)

    # Relative move
    def rel_move(self,x,y,z=0):

        # Set position & speed
        self.requestRel.Translation = {'PanTilt': {'x': x, 'y': y} ,'Zoom': z }
        #request.Speed    = {'PanTilt': {'x': XMAX, 'y': YMAX}}
        #print('\nrequest=',request)
    
        # Send the command
        try:
            self.ptz.RelativeMove(self.requestRel)
        except:
            print('Relative Move Failed - probably hit stop')

    # Absolute move
    def abs_move(self,x,y,z=0):
        
        # Set position & speed
        self.requestAbs.Position = {'PanTilt': {'x': x, 'y': y} ,'Zoom': z }
        #request.Speed    = {'PanTilt': {'x': XMAX, 'y': YMAX}}
        #print('\nrequest=',request)
    
        # Send the command
        self.ptz.AbsoluteMove(self.requestAbs)

    # Continuous move
    def cont_move(self,dir,timeout=1):
        
        # Should read these from the camera but good senough for now ...
        XMAX = 1
        XMIN = -1
        YMAX = 1
        YMIN = -1

        # Set Pan-Tilt movement
        if dir=='up':
            x=0
            y=YMAX
            z=0
        elif dir=='down':
            x=0
            y=YMIN
            z=0
        elif dir=='left':
            x=XMAX
            y=0
            z=0
        elif dir=='right':
            x=XMIN
            y=0
            z=0
        elif dir=='in' and False:
            # It doesn't look like zooming is available on this camera
            x=0
            y=0
            z=1
        elif dir=='out' and False:
            x=0
            y=0
            z=-1
        else:
            print('\n*** ERROR *** Invalid direction',dir)
            return
        self.requestCont.Velocity = {'PanTilt': {'x': x, 'y': y} , 'Zoom': {'x':z} }
        
        # Set the timeout for the movement
        self.requestCont.Timeout = datetime.timedelta(seconds=timeout)
        #print('\nrequest=',request)
        
        # Send the command
        try:
            self.ptz.ContinuousMove(self.requestCont)
        except:
            print('Continuous Move Failed - probably hit stop')
    
    # Stop pan, tilt and zoom
    def stop(self):
        self.requests.PanTilt = True
        self.requests.Zoom = True
        print(f"self.request:{self.requests}")
        self.ptz.Stop(self.requests)

############################################################################################

if __name__ == '__main__':
    ptz = TapoC500(IP,PORT,USER,PASS)
    
    #ptz.rel_move(0.1,0.1)
    ptz.abs_move(0.,0.)
    sleep(2)

    if True:
        ptz.cont_move('left')
        sleep(2)
        ptz.cont_move('up')
        sleep(2)
        ptz.cont_move('right')
        sleep(2)
        ptz.cont_move('down')

    # These don't work
    if False:
        request = ptz.ptz.create_type('GotoHomePosition')
        request.ProfileToken = ptz.media_profile.token
        request.Speed = {'PanTilt': {'x': 0.5, 'y': 0.5}}
        print('\nrequest=',request)
        status = ptz.ptz.GotoHomePosition(request)
        print('\nstatus=',status)
        sys.exit(0)
        
    if False:
        request = ptz.ptz.create_type('GetStatus')
        request.ProfileToken = ptz.media_profile.token
        print('\nrequest=',request)
        status = ptz.ptz.GetStatus(request)
        print('\nstatus=',status)
        sys.exit(0)
    

        
