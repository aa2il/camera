#!/usr/bin/env -S uv run --script

import sys
import scapy.all as scapy

def scan(ip_range):
    print(f"Scanning IP range: {ip_range}")
    
    arp_request = scapy.ARP(pdst=ip_range)
    broadcast = scapy.Ether(dst="ff:ff:ff:ff:ff:ff")
    arp_request_broadcast = broadcast / arp_request
    
    print("Sending ARP requests...")
    answered_list = scapy.srp(arp_request_broadcast, timeout=5, verbose=True)[0]
    
    if not answered_list:
        print("No responses received.")
    else:
        print("Responses received.")
    
    devices = []
    for element in answered_list:
        device = {'ip': element[1].psrc, 'mac': element[1].hwsrc}
        devices.append(device)
        print(f"Device found: IP = {device['ip']}, MAC = {device['mac']}")
    
    return devices


def display_devices(devices):
    if devices:
        print("\nIP\t\t\tMAC Address")
        print("-----------------------------------------")
        for device in devices:
            print(f"{device['ip']}\t\t{device['mac']}")
    else:
        print("No devices found.")


def scan_network(ip_range):
    devices = scan(ip_range)
    display_devices(devices)

if __name__ == "__main__":
    ip_range = '192.168.0.0/24'
    scan_network(ip_range)

        

sys.exit(0)






import scapy.all as scapy
import sys

request = scapy.ARP()
print('\nsummary=',request.summary())
print('\nshow=',request.show())
print('\nls=',scapy.ls(scapy.ARP()))

request.pdst = 'x'
broadcast = scapy.Ether()

broadcast.dst = 'ff:ff:ff:ff:ff:ff'

request_broadcast = broadcast / request
clients = scapy.srp(request_broadcast, timeout = 1)[0]
for element in clients:
    print(element[1].psrc + "      " + element[1].hwsrc)
    

sys.exit(0)



# This replicates what laptop does
import subprocess

ADDR="192.168.0.0"
CMD=['nmap', '-sP', ADDR+'/24']

# This replicates what laptop does
print('\nCalling nmap ...')
result = subprocess.run(CMD, stdout=subprocess.PIPE)
out=result.stdout.decode('utf-8')
print(out)

print(' ')
for line in out.splitlines():
    ADDR2=ADDR[:-2]
    if ADDR2 in line:
        addr=ADDR2+line.split(ADDR2)[1].replace(')','')
        print('\n',line)
        print('\t',addr)
        
        CMD2=['nbtscan','-s','" "',addr]
        n = subprocess.run(CMD2, stdout=subprocess.PIPE).stdout.decode('utf-8')
        print('\tn=',n)

        CMD3=['arp','-a',addr]
        a = subprocess.run(CMD3, stdout=subprocess.PIPE).stdout.decode('utf-8')
        #print('\ta=',a)
        mac=a.split(' ')[3]
        print('\tmac=',mac)

        if mac == "e2:ea:c4:c8:82:45":
            print("\tDriveway Camera 3")
        elif mac == "20:4e:7f:58:0a:04":
            print("\tBarn Camera")
        elif mac == "98:25:4a:03:3e:90":
            print("\tOutside Camera 1")

sys.exit(0)
        
"""
for ping in range(1,10):
    address = "127.0.0." + str(ping)
    res = subprocess.call(['ping', '-c', '3', address])
    if res == 0:
        print( "ping to", address, "OK")
    elif res == 2:
        print("no response from", address)
    else:
        print("ping to", address, "failed!")
"""
