#!/usr/bin/env python
"""
Use the ansible host inventory and the virt module to startup/shutdown VM's thru KVM

With Ansible, the control node can only control managed nodes that are running.

In a small KVM lab environment, though, where the control and managed nodes are all kvms, 
by defining the KVM host as a managed node, through the Ansible virt module the control
node can issue commands to startup/shutdown/kill managed nodes.

Furthermore, the ansible-inventory command can be engaged so that commands to the KVM host can be 
made on behalf of hosts AND groups defined in the inventory.

This script exploits these features so that from the Ansible control node managed nodes can be started/stopped/killed via the KVM host, 
utilizing KVM's virsh command.

Assumptions:
  1) All managed nodes are defined to KVM with a common domain, (kvm_domain). They are named to KVM by their FQDNs.
  2) To Ansible, though, the managed nodes are defined by their hostnames, not their FQDNs. 
  3) Name resolution by the control node for the managed nodes is done via hostfile entries, ssh config entries, ansible_hostname variables 
     or some other mechanism so that the nodes can be defined in the Ansible inventory by their hostnames, not their FQDNs.
  4) The managed nodes to be controlled via this script are defined in all:!ungrouped, i.e. they DO NOT belong to the 'ungrouped' group.
  5) The Ansible control node and the KVM host node ARE ungrouped, so that they cannot be inadvertently stopped/started/killed by this script.

Examples:
  List the running VMs:
     virsh.py --list

  Startup a host:
     virsh.py --host centoshost --start
 
  Shutdown a group's hosts:
     virsh.py --group ubuntugroup --stop

  Kill (ungracefully stop) a host:
     virsh.py --host myhost --kill

  Shutdown all the hosts in Ansible inventory:
    virsh.py --group all --stop
"""

import sys
import subprocess
import argparse
import json
import re

# Global variables
kvm_host = "hypervsor"
kvm_domain = "localnet.com"
ansible = "/usr/bin/ansible"
ansible_inventory = "/usr/bin/ansible-inventory"
action = None
stated_actions = set()
group = None
host  = None
hosts_to_process_list = []
running_hosts = []
command = None
commands = []
inventory = {}

def addHosts(group,hosts_to_process):
    if 'children' in inventory[group]:
        for subgroup in inventory[group]['children']:
            addHosts(subgroup,hosts_to_process)
    elif 'hosts' in inventory[group]:
        for host in inventory[group]['hosts']:
            hosts_to_process.add(host)

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
    proc = None
    # Make sure there's an action
    if not action:
        print(f"Error - no action  (--start|--stop|--kill) specified...Execution Aborted")
        sys.exit(101)

    # Get the running hosts (VMs) 
    command = ansible + ' ' + kvm_host + ' -b -m virt -a "command=list_vms state=running"'
    try:
        proc = subprocess.run(command,shell=True,check=True,stdout=subprocess.PIPE)
        # output has embedded json starting at "{" - need to skip the preceding text
        output = ''.join(proc.stdout.decode().splitlines())
        # Hop to the '{'
        output = output[output.index('{'):]
        # Now load it as json
        running_hosts_json = json.loads(output)
        running_hosts_full = running_hosts_json['list_vms']
    except Exception:
        print(f"Error in Command: {command}...Script Aborted")
        sys.exit(102)
    # Trim down running hosts' names to match those in Ansible Inventory
    running_hosts = [ ]
    for running_host in running_hosts_full:
        if running_host.find('.'+kvm_domain) > -1:              # host name ends in KVM domain?
            running_hosts.append(running_host.split('.')[0])    # Yes: strip KVM domain off
        else:
            running_hosts.append(running_host)                  # No: leave host name as is
    
    # Grab the ansible inventory
    command = ansible_inventory + ' --list'
    try:
        proc = subprocess.run(command,shell=True,check=True,stdout=subprocess.PIPE)
        inventory = json.loads(proc.stdout.decode())
    except subprocess.SubprocessError:
        print(f"Error in Command: {command}...Script Aborted")
        sys.exit(103)

    # Trim out the '_meta' and 'ungrouped' groups, so they can't be --group arguments
    del inventory['_meta']
    del inventory['ungrouped']
    inventory['all']['children'].remove('ungrouped')

    # Get all the hosts, i.e. the hosts under the 'all' group:
    all_hosts = set()
    addHosts('all',all_hosts)

    # Get the host(s) to process from the --host|--group argument
    hosts_to_process = set()
    if host and host in all_hosts:
        hosts_to_process.add(host)       
    elif group and group in inventory.keys():
        addHosts(group,hosts_to_process)

    # If no hosts to process, then the --host|--group argument wasn't found
    if not hosts_to_process:
        print(f"Error..host/group not found in inventory...Execution Aborted")
        sys.exit(104)

    # For --start, filter out the hosts that are already running
    # For --stop|--kill, filter out the hosts that are not running
    hosts_to_remove = set()
    for host in hosts_to_process:
        if args.start and host in running_hosts:
            print(f"--start specified and {host} already running...bypass")
            hosts_to_remove.add(host)
        elif (args.stop or args.kill) and host not in running_hosts:
            print(f"--stop|--kill specified and {host} not running...bypass")
            hosts_to_remove.add(host)

    hosts_to_process_list = sorted(list(hosts_to_process - hosts_to_remove))

    if not hosts_to_process_list:
        print(f"No hosts to process...exiting")
        sys.exit(0)

# Make a list of commands, one for each host
for host in hosts_to_process_list:
    if host.find('.') == -1:                                                                                                            # '.' in host name?
        commands.append(ansible + ' ' + kvm_host + ' -b -m virt -a "name=' + host + '.' + kvm_domain  + ' command=' + action + '"')     # No: Add on KVM domain
    else:
        commands.append(ansible + ' ' + kvm_host + ' -b -m virt -a "name=' + host + ' command=' + action + '"')                         # Yes: leave it alone
# Run the commands
for command in commands:
    print(command)
    proc = subprocess.run(command,shell=True,check=False)

