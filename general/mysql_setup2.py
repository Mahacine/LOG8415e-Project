import os
import paramiko
from dotenv import load_dotenv
import argparse

# Define connection parameters
port = 22
username = 'ubuntu'

def mysql_setup(key_file_path, target_ip):

    # Load environment variables from .env file
    load_dotenv()

    # Get instance details from environment variables
    gatekeeper_ip = os.getenv('GATE_IP')
    trusted_host_ip = os.getenv('HOST_IP')
    proxy_ip = os.getenv('PROXY_IP')

    # Load SSH key
    key = paramiko.RSAKey.from_private_key_file(key_file_path)

    # Connect to Gatekeeper
    gatekeeper_client = paramiko.SSHClient()
    gatekeeper_client.set_missing_host_key_policy(paramiko.AutoAddPolicy())
    gatekeeper_client.connect(gatekeeper_ip, username=username, pkey=key)

    # Connect to Trusted Host
    trusted_host_client = paramiko.SSHClient()
    trusted_host_client.set_missing_host_key_policy(paramiko.AutoAddPolicy())
    gatekeeper_transport = gatekeeper_client.get_transport()
    trusted_host_channel = gatekeeper_transport.open_channel("direct-tcpip", (trusted_host_ip, 22), (gatekeeper_ip, 0))
    trusted_host_client.connect(trusted_host_ip, username=username, pkey=key, sock=trusted_host_channel)

    # Connect to Proxy
    proxy_client = paramiko.SSHClient()
    proxy_client.set_missing_host_key_policy(paramiko.AutoAddPolicy())
    proxy_channel = trusted_host_client.get_transport().open_channel("direct-tcpip", (proxy_ip, 22), (trusted_host_ip, 0))
    proxy_client.connect(proxy_ip, username=username, pkey=key, sock=proxy_channel)

    # Connect to Manager and run the command
    manager_client = paramiko.SSHClient()
    manager_client.set_missing_host_key_policy(paramiko.AutoAddPolicy())
    manager_channel = proxy_client.get_transport().open_channel("direct-tcpip", (target_ip, 22), (proxy_ip, 0))
    manager_client.connect(target_ip, username=username, pkey=key, sock=manager_channel)

    # Update package index
    print("Starting package index update...")
    stdin, stdout, stderr = manager_client.exec_command('sudo apt-get update')
    print(stdout.read().decode().strip())
    error = stderr.read().decode().strip()
    if error:
        print(f"Error during package index update: {error}")
    else:
        print("Package index update completed.\n")

    # Install MySQL Server
    print("Starting MySQL Server installation...")
    stdin, stdout, stderr = manager_client.exec_command('sudo apt-get install -y mysql-server')
    print(stdout.read().decode().strip())
    error = stderr.read().decode().strip()
    if error:
        print(f"Error during MySQL Server installation: {error}")
    else:
        print("MySQL Server installation completed.\n")

    # Download Sakila Database
    print("Downloading Sakila Database...")
    stdin, stdout, stderr = manager_client.exec_command('wget http://downloads.mysql.com/docs/sakila-db.tar.gz')
    print(stdout.read().decode().strip())
    error = stderr.read().decode().strip()
    if error:
        print(f"Error during Sakila Database download: {error}")
    else:
        print("Sakila Database download completed.\n")

    # Install tar Utility
    print("Installing tar utility...")
    stdin, stdout, stderr = manager_client.exec_command('sudo apt-get install -y tar')
    print(stdout.read().decode().strip())
    error = stderr.read().decode().strip()
    if error:
        print(f"Error during tar utility installation: {error}")
    else:
        print("tar utility installation completed.\n")

    # Unzip Sakila Database
    print("Unzipping Sakila Database...")
    stdin, stdout, stderr = manager_client.exec_command('tar -xzf sakila-db.tar.gz')
    print(stdout.read().decode().strip())
    error = stderr.read().decode().strip()
    if error:
        print(f"Error during unzipping Sakila Database: {error}")
    else:
        print("Sakila Database unzipped.\n")

    # Load Sakila Schema
    print("Loading Sakila Schema...")
    stdin, stdout, stderr = manager_client.exec_command('sudo mysql < sakila-db/sakila-schema.sql')
    print(stdout.read().decode().strip())
    error = stderr.read().decode().strip()
    if error:
        print(f"Error during loading Sakila Schema: {error}")
    else:
        print("Sakila Schema loading completed.\n")

    # Load Sakila Data
    print("Loading Sakila Data...")
    stdin, stdout, stderr = manager_client.exec_command('sudo mysql < sakila-db/sakila-data.sql')
    print(stdout.read().decode().strip())
    error = stderr.read().decode().strip()
    if error:
        print(f"Error during loading Sakila Data: {error}")
    else:
        print("Sakila Data loading completed.\n")

    # Check MySQL Service Status
    print("Checking MySQL service status...")
    stdin, stdout, stderr = manager_client.exec_command('sudo systemctl status mysql')
    print(stdout.read().decode().strip())
    error = stderr.read().decode().strip()
    if error:
        print(f"Error checking MySQL service status: {error}")
    else:
        print("MySQL service status checked.\n")

    # List Databases in MySQL
    print("Listing databases in MySQL...")
    commands = [
        'sudo mysql -e "USE sakila; SHOW FULL TABLES;"',
        'sudo mysql -e "USE sakila; SELECT COUNT(*) FROM film;"',
        'sudo mysql -e "USE sakila; SELECT COUNT(*) FROM film_text;"',
        'sudo mysql -e "USE sakila; SHOW DATABASES;"'
    ]
    for command in commands:
        print(f"Executing: {command}")
        stdin, stdout, stderr = manager_client.exec_command(command)
        output = stdout.read().decode().strip()
        error = stderr.read().decode().strip()

        if output:
            print(f"Output: {output}")
        if error:
            print(f"Error: {error}")

    # Sysbench install
    print("Installing Sysbench...")
    stdin, stdout, stderr = manager_client.exec_command('sudo apt-get install -y sysbench')
    print(stdout.read().decode().strip())
    error = stderr.read().decode().strip()
    if error:
        print(f"Error installing Sysbench: {error}")
    else:
        print("Sysbench installed.\n")
    
    """
    # Load Sakila Data
    print("Creating dbtest database...")
    stdin, stdout, stderr = manager_client.exec_command('sudo mysql < create database dbtest;')
    print(stdout.read().decode().strip())
    error = stderr.read().decode().strip()
    if error:
        print(f"Error creating dbtest database: {error}")
    else:
        print("dbtest database created.\n")
    """

    # Prepare for benchmark
    print("Preparing...")
    stdin, stdout, stderr = manager_client.exec_command('sudo sysbench /usr/share/sysbench/oltp_read_only.lua --mysql-user="root" --mysql-db=sakila prepare')
    print(stdout.read().decode().strip())
    error = stderr.read().decode().strip()
    if error:
        print(f"Error preparing: {error}")
    else:
        print("Prepared.\n")

    # Load Sakila Data
    print("Benchmark...")
    stdin, stdout, stderr = manager_client.exec_command('sudo sysbench /usr/share/sysbench/oltp_read_only.lua --mysql-user="root" --mysql-db=sakila run')
    # Get the output from stdout and stderr
    output = stdout.read().decode().strip()
    error = stderr.read().decode().strip()

    # Define the path for the result file
    result_file_path = "./general/mysql_benchmark_results.txt"

    # Write the output (stdout and stderr) to a file
    with open(result_file_path, "w") as result_file:
        # Write standard output (stdout)
        result_file.write("Benchmark Output:\n")
        result_file.write(output + "\n")

        # If there's any error in stderr, write it as well
        if error:
            result_file.write("\nError Output:\n")
            result_file.write(error + "\n")

        # Optionally, print a message indicating the file is written
        print(f"Benchmark results written to {result_file_path}.")
    
    if error:
        print(f"Error benchmarking: {error}")
    else:
        print("Benchmark done.\n")

    # Clean up
    manager_client.close()
    proxy_client.close()
    trusted_host_client.close()
    gatekeeper_client.close()

if __name__ == "__main__":
    parser = argparse.ArgumentParser(description='MySQL Setup Script')
    parser.add_argument('target', type=str, help='Target type')
    
    args = parser.parse_args()
    print(args.target)

    load_dotenv()
    target_ip = os.getenv(args.target)
    print(target_ip)

    mysql_setup('./general/key-pair-lab2.pem', target_ip)