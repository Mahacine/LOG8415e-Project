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

"""
def execute_curl_command(endpoint: str, data: dict = None):
    # try:
        # Load SSH private key
        key = paramiko.RSAKey.from_private_key_file(key_file_path)

        trusted_host_client = paramiko.SSHClient()
        trusted_host_client.set_missing_host_key_policy(paramiko.AutoAddPolicy())
        trusted_host_client.connect(trusted_host_ip, username=username, pkey=key)

        # Install curl on Trusted Host (Debian/Ubuntu)
        install_curl_command = "sudo apt-get install -y curl"
        # trusted_host_client.exec_command(install_curl_command)

        # Connect to Proxy
        proxy_client = paramiko.SSHClient()
        proxy_client.set_missing_host_key_policy(paramiko.AutoAddPolicy())
        proxy_channel = trusted_host_client.get_transport().open_channel("direct-tcpip", (proxy_ip, 22), (trusted_host_ip, 0))
        proxy_client.connect(proxy_ip, username=username, pkey=key, sock=proxy_channel)
        
        # If there's data to post, build the curl command with JSON payload
        if data:
            curl_command = f"curl -X POST http://{proxy_ip}:8000/{endpoint} -H 'Content-Type: application/json' -d '{json.dumps(data)}'"
        else:
            curl_command = f"curl http://{proxy_ip}:8000/{endpoint}"
        
        # Execute the curl command
        stdin, stdout, stderr = trusted_host_client.exec_command(curl_command)

        # Print the output from the FastAPI request
        output = stdout.read().decode()
        error = stderr.read().decode()
        
        # Step 1: Isolate the JSON part (before the newline)
        json_part = (output + "\n" + error).split('\n')[0]

        # Step 2: Parse the JSON string
        try:
            data = json.loads(json_part)
            # Step 3: Extract the 'message' field
            message = data.get("message", "No message found")
            print(message)
        except json.JSONDecodeError:
            print("Error: Could not decode JSON.")
        
        return message
    
    # except Exception as e:
    #    raise HTTPException(status_code=500, detail=f"Error forwarding request: {str(e)}")
"""
def execute_curl_command(endpoint: str, data: dict = None):
        # If there's data to post, build the curl command with JSON payload
        if data:
            curl_command = f"curl -X POST http://{trusted_host_ip}:8000/{endpoint} -H 'Content-Type: application/json' -d '{json.dumps(data)}'"
        else:
            curl_command = f"curl http://{trusted_host_ip}:8000/{endpoint}"
        
        # Execute the curl command
        # stdin, stdout, stderr = trusted_host_client.exec_command(curl_command)
        result = subprocess.run(curl_command, capture_output=True, text=True, shell=True)

        # Capture the output and error
        output = result.stdout
        error = result.stderr
        
        # Step 1: Isolate the JSON part (before the newline)
        json_part = (output + "\n" + error).split('\n')[0]

        # Step 2: Parse the JSON string
        try:
            data = json.loads(json_part)
            # Step 3: Extract the 'message' field
            message = data.get("message", "No message found")
            print(message)
        except json.JSONDecodeError:
            print("Error: Could not decode JSON.")
        
        return message

# Pydantic model for the data
class CustomData(BaseModel):
    first_name: str
    last_name: str


# Validation for URL endpoint
def validate_url(endpoint: str, data: dict = None):
    valid_endpoints = ['direct', 'random', 'custom']
    # Check if the endpoint starts with any valid prefix
    if not any(endpoint.startswith(ve) for ve in valid_endpoints):
        raise HTTPException(status_code=400, detail="Invalid URL path")
    
    # Check if it's a "write" endpoint and ensure that both first_name and last_name are provided
    if "write" in endpoint:
        first_name = data.get('first_name')
        last_name = data.get('last_name')
        
        # Validate that both 'first_name' and 'last_name' are provided
        if not first_name or not last_name:
            raise HTTPException(status_code=400, detail="Both 'first_name' and 'last_name' are required for write endpoints (Insert in actor table)")

# FastAPI Routes for Direct
@app.post("/direct/write")
async def direct_write(data: CustomData):
    validate_url("direct/write", data.dict())
    return execute_curl_command("direct/write", data.dict())

@app.get("/direct/read")
async def direct_read():
    validate_url("direct/read")
    return execute_curl_command("direct/read")


# FastAPI Routes for Random
@app.post("/random/write")
async def random_write(data: CustomData):
    validate_url("random/write", data.dict())
    return execute_curl_command("random/write", data.dict())

@app.get("/random/read")
async def random_read():
    validate_url("random/read")
    return execute_curl_command("random/read")


# FastAPI Routes for Custom
@app.post("/custom/write")
async def custom_write(data: CustomData):
    validate_url("custom/write", data.dict())
    return execute_curl_command("custom/write", data.dict())

@app.get("/custom/read")
async def custom_read():
    validate_url("custom/read")
    return execute_curl_command("custom/read")

# Health check endpoint
@app.get("/health")
async def health_check():
    return {"status": "OK"}

# Invalid url endpoint
@app.get("/other")
async def invalidate_url():
    validate_url("/other")