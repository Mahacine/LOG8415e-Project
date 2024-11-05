import paramiko
import json
from fastapi import FastAPI, HTTPException, Request
from pydantic import BaseModel
import subprocess
import os
from threading import Thread

# FastAPI App instance
app = FastAPI()

# Trusted Host and Gatekeeper Configuration
gatekeeper_ip = os.getenv('GATE_IP', 'unknown')
trusted_host_ip = os.getenv('HOST_IP', 'unknown')
# trusted_host_ip = os.getenv('PROXY_IP', 'unknown')
proxy_ip = os.getenv('PROXY_IP', 'unknown')
username = "ubuntu"
INSTANCE_KEY_NAME = "key-pair-lab2"
key_file_path = f'/home/ubuntu/{INSTANCE_KEY_NAME}.pem'
port = 22

# Establish SSH client and connection to the trusted host
def connect_to_trusted_host():
    try:
         # Load SSH private key
        key = paramiko.RSAKey.from_private_key_file(key_file_path)

        # Initialize SSH client for the gatekeeper
        gatekeeper_client = paramiko.SSHClient()
        gatekeeper_client.set_missing_host_key_policy(paramiko.AutoAddPolicy())
        gatekeeper_client.load_system_host_keys()
        
        # Connect to the gatekeeper (we're already inside, but still need to initiate connection)
        gatekeeper_client.connect(gatekeeper_ip, username=username, pkey=key)
        
        # Get the transport from the gatekeeper SSH connection
        gatekeeper_transport = gatekeeper_client.get_transport()

        # Open a direct TCP/IP channel to the trusted host
        trusted_host_channel = gatekeeper_transport.open_channel("direct-tcpip", (trusted_host_ip, 22), (gatekeeper_ip, 0))

        # Now, connect to the trusted host via the tunnel established in the gatekeeper
        trusted_host_client = paramiko.SSHClient()
        trusted_host_client.set_missing_host_key_policy(paramiko.AutoAddPolicy())
        trusted_host_client.connect(trusted_host_ip, username=username, pkey=key, sock=trusted_host_channel)
        
        return trusted_host_client
    except Exception as e:
        raise HTTPException(status_code=500, detail=f"Connection failed: {str(e)}")

# Function to establish the SSH tunnel
def establish_ssh_tunnel():
    try:
        # Load SSH private key
        key = paramiko.RSAKey.from_private_key_file(key_file_path)

        local_forward_port = 8080

        # Initialize SSH client
        gatekeeper_client = paramiko.SSHClient()
        gatekeeper_client.set_missing_host_key_policy(paramiko.AutoAddPolicy())
        gatekeeper_client.connect(gatekeeper_ip, username=username, pkey=key)

        # Establish SSH tunnel to trusted host
        transport = gatekeeper_client.get_transport()
        # Forward local port (e.g., 8080) to trusted host on port 8000 (FastAPI port)
        transport.request_port_forward('localhost', local_forward_port, trusted_host_ip, 8000)

        print(f"SSH Tunnel established: Forwarding localhost:{local_forward_port} to {trusted_host_ip}:8000")
    except Exception as e:
        raise HTTPException(status_code=500, detail=f"Error establishing SSH tunnel: {str(e)}")

def execute_curl_command(endpoint: str, data: dict = None):
    try:
        # establish_ssh_tunnel()

        trusted_host_client = connect_to_trusted_host()

        # Build the curl command to access the FastAPI endpoint
        url = f"http://{proxy_ip}:8000/{endpoint}"
        # url = 'http://172.31.99.236:8000/direct/write'
        # url = f"http://localhost:8080/{endpoint}"
        
        # If there's data to post, build the curl command with JSON payload
        """
        if data:
            curl_command = [
                "curl", "-X", "POST", url,
                "-H", "Content-Type: application/json",
                "-d", json.dumps(data)
            ]
        else:
            curl_command = ["curl", url]
        """
        if data:
            curl_command = f"curl -X POST {url} -H 'Content-Type: application/json' -d '{json.dumps(data)}'"
        else:
            curl_command = f"curl {url}"
        # Execute the curl command locally on the gatekeeper machine
        # result = subprocess.run(curl_command, stdout=subprocess.PIPE, stderr=subprocess.PIPE, text=True)
        stdin, stdout, stderr = trusted_host_client.exec_command(curl_command)

        """
        # Get the output and error (if any)
        output = result.stdout
        error = result.stderr
        """
        # Print the output from the FastAPI request
        output = stdout.read().decode()
        error = stderr.read().decode()
        
        if error:
            raise HTTPException(status_code=500, detail=f"Error executing curl command: {error}")
        
        # Parse the result as JSON (if it's JSON output)
        try:
            return json.loads(output)
        except json.JSONDecodeError:
            return output  # Return raw output if not JSON
    except Exception as e:
        raise HTTPException(status_code=500, detail=f"Error forwarding request: {str(e)}")


# Pydantic model for the data
class CustomData(BaseModel):
    key: str
    value: str


# Validation for URL endpoint
def validate_url(endpoint: str):
    valid_endpoints = ['direct', 'random', 'custom']
    if not any(endpoint.startswith(ve) for ve in valid_endpoints):
        raise HTTPException(status_code=400, detail="Invalid URL path")

"""
# Trigger SSH tunnel setup on FastAPI startup
@app.on_event("startup")
def startup_event():
    tunnel_thread = Thread(target=establish_ssh_tunnel)
    tunnel_thread.daemon = True
    tunnel_thread.start()
"""

# FastAPI Routes for Direct
@app.post("/direct/write")
async def direct_write(data: CustomData):
    validate_url("direct/write")
    return execute_curl_command("direct/write", data.dict())

@app.get("/direct/read")
async def direct_read():
    validate_url("direct/read")
    return execute_curl_command("direct/read")


# FastAPI Routes for Random
@app.post("/random/write")
async def random_write(data: CustomData):
    validate_url("random/write")
    return execute_curl_command("random/write", data.dict())

@app.get("/random/read")
async def random_read():
    validate_url("random/read")
    return execute_curl_command("random/read")


# FastAPI Routes for Custom
@app.post("/custom/write")
async def custom_write(data: CustomData):
    validate_url("custom/write")
    return execute_curl_command("custom/write", data.dict())

@app.get("/custom/read")
async def custom_read():
    validate_url("custom/read")
    return execute_curl_command("custom/read")
