# Packet Capture Analyzer


A command-line network packet analysis tool for inspecting and filtering packet capture (`.pcap`) files.

This project parses packet captures and reconstructs protocol header information across multiple networking layers, including Ethernet, IPv4, ICMP, TCP, and UDP traffic.

I used the "scapy", "sys", and "socket" libraries

An example of how to run my program in terminal/command line (I’ve only tested in
the PyCharm IDE):

pktsniffer -r NameOfFile.pcap host 2.2.2.2 -c 42

The above example reads in a .pcap file from “NameOfFile”, prints out a maximum
of “42” packets, but only prints up to “42” packets those whose source or destination
address matches the IPv4 address “2.2.2.2”

Commands:
1. -host [IP-address]
a. Prints only IP packets whose ‘source’ or ‘destination’ IPv4 addresses
match [IP-address]

2. -port [Port-Number]
a. Prints only TCP and UDP packets that have either their source or
destination ports as [Port-Number]

3. -ip
a. Prints all IP packets, but no other type of packet

4. -tcp
a. Prints all TCP packets, but no other type of packet

5. -udp
a. Prints all UDP packets, but no other type of packet

6. -icmp
a. Prints all ICMP packets, but no other type of packet

7. -net [Net-Address]
a. Prints all IP packets that are up to and include the sub-group of
[Net-Address] address
i. ex) -net 128.215 (or -net 128.215.) prints out all IP packets
whose source/destination IPv4 address starts with exactly
128.215 (or 128.215.) but can end in any form of “128.215.x.x”
(i.e. will print all address from 128.215.0.0 to 128.215.255.255
ii. ex) -net 128.215.3 (or -net 128.215.3.) prints out all IP packets
whose source/destination IPv4 address starts with exactly
128.215.3 (or 128.215.3.) but can end in any form of
“128.215.3.x” (i.e. will print all addresses from 128.215.3.0 to
128.215.3.255)
iii. ex) -net 0 (or -net 0., -net 0.0, -net 0.0., -net 0.0.0, -net 0.0.0. or
-net 0.0.0.0) prints out all IP addresses

8. -c [Max-Packet-Count]
a. Prints up to [Max-Packet-Count] number of packets from the .pcap file

##Example output: 

packet number 349:

ETHER:  ----- Ether Header -----

ETHER: 

ETHER: Packet size = 75 bytes

ETHER: Destination = 01:00:5e:00:00:fc

ETHER: Source = cc:f9:e4:e8:bc:af

ETHER: Ethertype = 0800 (IP)

ETHER: 


IP:  ----- IP Header -----

IP: 

IP: Version = 4

IP: Header length = 20 bytes

IP: Type of service = 0x00

IP:    xxx. .... = 0 (precedence)

IP:    ...0 .... = normal delay

IP:    .... 0... = normal throughput

IP:    .... .0.. = normal reliability

IP: Total length = 61 bytes

IP: Identification = 34827

IP: Flags = 0x0

IP:    .0.. .... = can fragment

IP:    ..0. .... = last fragment

IP: Fragment offset = 0 bytes

IP: Time to live = 1 seconds/hops

IP: Protocol = 17 (UDP)

IP: Header checksum = 0x5117

IP: Source address = 129.21.126.124, (hostname unknown)

IP: Destination address = 224.0.0.252, (hostname unknown)

IP: No options

IP: 


UDP: ----- UDP Header -----

UDP: Source port = 65227

UDP: Destination port = 5355

UDP: Length = 41

UDP: Checksum = 0xb4ea




