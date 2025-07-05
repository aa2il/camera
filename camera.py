#!/usr/bin/env -S uv run --script
#
# NEW: /home/joea/miniconda3/envs/py3_10/bin/python -u
# OLD: /usr/bin/python3 -u 
################################################################################
#
# Camera - Rev 0.1
# Copyright (C) 2024-5 by Joseph B. Attili, joe DOT aa2il AT gmail DOT com
#
# Simple app to view, control and download videos for Tapo C500 Video Camera.
#
# The code for downloading is based on pytapo by Juraj Nyiri found at 
#         https://github.com/JurajNyiri
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
import sys
#import os
import subprocess
import cv2
from tapoC500 import TapoC500
from time import time
from settings import CONFIG_PARAMS,SETTINGS_GUI
from datetime import datetime

from pytapo import Tapo
from pytapo.media_stream.downloader import Downloader
import asyncio
import os

################################################################################

# Structure to contain config params
class CAM_CONFIG_PARAMS:
    def __init__(self,fname,CAMERA=None):
        rcfile=os.path.expanduser(fname)
        with open(rcfile) as json_data_file:
            cams = json.load(json_data_file)
            print(cams)
            print(len(cams))
            for cam in cams:
                if cam['MY_CAMERA']==CAMERA:
                    self.SETTINGS=cam
                    break
            else:
                self.SETTINGS=cams[0]         # Default to first camera

################################################################################

class VIDEO_CAMERA():
    def __init__(self,P):

        self.P=P
        self.step=0.1

        IP=P.SETTINGS['MY_IP']
        USER=P.SETTINGS['MY_USER']
        PASSWORD=P.SETTINGS['MY_PASSWORD']

        self.cross_hairs=None
        self.cross_size=50
        self.box1=None
        self.box2=None
        self.LEFT_DOWN=False
        
        # See opencv.org for details
        print('Setting up Video Camera - Press ESCAPE to exit ...')

        # Open PTZ controls
        print('If we get failure here, probably need to update camera firmware via Tapo app on phone or tablet.')
        self.ptz = TapoC500(IP,USER,PASSWORD)

        # Open camera video stream
        print('Opening video stream ...',self.ptz.RTSP_URL)
        self.cap = cv2.VideoCapture(self.ptz.RTSP_URL)

        print('And away we go!')
        self.run_camera()

    # Read the stream
    def run_camera(self):

        # Create window to display imagery
        # Do it this way so we can resize it manually if we want to
        #cam_name='frame'
        cam_name=self.P.SETTINGS['MY_CAMERA']
        cv2.namedWindow(cam_name, cv2.WINDOW_NORMAL)
        first_time=True

        now = datetime.now()
        print('Camera started at',now)
        
        while(self.cap.isOpened()):
            ret, img = self.cap.read()
            
            # Put frame operations here - e.g. resize
            #print('Original Dimensions : ',img.shape)
            try:
                # First, compute new image size ...
                sc = 1 # 0.5
                width = int(sc*img.shape[1])
                height = int(sc*img.shape[0])
                missed=0
            except:
                # If the camera has been turned off, try again
                # If too many retries, exit gracefully
                missed+=1
                print('Whoops - missed image???!!!',missed)
                if missed<50:
                    continue
                else:
                    print('*** Camera probably disconeected - bailing out! ***')
                    break

            # Do the actual resizing
            dim = (width, height)
            self.img2 = cv2.resize(img, dim, interpolation = cv2.INTER_AREA)
            #print('Resized Dimensions : ',img2.shape)

            # Add box/cross-hairs
            if self.LEFT_DOWN:
                self.DrawBox()
                self.cross_hairs=None
            else:
                if self.cross_hairs:
                    self.DrawCrossHairs()
                    
            # Display the frame
            cv2.imshow(cam_name, self.img2)
            if first_time:
                cv2.resizeWindow(cam_name,width,height)
                #sz=cv2.getWindowImageRect(cam_name)
                #print(sz,width,height)
                first_time=False

            # Enable mouse callback
            cv2.setMouseCallback(cam_name, self.MouseCB)

            # Check for clean exit
            ch = cv2.waitKey(20) # & 0xFF
            if ch>0:
                print('ch=',ch)
                if ch==82:
                    self.ptz.rel_move(0,-self.step)
                elif ch==84:
                    self.ptz.rel_move(0,self.step)
                elif ch==81:
                    self.ptz.rel_move(-self.step,0)
                elif ch==83:
                    self.ptz.rel_move(self.step,0)
                elif ch in [27,ord('q'),ord('Q')]:
                    break
            
            # Check for click on big X to exit also
            if cv2.getWindowProperty(cam_name,cv2.WND_PROP_VISIBLE) <= 0:
                print('Blah blah blah')
                break        
            
        # Clean-up and quit
        print('Cleaning up ...')
        self.cap.release()
        cv2.destroyAllWindows()
        now = datetime.now()
        print('Camera done at',now)        

    ############################################################################
    
    def MouseCB(self,event, x, y, flags, param):

        if event == cv2.EVENT_MOUSEMOVE:
            #print(cross_hairs)
        
            imgCopy = self.img2.copy()
            #cv2.circle(imgCopy, (x, y), 10, (255, 0, 0), -1)
            if self.LEFT_DOWN:
                self.box2=(x,y)
                #DrawBox(imgCopy,box1,box2)
            else:
                self.cross_hairs=(x,y)
                #DrawCrossHairs(imgCopy,cross_hairs,cross_size)
            cam_name=self.P.SETTINGS['MY_CAMERA']
            cv2.imshow(cam_name, imgCopy)

        elif event == cv2.EVENT_LBUTTONDBLCLK:

            #print('MouseCB: Left Button DOUBLE CLOCK:',x, y, flags, param)
            w=self.img2.shape[1]
            h=self.img2.shape[0]
            center=( int(w/2), int(h/2) )
            lr = 2*self.ptz.ifov1*(x-center[0])/w
            ud = 2*self.ptz.ifov2*(y-center[1])/h
            #print('center=',center,'lr=',lr,'ud=',ud)
            self.ptz.rel_move(lr,ud)
        
        elif event == cv2.EVENT_LBUTTONDOWN:

            #print('MouseCB: Left Button DOWN:',x, y, flags, param)
            self.LEFT_DOWN=True
            self.box1=(x,y)
            self.box2=self.box1
            #t1=time()
            #print(t1)
    
        elif event == cv2.EVENT_LBUTTONUP:

            #print('MouseCB: Left Button UP:',x, y, flags, param)
            self.LEFT_DOWN=False
            self.box2=(x,y)
            #t2=time()
            #print(t2)

            if self.box2==self.box1 and False:
                print('Quick click!')

        elif event==cv2.EVENT_MOUSEWHEEL:

            #print('MouseCB: WHEEL:',x, y, flags, param)
            if flags>0:
                print('Zoom in')
            else:
                print('Zoom out')
                
    ############################################################################
    
    def DrawBox(self):
    
        p1 = (self.box1[0],self.box1[1])
        p2 = (self.box1[0],self.box2[1])
        p3 = (self.box2[0],self.box2[1])
        p4 = (self.box2[0],self.box1[1])
        #print(p1,p2,p3,p4)
    
        c  =(0,0,255)  # Red
        th = 2         # Line thickness
    
        cv2.line(self.img2, p1, p2, c, thickness=th)
        cv2.line(self.img2, p2, p3, c, thickness=th)
        cv2.line(self.img2, p3, p4, c, thickness=th)
        cv2.line(self.img2, p4, p1, c, thickness=th)

    def DrawCrossHairs(self):
    
        # If mouse hasn't moved yet, put cross-hairs in the center of the image
        #print(cross_hairs)
        if self.cross_hairs==None:
            center=( int(img.shape[1]/2), int(img.shape[0]/2) )
        else:
            center=self.cross_hairs

        p1 = (center[0], center[1] - self.cross_size)
        p2 = (center[0], center[1] + self.cross_size)
        p3 = (center[0] - self.cross_size, center[1])
        p4 = (center[0] + self.cross_size, center[1])
        #print(p1,p2,p3,p4)

        c  =(0,0,255)  # Red
        th = 2         # Line thickness
    
        cv2.line(self.img2, p1, p2, c, thickness=th)
        cv2.line(self.img2, p3, p4, c, thickness=th)

################################################################################

class VIDEO_DOWNLOADER():
    def __init__(self,P,date,outDir=''):

        self.outputDir = outDir    # directory path where videos will be saved
        self.date = date           # date to download recordings for in format YYYYMMDD
        
        self.host = P.SETTINGS['MY_IP']
        self.user_cloud = P.SETTINGS['MY_CLOUD_USER']
        self.password_cloud = P.SETTINGS['MY_CLOUD_PASSWORD']
        
        self.window_size = 50

        if True:
            print('host=',self.host)
            print('user=',self.user_cloud)
            print('password=',self.password_cloud)
            #sys.exit(0)
        
        print("Connecting to camera...")
        self.tapo = Tapo(self.host, self.user_cloud, self.password_cloud, self.password_cloud)
        print('Getting basic data...')
        print('\nBasic Camera Info:',self.tapo.basicInfo)
        #sys.exit(0)

        self.get_recording_list()
        #sys.exit(0)

        loop = asyncio.get_event_loop()
        loop.run_until_complete(self.download_async())

    def get_recording_list(self):
        print("\nGetting recordings...")
        self.recordings = self.tapo.getRecordings(self.date)
        print('\nRecordings=',self.recordings)
        self.timeCorrection = self.tapo.getTimeCorrection()
        print('\nTime Correction=',self.timeCorrection)

        total=0
        for rec in self.recordings:
            for key in rec:
                t1=rec[key]["startTime"]
                t2=rec[key]["endTime"]
                dt=t2-t1
                total+=dt
                print('\t',key,t1,t2,dt,dt/60)
        print('\nTotal of',total,' secs available =',total/60.,'min =',total/3600.,'hours')
            
    async def download_async(self):
        for rec in self.recordings:
            print('\nDownloading',rec,' ...')
            for key in rec:
                print('\t',key)
                downloader = Downloader( self.tapo,
                                         rec[key]["startTime"],rec[key]["endTime"],
                                         self.timeCorrection,self.outputDir,
                                         None,False,self.window_size)
                async for status in downloader.download():
                    statusString = status["currentAction"] + " " + status["fileName"]
                    if status["progress"] > 0:
                        statusString += (": " + str(round(status["progress"], 2))
                                         + " / " + str(status["total"]) )
                    else:
                        statusString += "..."
                    print(statusString + (" " * 10) + "\r", end="",)
                print("")


################################################################################

# Function to look for a camera on the LAN
def find_camera(mac):
    print('\nLooking for camera with MAC',mac,'...')
    #
    # The linux command to find a device on the LAN with specified MAC address:
    # ip neighbour - lists most devices on the LAN - doesn't show this host?
    # Cameras connected to one of the WiFi extenders show up twice - once with
    # the IP of the extender and a second time with the actual IP we want.
    #
    if True:
        cmd="ip neighbour"
        cmd="ip neighbour | fgrep "+mac
        print('cmd=',cmd)
        ip=subprocess.Popen(cmd, shell=True, stdout=subprocess.PIPE).stdout.read()
        print('ip=',ip)
    
    cmd="ip neighbour | fgrep "+mac+" | tail -1 | cut -f 1 -d ' '"
    print('cmd=',cmd)
    #ip=os.popen(cmd).read()
    ip=subprocess.Popen(cmd, shell=True, stdout=subprocess.PIPE).stdout.read()
    print('ip=',ip)
    #sys.exit(0)
    return ip.decode().strip()
        
################################################################################
        
if __name__ == '__main__':

    from tkinter import mainloop

    print(" ")

    # Command line args
    arg_proc = argparse.ArgumentParser()
    #arg_proc.add_argument("-cam", help="Camera number",
    #                      type=int,default=1)
    arg_proc.add_argument("-cam", help="Camera Name",
                          type=str,default=None)
    arg_proc.add_argument("-download", help="Download videos for given date YYYYMMDD",
                          type=str,default=None)
    arg_proc.add_argument('-settings', action='store_true',
                              help='Update Camera Settings')
    args = arg_proc.parse_args()

    # Handle resource file (settings)
    if False:
        # Old - Single camera per rc file
        ATTRS=['MAC','IP','USER','PASSWORD','CLOUD_USER','CLOUD_PASSWORD']
        rcfile = '.camera'+str(args.cam)+'rc'
        P=CONFIG_PARAMS(rcfile,ATTRS)
    else:
        # Much better - single rc file for all cams
        import json
        P=CAM_CONFIG_PARAMS("~/.camerarc",args.cam)
    
    #print(P)
    print(P.SETTINGS)
    print(P.SETTINGS['MY_IP'])
    #sys.exit(0)

    # Open dialog to change camera settings
    # Need to revise this for multiple cams in single rc file
    if args.settings:
        P.SettingsWin = SETTINGS_GUI(None,P,ATTRS)
        mainloop()
        sys.exit(0)

    # Try to find the camera
    if True:
        ip=find_camera(P.SETTINGS['MY_MAC'])
        if P.SETTINGS['MY_IP']!=ip:
            print("Whoops - LAN device IP doesn't match settings:")
            print('ip=',ip,'\tconfigured=',P.SETTINGS['MY_IP'])
            print('Fix this!!!')
            #sys.exit(0)

    # Download videos
    if args.download!=None:
        downloader=VIDEO_DOWNLOADER(P,args.download)
        sys.exit(0)

    # View and control camera in real-time
    camera=VIDEO_CAMERA(P)
    
    print("\nThat's All Folks!\n")

