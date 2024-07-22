import subprocess
import time

def run_vpncmd_command(vpncmd_path, command):
    # Construct the full command to run
    full_command = f'"{vpncmd_path}" /server 10.40.90.101 /PASSWORD:12345678 /CMD {command}'

    # Run vpncmd command
    try:
        print("Executing command:", full_command)
        proc = subprocess.Popen(full_command, shell=True, stdout=subprocess.PIPE, stderr=subprocess.PIPE)
        stdout, stderr = proc.communicate()
        print("Command output:", stdout.decode())
        print("Command errors:", stderr.decode())
        return stdout, stderr
    except Exception as e:
        print("Error executing command:", e)
        return None, None

def main():
    vpncmd_path = r"C:\Program Files\SoftEther VPN Client\vpncmd.exe"

    try:
        # Select Virtual Hub
        hub_command = 'Hub VPN'
        run_vpncmd_command(vpncmd_path, hub_command)

        # Get session list
        session_list_command = 'SessionList'
        run_vpncmd_command(vpncmd_path, session_list_command)

        print("SoftEther VPN server sessions retrieved successfully!")
    except Exception as e:
        print(f"Error: {e}")

if __name__ == "__main__":
    main()
