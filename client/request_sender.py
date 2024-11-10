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

nest_asyncio.apply()

# Load environment variable (DNS) from the .env file
load_dotenv(override=True)
GATE_DNS = os.getenv('GATE_DNS', '')

class CustomData(BaseModel):
    first_name: str
    last_name: str

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

# Function to check if LB's fastapi is up and running   
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


# Generic function to calculate execution time for a couple of tasks
# Calculates the execution time for each cluster
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

async def main ():
    num_requests = 10
    print('***Random***')
    await measure_scenario_concurrently(num_requests, 'random')
    print('***Custom***')
    await measure_scenario_concurrently(num_requests, 'custom')
    print('***Direct Hit***')
    await measure_scenario_concurrently(num_requests, 'direct')


if __name__ == "__main__":
    print('***Starting infrastructure setup and App deployment***')
    start_time = datetime.now(timezone.utc)
    check_health(2)
    print('Infrastructure setup and App deployment Time - ', datetime.now(timezone.utc)-start_time)
    print('***Starting client requests***')
    asyncio.run(main())