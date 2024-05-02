#! /usr/bin/python3 -u
############################################################################################
#
# Camera - Rev 0.1
# Copyright (C) 2024 by Joseph B. Attili, aa2il AT arrl DOT net
#
# Simple app to view and control Tapo C500 Video Camera.
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
import cv2
from tapoC500 import TapoC500
from time import time
from settings import CONFIG_PARAMS

############################################################################################

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
        cv2.namedWindow('frame', cv2.WINDOW_NORMAL)
        first_time=True
        
        while(self.cap.isOpened()):
            ret, img = self.cap.read()
    
            # Put frame operations here - e.g. resize
            #print('Original Dimensions : ',img.shape)
            sc = 1 # 0.5
            width = int(sc*img.shape[1])
            height = int(sc*img.shape[0])
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
            cv2.imshow('frame', self.img2)
            if first_time:
                cv2.resizeWindow('frame',width,height)
                #sz=cv2.getWindowImageRect('frame')
                #print(sz,width,height)
                first_time=False

            # Enable mouse callback
            cv2.setMouseCallback('frame', self.MouseCB)
            
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
            
        # Clean-up and quit
        self.cap.release()
        cv2.destroyAllWindows()

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
            cv2.imshow('frame', imgCopy)

        elif event == cv2.EVENT_LBUTTONDBLCLK:

            print('MouseCB: Left Button DOUBLE CLOCK:',x, y, flags, param)
            w=self.img2.shape[1]
            h=self.img2.shape[0]
            center=( int(w/2), int(h/2) )
            lr = 2*self.ptz.ifov1*(x-center[0])/w
            ud = 2*self.ptz.ifov2*(y-center[1])/h
            print('center=',center,'lr=',lr,'ud=',ud)
            self.ptz.rel_move(lr,ud)
        
        elif event == cv2.EVENT_LBUTTONDOWN:

            print('MouseCB: Left Button DOWN:',x, y, flags, param)
            self.LEFT_DOWN=True
            self.box1=(x,y)
            self.box2=self.box1
            #t1=time()
            #print(t1)
    
        elif event == cv2.EVENT_LBUTTONUP:

            print('MouseCB: Left Button UP:',x, y, flags, param)
            self.LEFT_DOWN=False
            self.box2=(x,y)
            #t2=time()
            #print(t2)

            if self.box2==self.box1:
                print('Quick click!')

        elif event==cv2.EVENT_MOUSEWHEEL:

            print('MouseCB: WHEEL:',x, y, flags, param)
            if flags>0:
                print('Zoom in')
            else:
                print('Zoom out')
                

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

############################################################################################
        
if __name__ == '__main__':

    # Handle resource file (settings)
    ATTRS=['IP','USER','PASSWORD']
    P=CONFIG_PARAMS('.camera1rc',ATTRS)
    print(P)
    print(P.SETTINGS)
    
    camera=VIDEO_CAMERA(P)
    
    print("\nThat's All Folks!\n")

