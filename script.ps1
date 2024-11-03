# Install AWS CLI 
# pip install awscli
# Configure credentials in %USERPROFILE%\.aws\credentials

# Setup a virtual environment
python -m venv venv

# Execute this script by running .\script.ps1 in PowerShell

# Activate virtual environment
& ./venv/Scripts/Activate.ps1

# Install required libraries
pip install boto3 paramiko scp matplotlib aiohttp python-dotenv requests pandas nest-asyncio

# Infrastructure setup
python ./general/infrastructure_setup.py

# Ask the user whether to delete the infrastructure
$confirm = Read-Host "Do you want to delete the infrastructure? (y/n)"

if ($confirm -ieq "y") {
    Write-Host "Deleting infrastructure..."
    python ./general/cleanup.py
} else {
    Write-Host "Deletion canceled."
}

Write-Host "Script completed. Press any key to continue..."
$x = $host.UI.RawUI.ReadKey("NoEcho,IncludeKeyDown")