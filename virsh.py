#!/usr/bin/env python
"""
Use the ansible host inventory and the virt module to startup/shutdown VM's thru KVM
"""

import sys
import subprocess
import argparse
import json

# Global variables
kvm_host = "hypervsor"
kvm_domain = "localnet.com"
ansible = "/usr/bin/ansible"
ansible_inventory = "/usr/bin/ansible-inventory"
action = None
stated_actions = set()
group = None
host  = None
hosts = []
command = None
commands = []
inventory = {}

def addHosts(group,host_set):
    if 'children' in inventory[group]:
        for subgroup in inventory[group]['children']:
            addHosts(subgroup,host_set)
    elif 'hosts' in inventory[group]:
        for host in inventory[group]['hosts']:
            host_set.add(host)

parser = argparse.ArgumentParser(description='virsh KVM processing of hosts in ansible inventory')
parser.add_argument('--group')
parser.add_argument('--host')
parser.add_argument('--list',action='store_true')
parser.add_argument('--listall',action='store_true')
parser.add_argument('--start',action='store_true')
parser.add_argument('--stop',action='store_true')
parser.add_argument('--kill',action='store_true')
args = parser.parse_args()

# Make sure only one action of --start|--stop|--kill is specified
host = args.host
group = args.group
if args.start:
    action = 'start'
    stated_actions.add(action)
if args.stop:
    action = 'shutdown'
    stated_actions.add(action)
if args.kill:
    action = 'destroy'
    stated_actions.add(action)
if len(stated_actions) > 1:
    print(f"Error - one and only one of --start|--stop|--kill can be specified")
    sys.exit(100)


# If --list, then we're just listing the running VMs:
if args.list:
    commands.append( ansible + ' ' + kvm_host + ' -b -m virt -a "command=list_vms state=running"')
# If --listall, then we're just listing all the VMs:
elif args.listall:
    commands.append( ansible + ' ' + kvm_host + ' -b -m virt -a "command=list_vms"')
else:
    # Make sure there's an action
    if not action:
        print(f"Error - no action  (--start|--stop|--kill) specified...Execution Aborted")
        sys.exit(101)
    # Grab the ansible inventory
    proc = None
    command = ansible_inventory + ' --list'
    try:
        proc = subprocess.run(command,shell=True,check=True,stdout=subprocess.PIPE)
        inventory = json.loads(proc.stdout.decode())
    except subprocess.SubprocessError:
        print(f"Error in Command: {command}...Script Aborted")
        sys.exit(101)

    # Trim out the '_meta' and 'ungrouped' groups, so they can't be --group arguments
    del inventory['_meta']
    del inventory['ungrouped']
    inventory['all']['children'].remove('ungrouped')

    # Get all the hosts, i.e. the hosts under the 'all' group:
    all_hosts = set()
    addHosts('all',all_hosts)

    # Get the host(s) to process from the --host|--group argument
    host_set = set()
    if host and host in all_hosts:
        host_set.add(host)       
    elif group and group in inventory.keys():
        addHosts(group,host_set)

    # If no hosts to process, then the --host|--group argument wasn't found
    if not host_set:
        print(f"Error..host/group not found in inventory...Execution Aborted")
        sys.exit(102)

    # Make a list of the host(s) to process
    hosts = sorted(list(host_set))


# Make a list of commands, one for each host
for host in hosts:
    commands.append(ansible + ' ' + kvm_host + ' -b -m virt -a "name=' + host + '.' + kvm_domain  + ' command=' + action + '"')
# Run the commands
# "Normal" exceptions (the code doesn't handle at the ansible libvirt module level):
#     --stop|--kill: libvirt.libvirtError: Requested operation is not valid: domain is not running
#     --start:       libvirt.libvirtError: Requested operation is not valid: domain is already running
for command in commands:
    print(command)
    proc = subprocess.run(command,shell=True,check=False)

