#!/usr/bin/env -S uv run --script
#
# OLD: /usr/bin/python3 -u 
################################################################################
#
# Camera - Rev 1.0
# Copyright (C) 2024-6 by Joseph B. Attili, joe DOT aa2il AT gmail DOT com
#
# Simple app to view, control and download videos for Tapo C500 and ESP32-cam
# Video Cameras.  This version support multiple cameras and is a work
# in progress.
#
# The code for downloading is based on pytapo by Juraj Nyiri found at 
#         https://github.com/JurajNyiri
#
# Supposed camera ports:
#   443  - HTTPS for control of the camera (services)
#   8800 - Proprietary protocol for video streaming and recordings downloads (if available)
#   554  - RTSP to fetch video stream from the camera (if available)
#   2020 - ONVIF to track detected movement via a binary sensor (if available)
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

import sys,os
import subprocess
import cv2
from tapoC500 import TapoC500
import time
#from settings import CONFIG_PARAMS,SETTINGS_GUI
from datetime import datetime
import numpy as np
#from utils import *
from tapo_discover import *

from pytapo import Tapo
from pytapo.media_stream.downloader import Downloader
import asyncio
from pprint import pprint

################################################################################

class VIDEO_CAMERA():
    def __init__(self,P,cam_name):

        self.P=P
        self.name = cam_name
        self.step=0.1

        # Aliases, for now
        cam_name=cam_name.replace(' ','').replace('BarnAisle','Aisle')
        #if cam_name=='BarnAisle':
        #    cam_name='Aisle'
        #elif cam_name=='Front Door':
        #    cam_name='Frontdoor'
        print(cam_name)
        self.SETTINGS=P.SETTINGS[cam_name]

        IP=self.SETTINGS['IP']
        self.CAM_TYPE=self.SETTINGS['CAM_TYPE']
        if 'USER' in self.SETTINGS:
            USER=self.SETTINGS['USER']
            PASSWORD=self.SETTINGS['PASSWORD']
            STREAM=None
        else:
            USER=None
            PASSWORD=None
            STREAM=self.SETTINGS['STREAM']

        self.cross_hairs=None
        self.cross_size=50
        self.box1=None
        self.box2=None
        self.LEFT_DOWN=False
        if 'ROTATE' in self.SETTINGS:
            self.rotation=self.SETTINGS['ROTATE']
        else:
            self.rotation=None

        self.nframes=0
        self.nrestarts=0
        self.missed=0
        self.t1=None
        self.online=None
        self.img2=None
            
        # See opencv.org for details
        print('Setting up Video Camera - Press ESCAPE to exit ...')

        # Open PTZ controls
        if self.CAM_TYPE=='Tapo':
            print('If we get failure here, probably need to update camera firmware via Tapo app on phone or tablet.')
            self.ptz = TapoC500(IP,USER,PASSWORD)
            self.STREAM_URL=self.ptz.RTSP_URL
        else:
            self.ptz = None
            self.STREAM_URL='http://'+IP+STREAM

        # Open camera video stream
        print('Opening video stream ...',self.STREAM_URL)
        self.cap = cv2.VideoCapture(self.STREAM_URL)

        print('And away we go!')
        #self.run_camera()

    def get_frame(self,width=None,height=None):
        #print('GET FRAME:',width,height)
        
        if self.missed>20 and not self.online:
            return
        ret, img = self.cap.read()

        # Check for failure
        if img is not None:
            self.missed=0
            self.online=True
        elif self.online==None:
            self.online=False
            self.img2=np.zeros((height,width,3),np.uint8)
            return
        else:
            # If the camera has been turned off, try again
            # If too many retries, exit gracefully
            self.missed+=1
            if self.missed<20:
                print(self.name,':\tWhoops - missed image???!!!  nframes=',
                      self.nframes,'\tmissed=',self.missed)
                self.img2=np.zeros((height,width,3),np.uint8)
                return
            else:
                if not self.online:
                    return
                print('*** Camera probably disconeected ***')
                self.nrestarts+=1
                if self.nrestarts<50:
                    print('Re-opening video stream in 10 secs ...',self.STREAM_URL)
                    self.cap.release()
                    time.sleep(10)
                    self.cap = cv2.VideoCapture(self.STREAM_URL)
                    self.img2=np.zeros((height,width,3),np.uint8)
                    return
                else:
                    print('*** Too many restarts - Bailing out! ***')
                    self.cap.release()
                    return
        
        self.nframes+=1
        if self.nframes==1:
            self.t1 = time.perf_counter()
            print(self.name,':\tOriginal Dimensions : ',img.shape,type(img))
        if self.nframes % 100 ==1:
            t2 = time.perf_counter()
            fps = round( 100./(t2-self.t1) , 1)
            print(self.name,':\tRead image',self.nframes,'\t',fps,'fps\tnrestarts=',self.nrestarts)
            self.t1 = t2
            
        # Put frame operations here - e.g. resize
        if width==None:
            width = img.shape[1]
        if height==None:
            height = img.shape[0]
        
        # Do the actual resizing & rotation
        dim = (width, height)
        self.img2 = cv2.resize(img, dim, interpolation = cv2.INTER_AREA)
        if self.rotation in ['CW','90']:
            self.img2 = cv2.rotate(self.img2, cv2.ROTATE_90_CLOCKWISE)
        elif self.rotation in ['CCW','-90']:
            self.img2 = cv2.rotate(self.img2, cv2.ROTATE_90_COUNTERCLOCKWISE)
        elif self.rotation=='180':
            self.img2 = cv2.rotate(self.img2, cv2.ROTATE_180)
        if self.nframes==1:
            print('Resized Dimensions : ',self.img2.shape)
            
        # Add box/cross-hairs
        if self.LEFT_DOWN:
            self.DrawBox()
            self.cross_hairs=None
        else:
            if self.cross_hairs:
                self.DrawCrossHairs()
                
        
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
            cv2.imshow(self.name, imgCopy)

        elif event == cv2.EVENT_LBUTTONDBLCLK:

            if self.ptz:
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
    
        elif event == cv2.EVENT_LBUTTONUP:

            #print('MouseCB: Left Button UP:',x, y, flags, param)
            self.LEFT_DOWN=False
            self.box2=(x,y)

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

############################################################################
        
# Read the streams
def run_cameras(video_cams):

    # Create window to display imagery
    # Do it this way so we can resize it manually if we want to
    cam_name=''
    for vc in video_cams:
        cam_name+=vc.name
    cv2.namedWindow(cam_name, cv2.WINDOW_NORMAL)
    first_time=True

    print('Camera started at',datetime.now())

    # Determine desired image sizes
    ncams=len( video_cams )
    if ncams==1:
        width=None
        height=None
    elif ncams<=6:
        width=640
        height=480
    elif ncams<=9:
        width=640
        height=480
        #width=320
        #height=240
    else:
        print('Too many cameras!',ncams)
        sys.exit(0)

    # Enable mouse callback - need to revisit this for multi cams
    if ncams==1:
        vc=video_cams[0]
        cv2.setMouseCallback(vc.name, vc.MouseCB)
        
    Done=False
    while(not Done):
        
        # Get a frame from each camera
        for vc in video_cams:
            vc.get_frame(width,height)
            if not vc.cap.isOpened():
                if ncams==1:
                    print('Camera has closed:',vc.name)
                    print('Bailing out!')
                    Done = True

        # Compose composite image
        if ncams==1:
            img =video_cams[0].img2
        else:
            img1=video_cams[0].img2
            img2=video_cams[1].img2
            if ncams==2:
                img = cv2.hconcat([img1, img2])
            else:
                img3=video_cams[2].img2
                if ncams>=4:
                    img4=video_cams[3].img2
                else:
                    img4=0*img3
                if ncams in [3,4]:
                    img = cv2.vconcat([
                        cv2.hconcat([img1, img2]),
                        cv2.hconcat([img3, img4]) ])
                else:
                    img5=video_cams[4].img2
                    if ncams>=6:
                        img6=video_cams[5].img2
                    else:
                        img6=0*img5
                    if ncams in [5,6]:
                        img = cv2.vconcat([
                            cv2.hconcat([img1, img2, img3]),
                            cv2.hconcat([img4, img5, img6]) ])
                    else:
                        img7=video_cams[6].img2
                        if ncams>=8:
                            img8=video_cams[7].img2
                        else:
                            img8=0*img7
                        if ncams>=9:
                            img9=video_cams[8].img2
                            img = cv2.vconcat([
                                cv2.hconcat([img1, img2, img3]),
                                cv2.hconcat([img4, img5, img6]),
                                cv2.hconcat([img7, img8, img9]) ])
                        else:
                            img9=0*img8
                            img = cv2.vconcat([
                                cv2.hconcat([img1, img2, img3, img4]),
                                cv2.hconcat([img5, img6, img7, img8]) ])
            
        # Display the composite frame
        cv2.imshow(cam_name,img)
        if first_time:
            cv2.resizeWindow(cam_name,img.shape[1],img.shape[0])
            first_time=False

        # Check for clean exit
        ch = cv2.waitKey(20) # & 0xFF
        if ch>0:
            print('ch=',ch)
            if ch==82 and vc.ptz:
                vc.ptz.rel_move(0,-vc.step)
            elif ch==84 and vc.ptz:
                vc.ptz.rel_move(0,vc.step)
            elif ch==81 and vc.ptz:
                vc.ptz.rel_move(-vc.step,0)
            elif ch==83 and vc.ptz:
                vc.ptz.rel_move(vc.step,0)
            elif ch in [27,ord('q'),ord('Q')]:
                Done = True
                #break
            
        # Check for click on big X to exit also
        try:
            #print(cam_name)
            if cv2.getWindowProperty(cam_name,cv2.WND_PROP_VISIBLE) <= 0:
                print('Blah blah blah')
                break
        except:
            print('Bailing out!')
            break
            
    # Clean-up and quit
    print('Cleaning up ...')
    vc.cap.release()
    cv2.destroyAllWindows()
    print('Camera done at',datetime.now())

############################################################################

class VIDEO_DOWNLOADER():
    def __init__(self,P,cam,date,outDir='recordings'):

        self.date = date           # date to download recordings for in format YYYYMMDD

        self.SETTINGS  = P.SETTINGS[cam]
        self.CAM_TYPE=self.SETTINGS['CAM_TYPE'] 
        if self.CAM_TYPE!='Tapo':
            print('\n*** Recordings only supported for Tapo cameras ***')
            self.recordings = None
            return
        
        self.outputDir = outDir    # directory path where videos will be saved
        os.makedirs(outDir, exist_ok=True)       # Make sure it exists

        self.host      = self.SETTINGS['IP']
        self.user      = self.SETTINGS['USER']
        self.user2     = self.SETTINGS['CLOUD_USER']
        self.password  = self.SETTINGS['PASSWORD']
        self.password2 = self.SETTINGS['CLOUD_PASSWORD']
        self.ctrl_port = 443
        
        self.window_size = 50

        if True:
            print('host           =',self.host,len(self.host))
            print('user           =',self.user,len(self.user))
            print('password       =',self.password,len(self.password))
            print('cloud user     =',self.user2,len(self.user2))
            print('cloud password =',self.password2)
            #sys.exit(0)
        
        print("Connecting to camera...")
        if 0:
            # Orig - doesn't work
            self.tapo = Tapo(self.host, self.user2, self.password2, self.password2,
                             printDebugInformation=True,
                             controlPort=self.ctrl_port,
                             redactConfidentialInformation=False)
        elif 0:
            # Works with older cams
            self.tapo = Tapo(self.host, self.user2, self.password2, self. password2)
        else:
            # Works with both older & newer cams
            # If there is a problem, try updating pytapo, e.g. uvinit
            #self.tapo = Tapo(self.host, "admin", self.password2)
            self.tapo = Tapo(self.host, "admin", self.password2, cloudPassword=self.password2)
        #sys.exit(0)
        print('Getting basic data...')
        print('\nBasic Camera Info:',self.tapo.basicInfo)
        #sys.exit(0)

        self.get_recording_list()
        #sys.exit(0)
        return

        loop = asyncio.get_event_loop()
        loop.run_until_complete(self.download_recordings())

    def get_recording_list(self):
        print("\nGetting recordings...")
        self.recordings = self.tapo.getRecordings(self.date)
        #print('\nRecordings=',self.recordings)
        print(f"Found {len(self.recordings)} recordings")
        for rec in self.recordings:
            print(rec)
        
        self.timeCorrection = self.tapo.getTimeCorrection()
        print('\nTime Correction=',self.timeCorrection)

        total=0
        print('\tkey\t\t\tt1\t\t\tt2\t\tdt\tdt/60')
        for rec in self.recordings:
            for key in rec:
                t1=rec[key]["startTime"] 
                t2=rec[key]["endTime"]  
                dt=t2-t1
                total+=dt
                print(key,'\t',datetime.fromtimestamp(t1),'\t',datetime.fromtimestamp(t2),
                      '\t',dt,'\t',dt/60)
        print('\nTotal of',total,' secs available =',total/60.,'min =',total/3600.,'hours')
            
    async def download_recordings(self):
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
    from params import *

    print(" ")

    # Command line args
    P=PARAMS()
    print('P=',P)
    pprint(vars(P))
    #sys.exit(0)

    # Open dialog to change camera settings
    # Need to revise this for multiple cams in single rc file
    if P.UPDATE_SETTINGS:
        print('*** NEED TO REVISIT THIS CODE FOR MULTIPLE CAMERAS !!! ***')
        sys.exit(0)
        P.SettingsWin = SETTINGS_GUI(None,P,ATTRS)
        mainloop()
        sys.exit(0)

    # Try to find the camera
    if False:
        cam=P.CAMS
        print('cam=',cam)
        SETTINGS=P.SETTINGS[cam]
        print(SETTINGS)
        ip=find_camera(P.SETTINGS[cam]['MAC'])
        if P.SETTINGS[cam]['IP']!=ip:
            print("Whoops - LAN device IP doesn't match settings:")
            print('ip=',ip,'\tconfigured=',P.SETTINGS[cam]['IP'])
            print('Fix this!!!')
            sys.exit(0)

    # Find all the cameras - experimental for now
    # Eventually, should be able to slim down .rc file significantly since most info can
    # be obtained directly from the cameras
    if True:
        P.CLOUD_USER,P.CLOUD_PASSWORD,IP=read_cam_rcfile("~/.camerarc")
        print(P.CLOUD_USER,'\t',P.CLOUD_PASSWORD,'\t',IP)
        Devices=asyncio.run( find_tapo(P.CLOUD_USER,P.CLOUD_PASSWORD,IP) )   # "192.168.0.255") )
        print('\nDevices=',Devices)        
        Cameras,Bulbs,Plugs,Other = sort_devices(Devices)
        print('\nCameras=',Cameras)
        if P.CAMS==None:
            P.CAMS=[]
            for cam in Cameras:
                P.CAMS.append( cam['NAME'] )
        
        #sys.exit(0)

    # View and control cameras and/or download recorded videos
    cameras=[]
    print('cams=',P.CAMS)
    if P.DOWNLOAD!=None:
        if len(P.DOWNLOAD)>0:
            date = P.DOWNLOAD[0]
        else:
            date=datetime.strftime(datetime.now(),'%Y%m%d')
        print('date=',date)
    for cam in P.CAMS:
        
        if P.DOWNLOAD==None:
            
            # Open this camera for viewing
            vc = VIDEO_CAMERA(P,cam)
            ret, img = vc.cap.read()
            if img is not None:
                cameras.append( vc )
            else:
                print('Unable to open camera',vc.name)
                
        else:
            
            # Download recordings from this camera
            dl=VIDEO_DOWNLOADER(P,cam,date,outDir='recordings/'+cam)
            if dl.recordings!=None and False:
                asyncio.run(dl.download_recordings())

    # View cams in real-time
    if P.DOWNLOAD==None:
        run_cameras(cameras)
    
    print("\nThat's All Folks!\n")

