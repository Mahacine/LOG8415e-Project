import boto3
import paramiko

# Create a Boto3 client for EC2 Instance Connect
client = boto3.client('ec2-instance-connect')

# Define your variables
instance_id = 'i-09669d081ed629c2f'  # Replace with your instance ID
instance_os_user = 'ubuntu'         # Replace with your OS user
private_key_path = "./general/key-pair-lab2.pem"  # Replace with your private key path

# Load the private key and generate the public key
key = paramiko.RSAKey.from_private_key_file(private_key_path)
public_key = f'ssh-rsa {key.get_base64()}'

# Send the SSH public key
response = client.send_ssh_public_key(
    InstanceId=instance_id,
    InstanceOSUser=instance_os_user,
    SSHPublicKey=public_key
)

# Check response status
if response['Success'] == True:
    print("SSH public key sent successfully.")
else:
    print("Failed to send SSH public key:", response)
    exit()

# Create SSH client and connect
ssh_client = paramiko.SSHClient()
ssh_client.set_missing_host_key_policy(paramiko.AutoAddPolicy())

# proxy_jump_command=f'aws ec2-instance-connect open-tunnel --instance-id {instance_id}'
# proxy = paramiko.ProxyCommand(proxy_jump_command)

# Connect to the instance using the public DNS or IP
hostname = '172.31.15.49'  # Replace with your instance's public DNS or IP
ssh_client.connect(hostname=hostname, username=instance_os_user, pkey=key)

# Execute a command (e.g., 'ls') and get the output
stdin, stdout, stderr = ssh_client.exec_command('ls -l')
output = stdout.read().decode()
error_output = stderr.read().decode()

# Print the output
if output:
    print("Command output:\n", output)
if error_output:
    print("Error output:\n", error_output)

# Close the SSH connection
ssh_client.close()