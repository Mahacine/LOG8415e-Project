import instance
import random
import time
import boto3
import threading
import os
from dotenv import load_dotenv
from datetime import datetime,timezone
import mysql_setup
import mysql_setup2
import time
import paramiko


def main():

    load_dotenv(override=True)

    # Get instance details from environment variables
    gatekeeper_ip = os.getenv('GATE_IP')
    gatekeeper_private_ip = os.getenv('GATE_PRIVATE_IP')
    trusted_host_ip = os.getenv('HOST_IP')
    proxy_ip = os.getenv('PROXY_IP')
    manager_ip = os.getenv('MANAGER_IP')
    worker1_ip = os.getenv('WORKER1_IP')
    worker2_ip = os.getenv('WORKER2_IP')
    
    # Assign custom security groups
    # Trusted Host
    gk_private_ip = gatekeeper_private_ip + '/32'
    print(gk_private_ip)
    # Proxy
    th_private_ip = trusted_host_ip + '/32'
    print(th_private_ip)
    # Cluster
    proxy_private_ip = proxy_ip + '/32'
    print(proxy_private_ip)

    # Load SSH key
    key = paramiko.RSAKey.from_private_key_file('./general/key-pair-lab2.pem')
    username = 'ubuntu'

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
    instance.configure_iptables(trusted_host_client, gk_private_ip, 'Trusted Host')

    # Connect to Proxy
    proxy_client = paramiko.SSHClient()
    proxy_client.set_missing_host_key_policy(paramiko.AutoAddPolicy())
    proxy_channel = trusted_host_client.get_transport().open_channel("direct-tcpip", (proxy_ip, 22), (trusted_host_ip, 0))
    proxy_client.connect(proxy_ip, username=username, pkey=key, sock=proxy_channel)
    instance.configure_iptables(proxy_client, th_private_ip, 'Proxy')

    # Connect to Manager and run the command
    manager_client = paramiko.SSHClient()
    manager_client.set_missing_host_key_policy(paramiko.AutoAddPolicy())
    manager_channel = proxy_client.get_transport().open_channel("direct-tcpip", (manager_ip, 22), (proxy_ip, 0))
    manager_client.connect(manager_ip, username=username, pkey=key, sock=manager_channel)
    instance.configure_iptables(manager_client, proxy_private_ip, 'Manager')

    # Connect to Worker1 and run the command
    worker1_client = paramiko.SSHClient()
    worker1_client.set_missing_host_key_policy(paramiko.AutoAddPolicy())
    worker1_channel = proxy_client.get_transport().open_channel("direct-tcpip", (worker1_ip, 22), (proxy_ip, 0))
    worker1_client.connect(worker1_ip, username=username, pkey=key, sock=worker1_channel)
    instance.configure_iptables(worker1_client, proxy_private_ip, 'Worker1')

    # Connect to Worker1 and run the command
    worker2_client = paramiko.SSHClient()
    worker2_client.set_missing_host_key_policy(paramiko.AutoAddPolicy())
    worker2_channel = proxy_client.get_transport().open_channel("direct-tcpip", (worker2_ip, 22), (proxy_ip, 0))
    worker2_client.connect(worker2_ip, username=username, pkey=key, sock=worker2_channel)
    instance.configure_iptables(worker2_client, proxy_private_ip, 'Worker2')

    manager_client.close()
    worker2_client.close()
    worker1_client.close()
    proxy_client.close()
    trusted_host_client.close()
    gatekeeper_client.close()

if __name__ == "__main__":
    main()