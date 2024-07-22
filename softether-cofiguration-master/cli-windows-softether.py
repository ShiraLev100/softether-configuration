from smb.SMBConnection import SMBConnection
import tkinter as tk
from tkinter import ttk, filedialog
from PIL import Image, ImageTk
import base64
import io
import os
import ctypes
import sys
import subprocess
#from ttkthemes import ThemedStyle

# Add logging configuration
import logging
logging.basicConfig(level=logging.INFO, format='%(asctime)s - %(levelname)s - %(message)s')



class SMBClient:
    def __init__(self, username, password, servername, share_name):
        self._username = username
        self._password = password
        self._port = 445
        self._share_name = share_name
        self._servername = servername
        self._server = ''

    def _connect(self):
        """ Connect and authenticate to the SMB share. """
        self._server = SMBConnection(username=self._username,
                                     password=self._password,
                                     my_name="script",
                                     remote_name=self._servername,
                                     domain="CASA.net",
                                     use_ntlm_v2=True,
                                     is_direct_tcp=True)
        self._server.connect(self._servername, port=self._port)

    def _downloadDir(self, path: str, dest_dir):
        """ Download files from the remote share. """
        os.makedirs(dest_dir, exist_ok=True)
        for file in self._server.listPath(service_name=self._share_name,
                                          path=path):
            print(f"file_name {file.filename}")

            if file.filename in [".", ".."]:
                continue
            if os.path.isfile(dest_dir +"/" + file.filename):
                continue
            with open(dest_dir+"/" + file.filename, 'wb') as file_obj:
                self._server.retrieveFile(service_name=self._share_name,
                                          path=path+file.filename,
                                          file_obj=file_obj)

    def _downloadFile(self, path: str, file_name: str, dest_path: str):
        """ Download files from the remote share. """
        os.makedirs(dest_path, exist_ok=True)
        with open(dest_path + file_name, 'wb') as file_obj:
            self._server.retrieveFile(service_name=self._share_name,
                                      path=path + file_name,
                                      file_obj=file_obj)
            print(f"downloaded {file_name}")


def run_vpncmd_command(vpncmd_path, command):
    # Construct the full command to run
    full_command = f'"{vpncmd_path}" {command}'

    # Run vpncmd command
    try:
        proc = subprocess.Popen(full_command, shell=True, stdout=subprocess.PIPE, stderr=subprocess.PIPE)
        stdout, stderr = proc.communicate()
        print("Command output:", stdout.decode())
        print("Command errors:", stderr.decode())
        return stdout, stderr
    except Exception as e:
        print("Error executing command:", e)
        return None, None

def configure_softether_vpn(vpn_server, vpn_hub, username, password, connection_name):
    vpncmd_path = r"C:\Program Files\SoftEther VPN Client\vpncmd.exe"
    disaccount_command = f'localhost /CLIENT /CMD AccountDisconnect {connection_name}'
    delete_account_command = f'localhost /CLIENT /CMD AccountDelete {connection_name}'
    delete_nic_command = f'localhost /CLIENT /CMD NicDelete {connection_name}'
    add_connection_command = f'localhost /CLIENT /CMD AccountCreate {connection_name} /SERVER:{vpn_server} /HUB:{vpn_hub} /USERNAME:{username} /NICNAME:vpn'
    startup_connection_command = f'localhost /CLIENT /CMD AccountStartupSet {connection_name}'
    set_password_command = f'localhost /CLIENT /CMD AccountPasswordSet {connection_name} /PASSWORD:{password} /TYPE:radius'
    connect_command = f'localhost /CLIENT /CMD NicCreate {connection_name}'
    connect_account_command = f'localhost /CLIENT localhost /CMD AccountConnect {connection_name}'

    try:
        # Check if the VPN connection exists and disconnect if connected
        stdout, stderr = run_vpncmd_command(vpncmd_path, f'localhost /CLIENT /CMD AccountStatusGet {connection_name}')
        if "Status: Connected" in stdout.decode():
            run_vpncmd_command(vpncmd_path, disaccount_command)

        # Delete VPN connection settings
        run_vpncmd_command(vpncmd_path, delete_account_command)

        # Delete NIC
        run_vpncmd_command(vpncmd_path, delete_nic_command)

        # Create new VPN connection settings
        try:
            # Attempt to create the Virtual Network Adapter
            run_vpncmd_command(vpncmd_path, add_connection_command)
        except subprocess.CalledProcessError as e:
            print(f"Error creating Virtual Network Adapter: {e.output}")
            print("Please choose a different name for the adapter.")
            return

        run_vpncmd_command(vpncmd_path, set_password_command)
        run_vpncmd_command(vpncmd_path, connect_command)
        run_vpncmd_command(vpncmd_path, connect_account_command)
        run_vpncmd_command(vpncmd_path, startup_connection_command)

        print("SoftEther VPN connection configured successfully!")
    except Exception as e:
        print(f"Error configuring SoftEther VPN: {e}")


def get_relative_path(wanted_path):
    curr_path = os.getcwd()
    return "." + wanted_path.replace(curr_path, '')

def connect_softether(username, password):
    # Define software folder path
    software_path = r"C:\Software"

    # Define VPN server details
    vpn_username = username
    vpn_password = password

    vpn_client_installer_path = os.path.join(software_path, "softether-vpnclient.exe")

    # Check if SoftEther VPN Client is already installed
    if os.path.exists(r"C:\Program Files\SoftEther VPN Client\vpnclient.exe"):
        print("SoftEther VPN Client is already installed.")
    else:
        print("no softether VPN client app is is installed on this device")
        return 0

    vpn_server = "10.40.90.101:443"  # Replace with your VPN server address and port
    vpn_hub = "VPN"  # Replace with your VPN hub name
    connection_name = "VPN"  # Replace with your desired connection name

    try:
        run_vpncmd_command("vpnclient" , "start")
    except Exception as e:
        logging.error("Error starting VPN client: %s", str(e))

    configure_softether_vpn(vpn_server, vpn_hub, vpn_username, vpn_password, connection_name)
    # Log that the VPN client has started
    logging.info("VPN client started successfully.")



def get_user_credentials():
    f = open("C:\\usernameData.txt")
    lines = f.readlines()

    username = lines[0].split(':')[1][1:-1]
    password = lines[1].split(':')[1][1:-1]
    return username, password

if __name__ == '__main__':
    connect_softether(get_user_credentials()[0], get_user_credentials()[1])