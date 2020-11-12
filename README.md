# MiscPythonScripts

### nethostid.py 
- takes a CIDR address as an argument, shows the Netid, Hostid, and Broadcast

### ifnethost.py
- takes an interface name as an argument, finds its inet address and calls nethostid.py

``
[ec2-user@ip-10-16-126-5 ~]$ ip a
1: lo: <LOOPBACK,UP,LOWER_UP> mtu 65536 qdisc noqueue state UNKNOWN group default qlen 1000
    link/loopback 00:00:00:00:00:00 brd 00:00:00:00:00:00
    inet 127.0.0.1/8 scope host lo
       valid_lft forever preferred_lft forever
    inet6 ::1/128 scope host 
       valid_lft forever preferred_lft forever
2: eth0: <BROADCAST,MULTICAST,UP,LOWER_UP> mtu 9001 qdisc pfifo_fast state UP group default qlen 1000
    link/ether 02:11:48:6d:4f:0b brd ff:ff:ff:ff:ff:ff
    inet 10.16.126.5/20 brd 10.16.127.255 scope global dynamic eth0
       valid_lft 3314sec preferred_lft 3314sec
    inet6 2600:1f18:c21:8307:17da:bee6:d38:cadf/128 scope global dynamic 
       valid_lft 390sec preferred_lft 90sec
    inet6 fe80::11:48ff:fe6d:4f0b/64 scope link 
       valid_lft forever preferred_lft forever
[ec2-user@ip-10-16-126-5 ~]$ 
[ec2-user@ip-10-16-126-5 ~]$ 
[ec2-user@ip-10-16-126-5 ~]$ nethostid.py 10.16.126.5/20
CIDR Addr:       10.16.126.5/20
Netid:              10.16.112.0
Hostid:                    3589
Broadcast:        10.16.127.255
[ec2-user@ip-10-16-126-5 ~]$ 
[ec2-user@ip-10-16-126-5 ~]$ 
[ec2-user@ip-10-16-126-5 ~]$ ifnethost.py eth0
eth0 IP at 10.16.126.5/20
CIDR Addr:       10.16.126.5/20
Netid:              10.16.112.0
Hostid:                    3589
Broadcast:        10.16.127.255
[ec2-user@ip-10-16-126-5 ~]$ 
[ec2-user@ip-10-16-126-5 ~]$ 
[ec2-user@ip-10-16-126-5 ~]$ 
```


