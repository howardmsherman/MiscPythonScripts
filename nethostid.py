#!/usr/bin/env python3

# Name:     nethostid.py
#
# Desc:     given an IPv4 address in CIDR format, compute and print the netid and hostid
#
# Syntax:   nethostid.py <IPv4 Addr/Mask bits>
#
# Author:   Howard Sherman

from argparse import ArgumentParser
from socket import inet_aton, inet_ntoa
from sys import exit
from math import pow

def badCIDRaddr():
    print(f"Error: not a valid IPv4 address in CIDR '<IP Addr>/<netid length>' format: {cidraddr}")
    print(f"EXECUTION ABORTED")
    exit(1)

parser = ArgumentParser(description='Given an IPv4 address in CIDR format, compute and print the netid and hostid')
parser.add_argument('cidraddr',help="IPv4 address in CIDR '<IP Addr>/<netid length>' format")

args=parser.parse_args()        # Parse
cidraddr = args.cidraddr        # Snag the IPv4 CIDR addr

slashidx = cidraddr.find('/')   # Where's the '/' ?
if slashidx < 7 or slashidx > 15:
    badCIDRaddr()

# Separate the IPv4 Address and the maskbits
ipv4addr_str,netidlen_str = cidraddr.split('/',1)

# Validate the IP
try:
    ipv4addr = inet_aton(ipv4addr_str)
except OSError:
    badCIDRaddr()

# Validate the maskbits
try:
    netidlen = int(netidlen_str)
except ValueError:
    badCIDRaddr()

# Finally, make sure 8 <=  netidlen <= 31
if netidlen < 8 or netidlen > 31:
    badCIDRaddr()

# Get the bit masks for the NetID and the HostID
allones = int(pow(2,32)-1)
hostmask = allones >> netidlen
netmask = allones  ^ hostmask

ipv4addr_int = int.from_bytes(ipv4addr, byteorder='big', signed=False)
netid_int = ipv4addr_int & netmask
netid = netid_int.to_bytes(4, byteorder='big')
hostid = ipv4addr_int & hostmask

print(f"Netid: {inet_ntoa(netid)}")
print(f"Hostid: {hostid}")

