from fastapi import FastAPI, HTTPException, Request
import uvicorn
import logging
import os
from pydantic import BaseModel
import random
import subprocess
import re
import paramiko
import json
from threading import Thread

# Configure logging
logging.basicConfig(level=logging.INFO)
logger = logging.getLogger(__name__)

# Create FastAPI app
app = FastAPI()

proxy_ip = os.getenv('PROXY_IP', 'unknown')

ssh_port = 22
ssh_username = "ubuntu"
private_key_path = '/home/ubuntu/key-pair-lab2.pem'

# Pydantic model for the data
class CustomData(BaseModel):
    first_name: str
    last_name: str

def execute_curl_command(endpoint: str, data: dict = None):
        # If there's data to post, build the curl command with JSON payload
        if data:
            curl_command = f"curl -X POST http://{proxy_ip}:8000/{endpoint} -H 'Content-Type: application/json' -d '{json.dumps(data)}'"
        else:
            curl_command = f"curl http://{proxy_ip}:8000/{endpoint}"
        
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
        
        # return message
        return {"message": message}

# FastAPI Routes for Direct
@app.post("/direct/write")
async def direct_write(data: CustomData):
    return execute_curl_command("direct/write", data.dict())

@app.get("/direct/read")
async def direct_read():
    return execute_curl_command("direct/read")

# FastAPI Routes for Random
@app.post("/random/write")
async def random_write(data: CustomData):
    return execute_curl_command("random/write", data.dict())

@app.get("/random/read")
async def random_read():
    return execute_curl_command("random/read")

# FastAPI Routes for Custom
@app.post("/custom/write")
async def custom_write(data: CustomData):
    return execute_curl_command("custom/write", data.dict())

@app.get("/custom/read")
async def custom_read():
    return execute_curl_command("custom/read")