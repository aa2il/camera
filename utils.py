import sys,os
import json

def read_cam_rcfile(fname):
    rcfile=os.path.expanduser(fname)
    with open(rcfile) as json_data_file:
        cams = json.load(json_data_file)
    SETTINGS = cams[0]
    #print('Settings=',SETTINGS)
    USER     = SETTINGS['CLOUD_USER']
    PASSWORD = SETTINGS['CLOUD_PASSWORD']
    IP       = SETTINGS['IP']

    ip2=IP.split('.')
    ip2[3]='255'
    IP2=".".join(ip2)
    
    return USER,PASSWORD,IP2



def sort_devices(Devices,VERBOSITY=0):
    Cameras=[]
    Plugs=[]
    Bulbs=[]
    Other=[]
    for dev in Devices:
        if dev['MODEL'][0]=='C':    # in ['C500','C510W']:
            Cameras.append(dev)
        elif dev['MODEL'][0]=='L':   # in ['L530']:
            Bulbs.append(dev)
        else:
            Other.append(dev)

    if VERBOSITY>0:
        print('\nCameras=',Cameras)
        print('\nBulbs=',Bulbs)
        print('\nPlugs=',Plugs)
        print('\nOther=',Other)
            
    return Cameras,Bulbs,Plugs,Other
    

