#! /usr/bin/python3 -u

# THIS WORKS!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!

from pytapo import Tapo
from pytapo.media_stream.downloader import Downloader
import asyncio
import os

import sys
from settings import CONFIG_PARAMS
ATTRS=['IP','USER','PASSWORD','CLOUD_USER','CLOUD_PASSWORD']
rcfile = '.camera1rc'
P=CONFIG_PARAMS(rcfile,ATTRS)
print(P.SETTINGS)
#sys.exit(0)

# mandatory
outputDir = ''        # os.environ.get("OUTPUT")  # directory path where videos will be saved
date = '20240520'     # os.environ.get("DATE")  # date to download recordings for in format YYYYMMDD
host = P.SETTINGS['MY_IP']
user_cloud = P.SETTINGS['MY_CLOUD_USER']
password_cloud = P.SETTINGS['MY_CLOUD_PASSWORD']

# optional
window_size = os.environ.get(
    "WINDOW_SIZE"
)  # set to prefferred window size, affects download speed and stability, recommended: 50

print("Connecting to camera...")
tapo = Tapo(host, user_cloud, password_cloud, password_cloud)
print('Getting basic data...')
print('\nBasic Camera Info:',tapo.basicInfo)

async def download_async():
    print("\nGetting recordings...")
    recordings = tapo.getRecordings(date)
    print('\nRecordings=',recordings)
    timeCorrection = tapo.getTimeCorrection()
    print('\nTime Correction=',timeCorrection)
    
    for recording in recordings:
        print('\nDownloading',recording,' ...')
        for key in recording:
            print('\t',key)
            downloader = Downloader(
                tapo,
                recording[key]["startTime"],
                recording[key]["endTime"],
                timeCorrection,
                outputDir,
                None,
                False,
                window_size,
            )
            async for status in downloader.download():
                statusString = status["currentAction"] + " " + status["fileName"]
                if status["progress"] > 0:
                    statusString += (
                        ": "
                        + str(round(status["progress"], 2))
                        + " / "
                        + str(status["total"])
                    )
                else:
                    statusString += "..."
                print(
                    statusString + (" " * 10) + "\r",
                    end="",
                )
            print("")


loop = asyncio.get_event_loop()
loop.run_until_complete(download_async())
