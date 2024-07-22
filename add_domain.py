import wmi
import os
import random
import string
from ldap3 import Server, Connection, ALL, NTLM


def get_random_vpn_pc_name():
    return f"VPNPC{''.join(random.choices(string.digits, k=3))}"


def check_computer_name_exists(domain, username, password, computer_name):
    # Connect to Active Directory
    server = Server(domain, get_info=ALL)
    conn = Connection(server, user=username, password=password, authentication=NTLM)
    conn.bind()

    # Search for the specific computer name
    search_filter = f'(sAMAccountName={computer_name}$)'
    conn.search('dc=casa,dc=net', search_filter, attributes=['sAMAccountName'])
    exists = len(conn.entries) > 0
    conn.unbind()

    return exists


def rename_computer(new_name):
    # Rename the computer
    os.system(f"wmic computersystem where caption='%computername%' rename {new_name}")


def join_domain(domain, username, password, computer_name=None, ou=None):
    c = wmi.WMI()
    # Get the computer system object
    computer_system = c.Win32_ComputerSystem()[0]

    try:
        print(f"Attempting to join the domain {domain} with username {username}")
        # Join the domain
        result = computer_system.JoinDomainOrWorkgroup(
            Name=domain,
            UserName=username,
            Password=password,
            AccountOU=ou,
            FJoinOptions=3
            # Set FJoinOptions to 3 to specify that the computer should join the domain with secure channel and create a computer account if it does not exist
        )

        if result == 0 or result == (0,):
            print(f"Successfully joined {computer_name or 'the computer'} to domain {domain}")
            os.system("shutdown /r /t 0")

        else:
            print(f"Failed to join {computer_name or 'the computer'} to domain {domain}. Error code: {result}")

    except AttributeError as e:
        print(f"Error: {e}")
        print("Make sure the 'JoinDomainOrWorkgroup' method exists and the parameters are correct.")
    except Exception as e:
        print(f"An unexpected error occurred: {e}")


def activate_windows(activation_code):
    os.system(f"slmgr /ipk {activation_code}")
    os.system("slmgr /ato")


if __name__ == "__main__":
    domain = "casa.net"
    username = input("Please enter casa domain username: ")  # Prompt for username
    if "casa.net" not in username or 'casa' not in username:
        username = "casa.net\\" + username  # Prompt for username
    password = input("Please enter casa domain password: ")  # Prompt for password
    ou_path = "OU=Casa VPN,OU=VDI,OU=Desktops,DC=casa,DC=net"
    activation_code = "NPPR9-FWDCX-D2C8J-H872K-2YT43"

    # Generate a unique VPN PC name
    while True:
        new_name = get_random_vpn_pc_name()
        if not check_computer_name_exists(domain, username, password, new_name):
            print(f"The new computer name '{new_name}' is available.")
            break
        else:
            print(f"The computer name '{new_name}' already exists. Generating a new name...")

    # Rename the computer
    rename_computer(new_name)

    # Join the domain
    join_domain(domain, username, password, new_name, ou_path)

    # Activate Windows
    activate_windows(activation_code)
