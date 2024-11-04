import os
import paramiko
from pathlib import Path
from dotenv import load_dotenv

# Define connection parameters
port = 22
username = 'ubuntu'
INSTANCE_KEY_NAME = "key-pair-lab2"

if __name__ == "__main__":
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
    parent_path = Path(__file__).resolve().parents[1]
    key_file_path = f"{parent_path}/general/{INSTANCE_KEY_NAME}.pem"
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

    # Install curl on Trusted Host (Debian/Ubuntu)
    install_curl_command = "sudo apt-get update && sudo apt-get install -y curl"
    trusted_host_client.exec_command(install_curl_command)

    stdin, stdout, stderr = trusted_host_client.exec_command(install_curl_command)
    print(stdout.read().decode())
    print(stderr.read().decode())

    # Connect to Proxy
    proxy_client = paramiko.SSHClient()
    proxy_client.set_missing_host_key_policy(paramiko.AutoAddPolicy())
    proxy_channel = trusted_host_client.get_transport().open_channel("direct-tcpip", (proxy_ip, 22), (trusted_host_ip, 0))
    proxy_client.connect(proxy_ip, username=username, pkey=key, sock=proxy_channel)

    # Execute command on Trusted Host to access FastAPI
    fastapi_command = f"curl http://{proxy_ip}:8000/"
    stdin, stdout, stderr = trusted_host_client.exec_command(fastapi_command)

    # Print the output from the FastAPI request
    output = stdout.read().decode()
    error = stderr.read().decode()

    if output:
        print('Response from FastAPI:', output)
    if error:
        print('Error:', error)

    # Clean up connections
    proxy_client.close()
    trusted_host_client.close()
    gatekeeper_client.close()
