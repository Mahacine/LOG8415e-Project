from fastapi import FastAPI
import uvicorn
import logging
import os
from pydantic import BaseModel
import random
import subprocess
import re
import paramiko

# Configure logging
logging.basicConfig(level=logging.INFO)
logger = logging.getLogger(__name__)

# Create FastAPI app
app = FastAPI()

manager_ip = os.getenv('MANAGER_IP', 'unknown')
worker1_ip = os.getenv('WORKER1_IP', 'unknown')
worker2_ip = os.getenv('WORKER2_IP', 'unknown')

ssh_port = 22
ssh_username = "ubuntu"
private_key_path = '/home/ubuntu/key-pair-lab2.pem'

# Pydantic model for the data
class CustomData(BaseModel):
    first_name: str
    last_name: str

# Function to execute SQL Commands
def execute_ssh_command(command, target_ip):
    try:
        # Create SSH client
        ssh_client = paramiko.SSHClient()
        ssh_client.set_missing_host_key_policy(paramiko.AutoAddPolicy())
        # Load SSH key
        key = paramiko.RSAKey.from_private_key_file(private_key_path)
        ssh_client.connect(target_ip, username=ssh_username, pkey=key)

        # Execute the command over SSH (using sudo for MySQL)
        stdin, stdout, stderr = ssh_client.exec_command(command)
        
        # Capture command output and errors
        output = stdout.read().decode()
        error = stderr.read().decode()
        
        # Close the SSH client
        ssh_client.close()

        # If there's an error, raise an exception
        if error:
            raise HTTPException(status_code=500, detail=f"SSH Error: {error}")
        
        return output
    except Exception as e:
        raise HTTPException(status_code=500, detail=f"SSH Connection Error: {str(e)}")

def get_fastest_worker(worker1_ip, worker2_ip):
    # Function to ping an instance and extract the average round-trip time
    def ping_instance(ip):
        try:
            # Run the ping command and get the output
            result = subprocess.run(['ping', '-c', '4', ip], capture_output=True, text=True)
            # Check if ping was successful
            if result.returncode == 0:
                # Parse the average round-trip time from the ping output
                match = re.search(r'rtt min/avg/max/mdev = [\d.]+/([\d.]+)/', result.stdout)
                if match:
                    return float(match.group(1))  # Return the average time
                else:
                    return None
            else:
                return None
        except Exception as e:
            print(f"Error pinging {ip}: {e}")
            return None

    # Ping both workers and get their average round-trip times
    avg_time1 = ping_instance(worker1_ip)
    avg_time2 = ping_instance(worker2_ip)

    if avg_time1 is None:
        print(f"Failed to ping Worker 1 ({worker1_ip})")
    if avg_time2 is None:
        print(f"Failed to ping Worker 2 ({worker2_ip})")

    # Compare the average ping times
    if avg_time1 is not None and avg_time2 is not None:
        if avg_time1 < avg_time2:
            return 0
        else:
            return 1
    else:
        return 1

def get_fastest_worker_fping(worker1_ip, worker2_ip):
    # Function to ping multiple instances using fping and extract the average round-trip time
    def ping_instances(worker1_ip, worker2_ip):
        try:
            # Run the fping command to ping both worker IPs at once
            command = f"fping -C 1 -q {worker1_ip} {worker2_ip}"
            result = subprocess.run(command, capture_output=True, text=True, shell=True)

            if result.returncode == 0:
                # Parse the average round-trip time for both pings
                # Using regular expression to extract avg time from fping output
                # avg_time1_match = re.search(rf'{worker1_ip}  : (\d+\.\d+)', result.stdout)
                # avg_time2_match = re.search(rf'{worker2_ip}  : (\d+\.\d+)', result.stdout)
                

                elements = result.stderr.split('\n')
                avg_time1 = float(elements[0].split(':')[1])
                avg_time2 = float(elements[1].split(':')[1])
                return avg_time1, avg_time2, result.stderr
            
            else:
                return None, None, result.stderr
        except Exception as e:
            print(f"Error pinging instances: {e}")
            return None, None, result.stderr

    # Get the average ping times for both workers
    avg_time1, avg_time2, result = ping_instances(worker1_ip, worker2_ip)

    if avg_time1 is None:
        print(f"Failed to ping Worker 1 ({worker1_ip})")
    if avg_time2 is None:
        print(f"Failed to ping Worker 2 ({worker2_ip})")

    # Compare the average ping times
    if avg_time1 is not None and avg_time2 is not None:
        if avg_time1 < avg_time2:
            return 0, avg_time1, avg_time2, result
        else:
            return 1 , avg_time1, avg_time2, result
    else:
        return 0, avg_time1, avg_time2, result

# FastAPI Routes for Direct
@app.post("/direct/write")
async def direct_write(data: CustomData):
    query = f'sudo mysql -e "USE sakila; INSERT INTO actor (first_name, last_name) VALUES (\'{data.first_name}\', \'{data.last_name}\');"'
    result = execute_ssh_command(query,manager_ip)
    message =  f"Direct - Write : Manager - {manager_ip} : {result} Inserted ({data.first_name}, {data.last_name}) in table actor"
    logger.info(message)
    return {"message": message}

@app.get("/direct/read")
async def direct_read():
    query = 'sudo mysql -e "USE sakila; SELECT COUNT(*) FROM actor;"'
    result = execute_ssh_command(query,manager_ip)
    message =  f"Direct - Read : Manager - {manager_ip} : {result}"
    logger.info(message)
    return {"message": message}


# FastAPI Routes for Random
@app.post("/random/write")
async def random_write(data: CustomData):
    query = f'sudo mysql -e "USE sakila; INSERT INTO actor (first_name, last_name) VALUES (\'{data.first_name}\', \'{data.last_name}\');"'
    result = execute_ssh_command(query, manager_ip)
    execute_ssh_command(query, worker1_ip)
    execute_ssh_command(query, worker2_ip)
    message =  f"Random - Write : Manager - {manager_ip} : {result} Inserted ({data.first_name}, {data.last_name}) in table actor"
    logger.info(message)
    return {"message": message}

@app.get("/random/read")
async def random_read():
    query = 'sudo mysql -e "USE sakila; SELECT COUNT(*) FROM actor;"'
    workers = [worker1_ip,worker2_ip]
    # Randomly choose a worker index (0 or 1)
    random_index = random.choice([0, 1])
    result = execute_ssh_command(query,workers[random_index])
    message =  f"Random - Read : Worker{random_index+1} - {workers[random_index]} : {result}"
    logger.info(message)
    return {"message": message}


# FastAPI Routes for Custom
@app.post("/custom/write")
async def custom_write(data: CustomData):
    query = f'sudo mysql -e "USE sakila; INSERT INTO actor (first_name, last_name) VALUES (\'{data.first_name}\', \'{data.last_name}\');"'
    result = execute_ssh_command(query, manager_ip)
    execute_ssh_command(query, worker1_ip)
    execute_ssh_command(query, worker2_ip)
    message =  f"Custom - Write : Manager - {manager_ip} : {result} Inserted ({data.first_name}, {data.last_name}) in table actor"
    logger.info(message)
    return {"message": message}

@app.get("/custom/read")
async def custom_read():
    query = 'sudo mysql -e "USE sakila; SELECT COUNT(*) FROM actor;"'
    workers = [worker1_ip,worker2_ip]
    # fastest_index = get_fastest_worker(worker1_ip, worker2_ip)
    fastest_index, avg_time1, avg_time2, result_ping = get_fastest_worker_fping(worker1_ip, worker2_ip)
    result = execute_ssh_command(query,workers[fastest_index])
    message =  f"Custom - Read : Worker{fastest_index+1} - {workers[fastest_index]} : {result} - Worker 1 : {avg_time1}ms VS Worker 2 : {avg_time2}ms"
    logger.info(message)
    return {"message": message}

@app.get("/")
async def root():
    message =  f"Hello from EC2 instance: Proxy - {manager_ip} - {worker1_ip} - {worker2_ip}"
    logger.info(message)
    return {"message": message}