#!/usr/bin/env python3

# Name:     ifnethost.py
#
# Function: Given an <interface> argument, run "ip addr show dev <interface>"
#    Get the interface's CIDR <address>/<maskbits>, and pass that as
#    an anrgument to nethostid.py to return the netid/hostid breakdown.
#
# Syntax:    ifnethost.py <interface>
#
# Author:    Howard Sherman

import argparse
import sys
import subprocess

parser = argparse.ArgumentParser(description='Show the CIDR, Network and Host ID for an interface')
parser.add_argument('interface',help='Network Interface')
args=parser.parse_args()

try:
    proc = subprocess.run(["ip", "addr", "show", "dev",args.interface],
            shell=False,check=True,stdout=subprocess.PIPE)
except subprocess.CalledProcessError:
    print(f"Error in Command...Script Aborted")
    sys.exit(1)

stdout = proc.stdout.decode().split('\n')
for line in stdout:
    tokens = line.lstrip().split(sep=' ')
    if tokens[0] == 'inet':
        print(f"{args.interface} IP at {tokens[1]}")
        proc = subprocess.run(["nethostid.py", tokens[1]])
        break
