- When running on a linux machine, you must run as root! or else you get errors :(

For my ping program: 

-maximum icmp_data size is 68 bytes. I.e. can only do up to "-s 68"

-if speicifying the number of packets to send with "-c" command, do NOT keyboard interrupt (i.e. ctrl + c) because the statistics will be incorrect

-You might lose say 1 packet out of 101, but the packet loss rate will be 0% because the loss percentage is too low to properly show, say, a 0.9% packet loss rate

-I'm using the python 'signal' class, and apparently this library doesn't work on a windows system :( so this only works so far in Linux

-if you have a timeout time less than the number of packets sent (with the sending time between packets being 1 second) then there is lots of packet loss because you immdiately stop receiving once the timeout hits zero

-the first argument must be either the website name or its IP address ("python3 rda6526_ping.py www.google.com -i 6") or 
("python3 rda6526_ping.py 8.8.8.8)


Traceroute: 

-Does not work with a keyboard interrupt

"-S" command doesn't work rip 


"python3 rda6526_traceroute.py www.google.com -q 5"

or you can replace the above "www.google.com" with an IPv4 address too 