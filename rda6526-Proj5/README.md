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
---

## Traceroute

A Linux-based traceroute implementation built from scratch in Python using raw ICMP sockets.

## Features

- Raw ICMP socket implementation
- Number of ICMP echo request packets to send per hop (`-q`)
- Output addresses numerically instead of numerically and with hostname (`-n`)
- Prints a summary of how many probes were not answered for each hop (`-S`)

- Timeout handling for non-responsive routers (`* * *` behavior)

## How It Works

Traceroute works by sending packets to the destination with progressively increasing TTL values.

- TTL = 1 → packet expires at the first router  
- TTL = 2 → packet expires at the second router  
- This process repeats until the destination host is reached

## Usage

Run with root privileges:

```bash
sudo python3 main.py <destination> [arguments]
```

### Examples

Basic traceroute:

```bash
sudo python3 main.py google.com
```

### Example Output

```text
Traceroute to www.google.com (142.251.153.119), 30 hops max, 64 byte packets
1   _gateway ([my-personal-IP-address]) 52.789ms 35.649ms 40.040ms 
2   107.243.2.12 (107.243.2.12) 119.742ms * 71.721ms 
3   * * * 
4   * * * 
5   * * * 
6   * * * 
7   * * * 
8   * * * 
9   * * * 
10   142.251.153.119 (142.251.153.119) 403.844ms 248.870ms 210.686ms 
```

## Other use cases

Set probe count:

```bash
sudo python3 main.py google.com -q 5
```

Print numeric IP addresses only:

```bash
sudo python3 main.py google.com -n
```

Print unanswered probe summary:

```bash
sudo python3 main.py google.com -S
```


