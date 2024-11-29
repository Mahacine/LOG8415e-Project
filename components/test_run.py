import subprocess
import os
import sys

# Command to kill the FastAPI process
kill_command = "python ./components/kill_gatekeeper_fastapi.py"

# Path to your virtual environment's Activate.ps1 script (make sure the path is correct)
venv_activate_script = "./venv/Scripts/Activate.ps1"

# The redeploy command to run after activation
redeploy_command = "python ./components/gate_keeper_deploy.py"

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
    if p.returncode == 0:
        print(f"Command '{command}' executed successfully.")
    else:
        print(f"Error executing command: '{command}'")

# Step 1: Kill the FastAPI process
print("Killing FastAPI process...")
run_command(kill_command)

# Step 2: Activate virtual environment and redeploy FastAPI app
print("Redeploying FastAPI app locally with virtual environment activation...")
full_command = f"& '{os.path.abspath(venv_activate_script)}' ; {redeploy_command}"
run_command(full_command)