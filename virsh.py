#!/usr/bin/env python
"""
Use the ansible host inventory and the virt module to startup/shutdown VM's thru KVM
"""
import yaml
import sys
import subprocess
import argparse
import json
import pprint

parser = argparse.ArgumentParser(description='virsh processing of hosts in ansible inventory')
parser.add_argument('--group')
parser.add_argument('--host')
parser.add_argument('--action')
parser.add_argument('--list',action='store_true')
parser.add_argument('--listall',action='store_true')
parser.add_argument('--start',action='store_true')
parser.add_argument('--stop',action='store_true')
parser.add_argument('--shutdown',action='store_true')
parser.add_argument('--destroy',action='store_true')
args = parser.parse_args()


hosts = []
commands = []
inventory = {}
valid_actions = ['start', 'stop', 'shutdown', 'destroy']
stated_actions = set()


def addHosts(group,hostset):
    if 'children' in inventory[group]:
        for subgroup in inventory[group]['children']:
            addHosts(subgroup,hostset)
    elif 'hosts' in inventory[group]:
        for host in inventory[group]['hosts']:
            hostset.add(host)

if args.start:
    action = 'start'
    stated_actions.add(action)
if args.stop:
    action = 'shutdown'
    stated_actions.add(action)
if args.shutdown:
    action = 'shutdown'
    stated_actions.add(action)
if args.destroy:
    action = 'destroy'
    stated_actions.add(action)
if args.action:
    action  = args.action
    stated_actions.add(action)
if len(stated_actions) > 1:
    print(f"Error - one and only one Action can be specified")
    sys.exit(1)

group = args.group
host = args.host

# If --list, then we're just listing the running VMs:
if args.list:
    commands.append( 'ansible hypervsor -b -m virt -a "command=list_vms state=running"')
elif args.listall:
    commands.append( 'ansible hypervsor -b -m virt -a "command=list_vms"')
else:
    proc = None
    command = "/usr/bin/ansible-inventory --list"
    try:
        proc = subprocess.run(command,shell=True,check=True,stdout=subprocess.PIPE)
        inventory = json.loads(proc.stdout.decode())
    except subprocess.SubprocessError:
        print(f"Error in Command: {command}...Script Aborted")
        sys.exit(101)

    # Remove the '_meta' and 'ungrouped' groups  from inventory
    del inventory['_meta']
    del inventory['ungrouped']
    inventory['all']['children'].remove('ungrouped')

    # Get all the hosts
    allhosts = set()
    addHosts('all',allhosts)

    hostset = set()

    if host and host in allhosts:
        hostset.add(host)       
    elif group and group in inventory.keys():
        addHosts(group,hostset)

    if not hostset:
        print(f"Error..host/group not found in inventory...Execution Aborted")
        sys.exit(102)

    hosts = sorted(list(hostset))


# Make a list of commands, one for each host
for host in hosts:
    commands.append('/usr/bin/ansible hypervsor -b -m virt -a "name=' + host + '.localnet.com' + ' command='+action+'"')
# Run the list of commands
for command in commands:
    print(command)
    proc = subprocess.run(command,shell=True,check=False)

