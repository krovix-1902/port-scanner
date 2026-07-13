#!/usr/bin/python3
import socket
import sys

usage = "python3 port_scan.py <host> <start_port> <end_port>"

print("-" * 70)
print("Simple port scanner by krovix")
print("-" * 70)

if len(sys.argv) != 4:
    print(usage)
    sys.exit(1)

try:
    host = socket.gethostbyname(sys.argv[1])
except socket.gaierror:
    print("Hostname could not be resolved. Exiting")
    sys.exit(1)

start_port = int(sys.argv[2])
end_port = int(sys.argv[3])
socket.setdefaulttimeout(1)

print(f"Scanning target host {host}\n")

try:
    for port in range(start_port, end_port + 1):
        s = socket.socket(socket.AF_INET, socket.SOCK_STREAM)
        if s.connect_ex((host, port)) == 0:
            print(f"Port {port} is open")
        s.close()
except KeyboardInterrupt:
    print("\nExiting.")
    sys.exit()

print("\nScan complete.")