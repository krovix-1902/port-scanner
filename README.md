# Simple Port Scanner

A lightweight TCP port scanner written in Python. It resolves a target hostname and checks a range of ports to report which ones are open. Built as a hands-on project for learning network fundamentals and socket programming.

## Features

- Resolves a hostname or IP to a target address
- Scans any range of ports you specify
- Reports open ports as it finds them
- Graceful handling of unresolvable hosts and Ctrl+C interrupts

## Requirements

- Python 3.x (uses only the standard library — no installs needed)

## Usage

```
python ports_scan.py <host> <start_port> <end_port>
```

On Windows you may need to use `py` instead of `python`.

### Example

```
py ports_scan.py scanme.nmap.org 1 100
```

`scanme.nmap.org` is a server the Nmap project maintains specifically for people to legally test scanners against.

### Sample output

```
----------------------------------------------------------------------
Simple port scanner by krovix
----------------------------------------------------------------------
Scanning target host 45.33.32.156

Port 22 is open
Port 80 is open

Scan complete.
```

## How it works

For each port in the range, the scanner opens a TCP socket and attempts a connection using `connect_ex()`. A return value of `0` means the connection succeeded, so the port is open. A 1-second timeout keeps closed or filtered ports from stalling the scan.

## Roadmap

Planned improvements as I keep learning:

- Multithreading for much faster scans over large ranges
- Service name lookup for each open port
- Banner grabbing to identify running services
- Cleaner CLI with flags (using `argparse`)

- <img width="1486" height="767" alt="image" src="https://github.com/user-attachments/assets/b56b3f13-38aa-413f-9ded-9893c4bc78f2" />


## Legal & ethical note

Only scan hosts you own or have explicit permission to test. Unauthorized port scanning may violate the law and the acceptable-use policies of networks you don't control. Use `scanme.nmap.org` or your own machines for practice.

## Author

Built by **krovix** as a cybersecurity learning project.


