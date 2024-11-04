from fastapi import FastAPI
import uvicorn
import logging
import os

# Configure logging
logging.basicConfig(level=logging.INFO)
logger = logging.getLogger(__name__)

# Create FastAPI app
app = FastAPI()

@app.get("/")
async def root():
    manager_ip = os.getenv('MANAGER_IP', 'unknown')
    worker1_ip = os.getenv('WORKER1_IP', 'unknown')
    worker2_ip = os.getenv('WORKER2_IP', 'unknown')
    message =  f"Hello from EC2 instance: Proxy - {manager_ip} - {worker1_ip} - {worker2_ip}"
    logger.info(message)
    return {"message": message}