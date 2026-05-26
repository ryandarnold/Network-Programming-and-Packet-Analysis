# Custom Ping and Traceroute Utility

## Ping

A Linux-style `ping` python program using raw ICMP sockets. I manually construct ICMP Echo Request packets, compute checksums, and measure network round-trip time (RTT).

### Features

- ICMP Echo Request/Reply using raw sockets
- Custom checksum generation
- Configurable packet count (`-c`)
- Adjustable wait interval (`-i`)
- Custom packet size (`-s`)
- Timeout support (`-t`)
- RTT statistics (`min/avg/max/mdev`)
- Packet loss reporting

### Requirements

- Python3
- Linux 
- Root privileges (`sudo`)

### Usage

```bash
sudo python3 ping.py <IPv4 destination> [options]
```

### Options

| Option | Description |
|--------|-------------|
| `-c` | Number of packets to send |
| `-i` | Wait time between packets (seconds) |
| `-s` | Packet payload size (bytes) |
| `-t` | Timeout before termination (seconds) |
| `-h` or `--help` | Show help menu |

### Example

Ping Google 3 times:

```bash
sudo python3 ping.py www.google.com -c 3
```

### Example Output

```text
PING www.google.com (142.251.156.119) 56(64) bytes of data
64 bytes from 142.251.156.119: icmp_seq=1 ttl=63 time=180.9 ms
64 bytes from 142.251.156.119: icmp_seq=2 ttl=63 time=280.3 ms
64 bytes from 142.251.156.119: icmp_seq=3 ttl=63 time=274.6 ms
--- 142.251.156.119 ping statistics ---
3 packets transmitted, 3 received, 0% packet loss, time 3742ms
rtt min/avg/max/mdev = 180.903/245.315/280.362/55.855

Process finished with exit code 0
```


## Traceroute

hi
