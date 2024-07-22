import os
import subprocess
import socket
import wmi
import time
import ctypes
import sys

# Check if time is synchronized with the domain controller
def test_time_synchronization():
    domain_controller = "10.10.50.1"  # Update with your domain controller's IP address
    current_time = time.time()
    max_time_difference = 5 * 60  # Adjust this value based on your requirements (in seconds)

    try:
        last_sync_time = subprocess.check_output("w32tm /query /status /verbose | findstr /i \"Last Successful Sync Time\"", shell=True)
        last_sync_time = last_sync_time.decode().split("Last Successful Sync Time: ")[1].strip()
        last_sync_time = time.mktime(time.strptime(last_sync_time, "%m/%d/%Y %I:%M:%S %p"))
    except subprocess.CalledProcessError:
        return False  # Time not synchronized

    time_difference = current_time - last_sync_time

    return time_difference > max_time_difference

# Set DNS server address
def set_dns_server(dns_server):
    c = wmi.WMI()
    for network_adapter in c.Win32_NetworkAdapterConfiguration(IPEnabled=True):
        network_adapter.SetDNSServerSearchOrder([dns_server])

# Set execution policy and install RSAT tools
subprocess.run(["Set-ExecutionPolicy", "-Scope", "CurrentUser", "-ExecutionPolicy", "Unrestricted"], stdout=subprocess.PIPE, stderr=subprocess.PIPE, check=True)
subprocess.run(["Add-WindowsCapability", "-Name", "Rsat.ActiveDirectory.DS-LDS.Tools~~~~0.0.1.0", "-Online"], stdout=subprocess.PIPE, stderr=subprocess.PIPE, check=True)

# Change routing table to allow USB connections
interface = None
for net_adapter in subprocess.run(["Get-NetAdapter"], stdout=subprocess.PIPE, stderr=subprocess.PIPE, text=True).stdout.splitlines():
    if "Up" in net_adapter:
        interface = net_adapter.split()[1]
        break

if interface:
    subprocess.run(["route", "add", "10.20.0.0", "mask", "255.255.0.0", "10.40.254.254"], stdout=subprocess.PIPE, stderr=subprocess.PIPE, check=True)
    # subprocess.run(["route", "add", "10.40.0.0", "mask", "255.255.0.0", "10.20.254.254", "if", interface], stdout=subprocess.PIPE, stderr=subprocess.PIPE, check=True)
else:
    print("No active network interface found.")

# Check if time synchronization is needed
if test_time_synchronization():
    # Time is not synchronized, perform synchronization steps
    print("Time is not synchronized with the domain controller. Performing synchronization...")

    # Stop the Windows Time service
    subprocess.run(["net", "stop", "w32time"], stdout=subprocess.PIPE, stderr=subprocess.PIPE, check=True)

    # Unregister and register the Windows Time service
    subprocess.run(["w32tm", "/unregister"], stdout=subprocess.PIPE, stderr=subprocess.PIPE, check=True)
    subprocess.run(["w32tm", "/register"], stdout=subprocess.PIPE, stderr=subprocess.PIPE, check=True)

    # Register the w32time.dll
    ctypes.windll.shell32.ShellExecuteW(None, "runas", "regsvr32.exe", "C:\\windows\\system32\\w32time.dll", None, 1)

    # Configure time synchronization with time.windows.com
    subprocess.run(["w32tm", "/config", "/manualpeerlist:time.windows.com,0x4", "/syncfromflags:MANUAL"], stdout=subprocess.PIPE, stderr=subprocess.PIPE, check=True)

    # Start the Windows Time service
    subprocess.run(["net", "start", "w32time"], stdout=subprocess.PIPE, stderr=subprocess.PIPE, check=True)

    print("Time synchronization completed.")
else:
    print("Time is already synchronized with the domain controller. No action needed.")

# Disable Windows Firewall
subprocess.run(["Set-NetFirewallProfile", "-Enabled", "False"], stdout=subprocess.PIPE, stderr=subprocess.PIPE, check=True)
subprocess.run(["Set-NetFirewallProfile", "-Profile", "Domain,Public,Private", "-Enabled", "False"], stdout=subprocess.PIPE, stderr=subprocess.PIPE, check=True)
subprocess.run(["netsh", "advfirewall", "show", "all"], stdout=subprocess.PIPE, stderr=subprocess.PIPE, check=True)

# Set DNS server address
set_dns_server("10.10.50.1")

# Specify domain information
domain_name = "casa.net"

# Specify OU information
ou_path = "OU=Casa VPN,OU=VDI,OU=Desktops,DC=casa,DC=net"  # Update with the correct OU path

# Specify the pattern for the new computer name
computer_name_pattern = "vpnpc{0}"

# Specify the Active Directory server
domain_controller = "10.10.50.1"

# Specify the activation code
activation_code = "NPPR9-FWDCX-D2C8J-H872K-2YT43"

# Activate Windows using slmgr.vbs
try:
    activate_command = "slmgr.vbs /ipk " + activation_code + " ; slmgr.vbs /ato"
    subprocess.run(activate_command, shell=True, check=True)
    print("Windows activated successfully.")
except subprocess.CalledProcessError as e:
    print("Error activating Windows:", e)
    sys.exit(1)

# Add the computer to the domain and specify the OU
try:
    subprocess.run(["Add-Computer", "-DomainName", domain_name, "-Force", "-OUPath", ou_path], stdout=subprocess.PIPE, stderr=subprocess.PIPE, check=True)
    print("Computer added to the domain.")
except subprocess.CalledProcessError as e:
    print("Error adding the computer to the domain:", e)
    sys.exit(1)

# Get computer names from the specified OU
try:
    ou_computers = subprocess.run(["Get-ADComputer", "-Filter", "*", "-SearchBase", ou_path, "-Server", domain_controller], stdout=subprocess.PIPE, stderr=subprocess.PIPE, text=True, check=True).stdout.strip().split("\n")
    ou_computers = [computer.strip() for computer in ou_computers]
except subprocess.CalledProcessError as e:
    print("Error connecting to the Active Directory server:", e)
    sys.exit(1)

# Generate a new computer name based on the pattern
new_computer_name = None
for i in range(1, 1000):
    if i != 5:
        potential_name = computer_name_pattern.format(i)
        if potential_name not in ou_computers:
            new_computer_name = potential_name
            break

if not new_computer_name:
    print("Error: Unable to generate a unique computer name")