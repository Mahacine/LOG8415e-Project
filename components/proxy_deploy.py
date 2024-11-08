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

def deploy_proxy(key_file_path):
    
    # Load environment variables from .env file
    load_dotenv()

    # Get instance details from environment variables
    gatekeeper_ip = os.getenv('GATE_IP')
    trusted_host_ip = os.getenv('HOST_IP')
    proxy_ip = os.getenv('PROXY_IP')
    manager_ip = os.getenv('MANAGER_IP')
    worker1_ip = os.getenv('WORKER1_IP')
    worker2_ip = os.getenv('WORKER2_IP')

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

    # Connect to Proxy
    proxy_client = paramiko.SSHClient()
    proxy_client.set_missing_host_key_policy(paramiko.AutoAddPolicy())
    proxy_channel = trusted_host_client.get_transport().open_channel("direct-tcpip", (proxy_ip, 22), (trusted_host_ip, 0))
    proxy_client.connect(proxy_ip, username=username, pkey=key, sock=proxy_channel)

    # Transfer files using SCP
    with SCPClient(proxy_client.get_transport()) as scp:
        scp.put('./components/proxy.py', '/home/ubuntu/proxy.py')
        scp.put(key_file_path, '/home/ubuntu/key-pair-lab2.pem')
    
    # Execute commands to set up and run FastAPI app
    commands = [
        'sudo apt-get update',
        'sudo apt-get install python3 python3-pip -y',
        'sudo apt-get install python3-venv -y',
        'python3 -m venv fastapi_env',
        'source fastapi_env/bin/activate',
        'fastapi_env/bin/pip install fastapi uvicorn paramiko scp pydantic',
        f'export MANAGER_IP={manager_ip} && export WORKER1_IP={worker1_ip} && export WORKER2_IP={worker2_ip} && nohup fastapi_env/bin/uvicorn proxy:app --host 0.0.0.0 --port 8000 &',
    ]
    
    for command in commands:
        stdin, stdout, stderr = proxy_client.exec_command(command)
        print(stdout.read().decode())
        print(stderr.read().decode())
    
    # Close the SSH connection
    proxy_client.close()
    trusted_host_client.close()
    gatekeeper_client.close()

if __name__ == "__main__":
    parent_path = Path(__file__).resolve().parents[1]
    key_file_path = f"{parent_path}/general/{INSTANCE_KEY_NAME}.pem"
    t = threading.Thread(target=deploy_proxy,args=(key_file_path,))
    t.start()