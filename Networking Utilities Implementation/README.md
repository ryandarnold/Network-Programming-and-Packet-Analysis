# Network Tools

Implementation of Linux networking utilities "route" and "ifconfig" in Python

## Reimplementation of the 'route' command using the "sys" library

Example output: 

	Kernel IP routing table
	Destination       Gateway           Genmask           Flags    Metric   Ref      Use     Iface
	default           172.17.0.1        0.0.0.0           UG       0        0        0       eth0    
	172.17.0.0        0.0.0.0           255.255.0.0       U        0        0        0       eth0 


## Reimplementation of the 'ifconfig' command using the "psutil" and "netifaces" libraries

Example output: 


	enp0s3: flags=4163<UP,BROADCAST,RUNNING,MULTICAST> mtu 1500
		inet 10.0.2.15 netmask 255.255.255.0 broadcast 10.0.2.255
		inet6 fd17:625c:f037:2:a00:27ff:fe18:8024 prefixlen 64 scopeid 0x20<link>
		ether 08:00:27:18:80:24 
		RX packets 16083 bytes 23060837 
		RX errors 0 dropped 0 
		TX packets 5121 bytes 378964 0 
		TX errors 0 dropped 0

	lo: flags=73<UP,LOOPBACK,RUNNING> mtu 65536
		inet 127.0.0.1 netmask 255.0.0.0
		inet6 ::1 prefixlen 128 scopeid 0x10<host>
		loop 
		RX packets 489 bytes 42064 
		RX errors 0 dropped 0 
		TX packets 489 bytes 42064 0 
		TX errors 0 dropped 0

