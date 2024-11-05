from fastapi import FastAPI
import uvicorn
import logging
import os
from pydantic import BaseModel

# Configure logging
logging.basicConfig(level=logging.INFO)
logger = logging.getLogger(__name__)

# Create FastAPI app
app = FastAPI()

manager_ip = os.getenv('MANAGER_IP', 'unknown')
worker1_ip = os.getenv('WORKER1_IP', 'unknown')
worker2_ip = os.getenv('WORKER2_IP', 'unknown')

@app.get("/")
async def root():
    message =  f"Hello from EC2 instance: Proxy - {manager_ip} - {worker1_ip} - {worker2_ip}"
    logger.info(message)
    return {"message": message}

# Pydantic model for the data
class CustomData(BaseModel):
    key: str
    value: str

# FastAPI Routes for Direct
@app.post("/direct/write")
async def direct_write(data: CustomData):
    message =  f"Direct - Write : Proxy - {manager_ip} - {worker1_ip} - {worker2_ip}"
    logger.info(message)
    return {"message": message}

@app.get("/direct/read")
async def direct_read():
    message =  f"Direct - Read : Proxy - {manager_ip} - {worker1_ip} - {worker2_ip}"
    logger.info(message)
    return {"message": message}


# FastAPI Routes for Random
@app.post("/random/write")
async def random_write(data: CustomData):
    message =  f"Random - Write : Proxy - {manager_ip} - {worker1_ip} - {worker2_ip}"
    logger.info(message)
    return {"message": message}

@app.get("/random/read")
async def random_read():
    message =  f"Random - Read : Proxy - {manager_ip} - {worker1_ip} - {worker2_ip}"
    logger.info(message)
    return {"message": message}


# FastAPI Routes for Custom
@app.post("/custom/write")
async def custom_write(data: CustomData):
    message =  f"Custom - Write : Proxy - {manager_ip} - {worker1_ip} - {worker2_ip}"
    logger.info(message)
    return {"message": message}

@app.get("/custom/read")
async def custom_read():
    message =  f"Custom - Read : Proxy - {manager_ip} - {worker1_ip} - {worker2_ip}"
    logger.info(message)
    return {"message": message}