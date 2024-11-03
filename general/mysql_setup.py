import paramiko
from paramiko import SSHClient, AutoAddPolicy
from scp import SCPClient

# Define connection parameters
port = 22
username = 'ubuntu'

ssh_client = None

def setup(instance_ip, private_key_path):
    # Create SSH client
    ssh_client = SSHClient()
    ssh_client.set_missing_host_key_policy(AutoAddPolicy())
    
    # Load private key
    private_key = paramiko.RSAKey.from_private_key_file(private_key_path)

    # Connect to the instance
    ssh_client.connect(instance_ip, port=port, username=username, pkey=private_key)

    return ssh_client

# Function to execute shell commands via SSH
def run_command(ssh_client, command):
    
    stdin, stdout, stderr = ssh_client.exec_command(command)
    
    stdout_output = stdout.read().decode()
    stderr_output = stderr.read().decode()
    
    if stdout_output:
        print(stdout_output)
    if stderr_output:
        print(stderr_output)

def install_mysql():
    
    global ssh_client

    print("MySQL installation started...")
    
    # Step 1 — Installing Java
    commands = ['sudo apt-get update -y && sudo apt-get install mysql-server -y']

    for command in commands:
        run_command(ssh_client, command)

    print("MySQL installation complete.")

def install_dependencies(instance_ip, private_key_path):
    
    global ssh_client

    ssh_client = setup(instance_ip, private_key_path)

    install_mysql()

    # Close the SSH connection
    ssh_client.close()