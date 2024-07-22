import re
import socket


file = open('C:\\Users\\eilat\\Documents\\vpn_sessions_9-4-2024.txt','r')


session_list = file.read()

# Regular expression pattern to match hostnames
hostname_pattern = re.compile(r'\b(?:[a-zA-Z0-9]+(?:-[a-zA-Z0-9]+)*\.)+[a-zA-Z]{2,}\b')

# Find all hostnames in the session list
hostnames = hostname_pattern.findall(session_list)

# Resolve hostnames to IP addresses
ip_addresses = []
for hostname in hostnames:
    try:
        ip = socket.gethostbyname(hostname)
        ip_addresses.append(ip)
    except socket.gaierror:
        print(f"Failed to resolve IP address for hostname: {hostname}")

print("IP Addresses:")
for ip in ip_addresses:
    print(ip)