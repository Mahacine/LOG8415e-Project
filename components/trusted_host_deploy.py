import paramiko
from paramiko import SSHClient, AutoAddPolicy
from scp import SCPClient
from pathlib import Path
from dotenv import load_dotenv
import os
import threading

# Define connection parameters
port = 22
username = 'ubuntu'
INSTANCE_KEY_NAME = "key-pair-lab2"

# Load environment variables from the .env file
load_dotenv(override=True)

def deploy_trusted_host(key_file_path):
    
    # Load environment variables from .env file
    load_dotenv()

    # Get instance details from environment variables
    proxy_ip = os.getenv('PROXY_IP')
    trusted_host_ip = os.getenv('HOST_IP')
    gatekeeper_ip = os.getenv('GATE_IP')

    # Load SSH key
    key = paramiko.RSAKey.from_private_key_file(key_file_path)

    # Connect to Gatekeeper
    gatekeeper_client = paramiko.SSHClient()
    gatekeeper_client.set_missing_host_key_policy(paramiko.AutoAddPolicy())
    gatekeeper_client.connect(gatekeeper_ip, username=username, pkey=key)

    # Connect to Trusted Host
    trusted_host_client = paramiko.SSHClient()
    trusted_host_client.set_missing_host_key_policy(paramiko.AutoAddPolicy())
    gatekeeper_transport = gatekeeper_client.get_transport()
    trusted_host_channel = gatekeeper_transport.open_channel("direct-tcpip", (trusted_host_ip, 22), (gatekeeper_ip, 0))
    trusted_host_client.connect(trusted_host_ip, username=username, pkey=key, sock=trusted_host_channel)

    # Transfer files using SCP
    with SCPClient(trusted_host_client.get_transport()) as scp:
        scp.put('./components/trusted_host.py', '/home/ubuntu/trusted_host.py')
        scp.put(key_file_path, f'/home/ubuntu/key-pair-lab2.pem')
    
    # Execute commands to set up and run FastAPI app
    commands = [
        'sudo apt-get update',
        'sudo apt-get install python3 python3-pip -y',
        'sudo apt-get install python3-venv -y',
        'python3 -m venv fastapi_env',
        'source fastapi_env/bin/activate',
        'fastapi_env/bin/pip install fastapi uvicorn paramiko scp pydantic',
        f'export PROXY_IP={proxy_ip} && nohup fastapi_env/bin/uvicorn trusted_host:app --host 0.0.0.0 --port 8000 &',
    ]
    
    for command in commands:
        stdin, stdout, stderr = trusted_host_client.exec_command(command)
        print(stdout.read().decode())
        print(stderr.read().decode())
    
    # Close the SSH connection
    trusted_host_client.close()

if __name__ == "__main__":
    parent_path = Path(__file__).resolve().parents[1]
    key_file_path = f"{parent_path}/general/{INSTANCE_KEY_NAME}.pem"
    t = threading.Thread(target=deploy_trusted_host,args=(key_file_path,))
    t.start()