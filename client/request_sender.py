import asyncio
import aiohttp
import time
import os
from dotenv import load_dotenv
import requests
from datetime import datetime,timezone
import nest_asyncio
import json
from pydantic import BaseModel
from requests.exceptions import RequestException, HTTPError
import subprocess
import sys

nest_asyncio.apply()

# Load environment variable (DNS) from the .env file
load_dotenv(override=True)
GATE_DNS = os.getenv('GATE_DNS', '')

class CustomData(BaseModel):
    first_name: str
    last_name: str

def refresh_app():
    # Command to kill the FastAPI process
    kill_command = "python ./components/kill_gatekeeper_fastapi.py"

    # Path to your virtual environment's Activate.ps1 script (make sure the path is correct)
    venv_activate_script = "./venv/Scripts/Activate.ps1"

    # The redeploy command to run after activation
    # redeploy_command = "python ./components/gate_keeper_deploy.py"
    redeploy_command = 'Start-Process -FilePath "python.exe" -ArgumentList "./components/gate_keeper_deploy.py" -WindowStyle Hidden'

    # Function to run a command in PowerShell
    def run_command(command):
        # Use subprocess.Popen() to execute the command in PowerShell
        p = subprocess.Popen(
            ["powershell.exe", "-Command", command],
            stdout=sys.stdout,  # Redirect stdout to the console
            stderr=sys.stderr   # Redirect stderr to the console
        )

        # Wait for the process to complete and capture the output
        p.communicate()

        # Check the return code to determine if it was successful
        """
        if p.returncode == 0:
            print(f"Command '{command}' executed successfully.")
        else:
            print(f"Error executing command: '{command}'")
        """

    # Step 1: Kill the FastAPI process
    # print("Killing FastAPI process...")
    print("Refreshing app...")
    run_command(kill_command)

    # Step 2: Activate virtual environment and redeploy FastAPI app
    # print("Redeploying FastAPI app locally with virtual environment activation...")
    full_command = f"& '{os.path.abspath(venv_activate_script)}' ; {redeploy_command}"
    run_command(full_command)

# A generic method to call the load balancer's endpoint
async def call_endpoint_http(session, request_num, scenario, request_type, custom_data):

    load_dotenv(override=True)
    GATE_DNS = os.getenv('GATE_DNS', '')
    
    url = f"http://{GATE_DNS}:8000/{scenario}/{request_type}"
    headers = {'content-type': 'application/json'}

    # For failed requests, try for 3 times at most
    retries = 3
    backoff_factor = 1
    for attempt in range(retries):
        try:
            if custom_data is None:
                async with session.get(url, headers=headers) as response:
                    status_code = response.status
                    response_json = await response.json()
                    response_text = await response.text()
                    if status_code == 200:
                        print(f"Request {request_num} *** Status Code: {status_code} *** Response: {response_text}")
                    else:
                        print(f"Request {request_num} *** Status Code: {status_code} *** Response: {response_json.get('detail')}")
                    return status_code, response_json
            else:
                payload = custom_data.dict()
                json_payload = json.dumps(payload)  # Convert dict to JSON string
                async with session.post(url, headers=headers, data=json_payload) as response:
                    status_code = response.status
                    response_json = await response.json()
                    response_text = await response.text()
                    if status_code == 200:
                        print(f"Request {request_num} *** Status Code: {status_code} *** Response: {response_text}")
                    else:
                        print(f"Request {request_num} *** Status Code: {status_code} *** Response: {response_json.get('detail')}")
                    return status_code, response_json

        except Exception as e:
            print(f"Request {request_num}: Attempt {attempt + 1}/{retries} failed - {str(e)}")
            if attempt < retries - 1:
                await asyncio.sleep(backoff_factor * (2 ** attempt))
    
    print(f"Request {request_num}: All retry attempts failed")
    return None, "All retry attempts failed"

# Function to check if GK's fastapi is up and running   
def check_health(delay):
    while True:
        load_dotenv(override=True)
        GATE_DNS = os.getenv('GATE_DNS', '')
        
        # Message to display when health checks are being performed, but the DNS is still not setup
        # The load balancer's instance setup is not complete yet (dns still not available)
        if not GATE_DNS:
            print("GateKeeper DNS is not received yet!")

        # Send request to /health endpoint once dns received (made available in the env variable)
        else:
            try:

                print("GateKeeper DNS Received :", GATE_DNS)

                url = f"http://{GATE_DNS}:8000/health"
                response = requests.get(url)

                print(f"Status Code: {response.status_code}")
                print(f"Response: {response.json()}")

                # Break the loop once a positive response is received
                if response.status_code == 200 and response.json().get("status") == "OK":
                    print("GateKeeper is UP!")
                    print('GateKeeper DNS :', GATE_DNS)
                    return True
                else:
                    print(f"Health check failed, retrying...")

            except requests.ConnectionError:
                print(f"Waiting for setup to complete...")
        
        # Otherwise, pause for a delay before sending the next health check
        time.sleep(delay)

# Function to check if GK's FastAPI is up and running
def invalidate_url():
    load_dotenv(override=True)
    GATE_DNS = os.getenv('GATE_DNS', '')

    try:
        url = f"http://{GATE_DNS}:8000/other"
        response = requests.get(url)

        # Check if the response was successful
        response.raise_for_status()

        # Print the successful response
        print(f"Status Code: {response.status_code}")
        print(f"Response: {response.json()}")

    except HTTPError as http_err:
        # Handle HTTP errors (e.g., 404, 500, etc.)
        print(f"HTTP error occurred: {http_err}")
        if response is not None:
            print(f"Response content: {response.text}")
    
    except RequestException as req_err:
        # Handle other types of request exceptions (e.g., network issues)
        print(f"Request error occurred: {req_err}")

    except Exception as err:
        # Handle other unexpected errors
        print(f"An error occurred: {err}")

async def invalid_write_request():
    # Load environment variables
    load_dotenv(override=True)
    GATE_DNS = os.getenv('GATE_DNS', '')

    # Define the scenario and request type for the URL
    scenario = "direct"
    request_type = "write"
    
    # Construct the request URL
    url = f"http://{GATE_DNS}:8000/{scenario}/{request_type}"
    
    # Set the headers for the request
    headers = {'Content-Type': 'application/json'}

    # Create an instance of CustomData with a missing last_name
    custom_data = CustomData(first_name='Test',last_name='')

    # Convert the payload to a dictionary and then to JSON
    payload = custom_data.dict()
    json_payload = json.dumps(payload)

    # Use aiohttp to send the request asynchronously
    async with aiohttp.ClientSession() as session:
        async with session.post(url, headers=headers, data=json_payload) as response:
            # Get the status code of the response
            status_code = response.status
            
            # Try to get the JSON response (error message)
            try:
                response_json = await response.json()
            except Exception as e:
                response_json = {"error": str(e)}

            # If the status code is 400, it means the request was invalid due to missing fields
            if status_code == 400:
                error_message = response_json.get("detail", "No error message found.")
                print(f"Error: {error_message}")
            else:
                # If the response is not an error, print the response
                response_text = await response.text()
                print(f"Response: {response_text}")

"""
# Generic function to calculate execution time for a couple of tasks
async def measure_scenario_time(scenario, request_type, num_requests):
    start_time = time.time()
    
    # Run concurrently the total amount of request for the specified cluster
    async with aiohttp.ClientSession() as session:
        if request_type == 'read':
            tasks = [call_endpoint_http(session, i, scenario, request_type, None) for i in range(num_requests)]
        else:
            tasks = [call_endpoint_http(session, i, scenario, request_type, CustomData(first_name='T'+str(i)+'-'+scenario,last_name='T'+str(i)+'-'+request_type)) for i in range(num_requests)]
        await asyncio.gather(*tasks)
    
    end_time = time.time()
    
    total_time = end_time - start_time
    avg_time = total_time / num_requests
    
    return total_time, avg_time
"""

async def measure_scenario_time(scenario, request_type, start_request, num_requests):
    start_time = time.time()
    
    # Run concurrently the total amount of request for the specified cluster
    async with aiohttp.ClientSession() as session:
        if request_type == 'read':
            tasks = [call_endpoint_http(session, i, scenario, request_type, None) for i in range(start_request, start_request + num_requests)]
        else:
            tasks = [call_endpoint_http(session, i, scenario, request_type, CustomData(first_name='T'+str(i)+'-'+scenario,last_name='T'+str(i)+'-'+request_type)) for i in range(start_request, start_request + num_requests)]
        await asyncio.gather(*tasks)
    
    end_time = time.time()
    
    total_time = end_time - start_time
    avg_time = total_time / num_requests
    
    return total_time, avg_time

"""
async def measure_scenario_concurrently(num_requests, scenario):
    
    print(f"\n****Measuring {scenario} Read and Write concurrently****\n")

    # Create a task for each request type
    task1 = asyncio.create_task(measure_scenario_time(scenario, 'read', num_requests))
    await asyncio.sleep(0)
    task2 = asyncio.create_task(measure_scenario_time(scenario, 'write', num_requests))
    # Wait for both tasks to finish concurrently
    result1, result2 = await asyncio.gather(task1, task2)

    # Unpack the results for each cluster
    total_time_1, avg_time_1 = result1
    total_time_2, avg_time_2 = result2
    
    # Print results for READ
    print(f"\n****{scenario} : Read****\n")
    print(f"Total time taken for endpoint 1: {total_time_1:.2f} seconds")
    print(f"Average time per request for endpoint 1: {avg_time_1:.4f} seconds")
    
    # Print results for WRITE
    print(f"\n****{scenario} : Write****\n")
    print(f"Total time taken for endpoint 2: {total_time_2:.2f} seconds")
    print(f"Average time per request for endpoint 2: {avg_time_2:.4f} seconds")
"""
# Measure the scenario concurrently with chunked requests
async def measure_scenario_concurrently(num_requests, scenario):
    
    print(f"\n****Measuring {scenario} Read and Write concurrently****\n")

    chunk_size = 100
    total_time_1, avg_time_1 = 0, 0
    total_time_2, avg_time_2 = 0, 0

    # Process requests in chunks (both read and write together)
    for start_request in range(0, num_requests, chunk_size):
        chunk_end = min(start_request + chunk_size, num_requests)
        
        # print(f"Processing requests {start_request} to {chunk_end - 1}...")
        
        # For each chunk, handle both read and write requests together
        task1 = asyncio.create_task(measure_scenario_time(scenario, 'read', start_request + 1, chunk_end - start_request))
        task2 = asyncio.create_task(measure_scenario_time(scenario, 'write', start_request + 1, chunk_end - start_request))
        
        # Wait for both tasks to complete
        result1, result2 = await asyncio.gather(task1, task2)

        total_time_1 += result1[0]
        avg_time_1 += result1[1]
        total_time_2 += result2[0]
        avg_time_2 += result2[1]

        # After processing this chunk, refresh app and check health
        refresh_app()
        check_health(2)

    # Calculate average times for each scenario
    avg_time_1 /= (num_requests / chunk_size)  # Average across all read chunks
    avg_time_2 /= (num_requests / chunk_size)  # Average across all write chunks

    # Print results for READ
    print(f"\n****{scenario} : Read****\n")
    print(f"Total time taken for endpoint 1: {total_time_1:.2f} seconds")
    print(f"Average time per request for endpoint 1: {avg_time_1:.4f} seconds")
    
    # Print results for WRITE
    print(f"\n****{scenario} : Write****\n")
    print(f"Total time taken for endpoint 2: {total_time_2:.2f} seconds")
    print(f"Average time per request for endpoint 2: {avg_time_2:.4f} seconds")

async def main ():
    num_requests = 1000
    print('***Random***')
    await measure_scenario_concurrently(num_requests, 'random')
    await asyncio.sleep(2)
    print('***Custom***')
    await measure_scenario_concurrently(num_requests, 'custom')
    await asyncio.sleep(2)
    print('***Direct Hit***')
    await measure_scenario_concurrently(num_requests, 'direct')


if __name__ == "__main__":
    print('***Starting infrastructure setup and App deployment***')
    start_time = datetime.now(timezone.utc)
    check_health(2)
    print('Infrastructure setup and App deployment Time - ', datetime.now(timezone.utc)-start_time)
    print('\n***Initial Test for invalid url***\n')
    invalidate_url()
    print('\n***Initial Test for missing data in request***\n')
    asyncio.run(invalid_write_request())
    print('\n***Starting client requests***\n')
    asyncio.run(main())