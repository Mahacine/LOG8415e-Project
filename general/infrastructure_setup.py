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

# Load environment variables from the .env file
load_dotenv(override=True)

AMI_UBUNTU = 'ubuntu/images/hvm-ssd-gp3/ubuntu-noble-24.04-amd64-server-20240801*'
INSTANCE_KEY_NAME = "key-pair-lab2"

def update_env_variable(key, value, file_path='.env'):
    # Read the current content of the .env file
    with open(file_path, 'r') as file:
        lines = file.readlines()

    # Update the specific variable
    with open(file_path, 'w') as file:
        for line in lines:
            if line.startswith(key):
                file.write(f'{key}={value}\n')
            else:
                file.write(line)
def main():

    instances_ids = []
    manager_instances_dict = {}
    workers_instances_dict = {}
    proxy_instances_dict = {}
    host_instances_dict = {}
    gatekeeper_instances_dict = {}
    manager_instances = []
    workers_instances = []
    proxy_instances = []
    host_instances = []
    gatekeeper_instances = []

    # Connect to ec2 client
    ec2_client = boto3.client('ec2', region_name='us-east-1')

    # Set up instances' parameters (keypair, security group, vpc, image, availability zones)
    # instance.convert_subnet_to_private()
    key_pair = instance.create_key_pair(INSTANCE_KEY_NAME)
    default_vpc_id = instance.get_default_vpc_id()
    security_group = instance.create_security_group('lab_sec_grp_desc', 'lab_sec_grp', default_vpc_id)
    security_group_id = security_group['GroupId']
    availability_zones = instance.get_availability_zones()
    ubuntu_image_id = instance.find_ami(AMI_UBUNTU)
    # endpoint_id = instance.create_instance_connect_endpoint(security_group_id)

    # Define CIDR block for the new private subnet
    private_subnet_cidr = '172.31.96.0/20'
    # Create the private subnet
    private_subnet_id = instance.create_private_subnet(private_subnet_cidr)
    # Create a new route table for the private subnet
    route_table_id = instance.create_route_table()
    # Associate the route table with the private subnet
    instance.associate_route_table(route_table_id, private_subnet_id)
    nat_gateway_id = instance.create_nat_gateway()
    instance.update_route_table(nat_gateway_id)
    update_env_variable('PRIVATE_SUBNET', private_subnet_id)
    update_env_variable('NAT_GATEWAY', nat_gateway_id)
    update_env_variable('ROUTE_TABLE_ID', route_table_id)

    # update_env_variable('ENDPOINT_ID', endpoint_id)
    
    # Manager : setup 1 t2.micro instances
    for i in range(1):
        instance_dict_key = f'instance_{i+1}'
        manager_instances_dict[instance_dict_key] = instance.create_ec2_instance(
            instance_type='t2.micro',
            key_name=key_pair.key_name,
            security_group_id=security_group_id,
            image_id=ubuntu_image_id,
            user_data='',
            availability_zone=random.choice(availability_zones),
            vpc_id=default_vpc_id,
            is_public=False
        )

        instances_ids.append(manager_instances_dict[instance_dict_key].instance_id)

        manager_instances.append(manager_instances_dict[instance_dict_key].instance_id)

        update_env_variable('MANAGER_ID', manager_instances_dict[instance_dict_key].instance_id)
        update_env_variable('MANAGER_IP', manager_instances_dict[instance_dict_key].private_ip_address)
    

    # Workers : setup 2 t2.micro instances
    for i in range(2):
        instance_dict_key = f'instance_{i+1}'
        workers_instances_dict[instance_dict_key] = instance.create_ec2_instance(
            instance_type='t2.micro',
            key_name=key_pair.key_name,
            security_group_id=security_group_id,
            image_id=ubuntu_image_id,
            user_data='',
            availability_zone=random.choice(availability_zones),
            vpc_id=default_vpc_id,
            is_public=False
        )

        instances_ids.append(workers_instances_dict[instance_dict_key].instance_id)

        workers_instances.append(workers_instances_dict[instance_dict_key].instance_id)

        update_env_variable(f'WORKER{i+1}_ID', workers_instances_dict[instance_dict_key].instance_id)
        update_env_variable(f'WORKER{i+1}_IP', workers_instances_dict[instance_dict_key].private_ip_address)
    
    # Proxy : setup 1 t2.large instances
    for i in range(1):
        instance_dict_key = f'instance_{i+1}'
        proxy_instances_dict[instance_dict_key] = instance.create_ec2_instance(
            instance_type='t2.large',
            key_name=key_pair.key_name,
            security_group_id=security_group_id,
            image_id=ubuntu_image_id,
            user_data='',
            availability_zone=random.choice(availability_zones),
            vpc_id=default_vpc_id,
            is_public=False
        )

        instances_ids.append(proxy_instances_dict[instance_dict_key].instance_id)

        proxy_instances.append(proxy_instances_dict[instance_dict_key].instance_id)

        update_env_variable('PROXY_ID', proxy_instances_dict[instance_dict_key].instance_id)
        update_env_variable('PROXY_IP', proxy_instances_dict[instance_dict_key].private_ip_address)

    # Trusted Host : setup 1 t2.large instances
    for i in range(1):
        instance_dict_key = f'instance_{i+1}'
        host_instances_dict[instance_dict_key] = instance.create_ec2_instance(
            instance_type='t2.large',
            key_name=key_pair.key_name,
            security_group_id=security_group_id,
            image_id=ubuntu_image_id,
            user_data='',
            availability_zone=random.choice(availability_zones),
            vpc_id=default_vpc_id,
            is_public=False
        )

        instances_ids.append(host_instances_dict[instance_dict_key].instance_id)

        host_instances.append(host_instances_dict[instance_dict_key].instance_id)

        update_env_variable('HOST_ID', host_instances_dict[instance_dict_key].instance_id)
        update_env_variable('HOST_IP', host_instances_dict[instance_dict_key].private_ip_address)
    
    # Gatekeeper : setup 1 t2.large instances
    for i in range(1):
        instance_dict_key = f'instance_{i+1}'
        gatekeeper_instances_dict[instance_dict_key] = instance.create_ec2_instance(
            instance_type='t2.large',
            key_name=key_pair.key_name,
            security_group_id=security_group_id,
            image_id=ubuntu_image_id,
            user_data='',
            availability_zone=random.choice(availability_zones),
            vpc_id=default_vpc_id,
            is_public=True
        )

        instances_ids.append(gatekeeper_instances_dict[instance_dict_key].instance_id)

        gatekeeper_instances.append(gatekeeper_instances_dict[instance_dict_key].instance_id)

        update_env_variable('GATE_ID', gatekeeper_instances_dict[instance_dict_key].instance_id)
        update_env_variable('GATE_IP', gatekeeper_instances_dict[instance_dict_key].public_ip_address)
        update_env_variable('GATE_DNS', gatekeeper_instances_dict[instance_dict_key].public_dns_name)
        update_env_variable('GATE_PRIVATE_IP', gatekeeper_instances_dict[instance_dict_key].private_ip_address)

    while True:
        statuses = ec2_client.describe_instance_status(InstanceIds=instances_ids)
        all_ok = True
            
        for status in statuses['InstanceStatuses']:
            # Check if both 'InstanceStatus' and 'SystemStatus' are 'ok' for each instance
            if status['InstanceStatus']['Status'] != 'ok' or status['SystemStatus']['Status'] != 'ok':
                all_ok = False
                break
            
        if all_ok:
            break
            
        time.sleep(1)
    
    # Assign custom security groups
    # Trusted Host
    gk_private_ip = gatekeeper_instances_dict['instance_1'].private_ip_address + '/32'
    print(gk_private_ip)
    trusted_host_sg = instance.create_custom_security_group('trusted_host_sg', 'trusted_host_sg', default_vpc_id, gk_private_ip)
    instance.assign_custom_security_group_to_instance(host_instances[0], trusted_host_sg['GroupId'])
    # Proxy
    th_private_ip = host_instances_dict['instance_1'].private_ip_address + '/32'
    print(th_private_ip)
    proxy_sg = instance.create_custom_security_group('proxy_sg', 'proxy_sg', default_vpc_id, th_private_ip)
    instance.assign_custom_security_group_to_instance(proxy_instances[0], proxy_sg['GroupId'])
    # Cluster
    proxy_private_ip = proxy_instances_dict['instance_1'].private_ip_address + '/32'
    print(proxy_private_ip)
    cluster_sg = instance.create_custom_security_group('cluster_sg', 'cluster_sg', default_vpc_id, proxy_private_ip)
    instance.assign_custom_security_group_to_instance(manager_instances[0], cluster_sg['GroupId'])
    instance.assign_custom_security_group_to_instance(workers_instances[0], cluster_sg['GroupId'])
    instance.assign_custom_security_group_to_instance(workers_instances[1], cluster_sg['GroupId'])
    
    """
    # IP TABLES
    # Load environment variables from .env file
    load_dotenv()

    # Get instance details from environment variables
    gatekeeper_ip = os.getenv('GATE_IP')
    trusted_host_ip = os.getenv('HOST_IP')
    proxy_ip = os.getenv('PROXY_IP')
    manager_ip = os.getenv('MANAGER_IP')
    worker1_ip = os.getenv('WORKER1_IP')
    worker2_ip = os.getenv('WORKER2_IP')

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
    """

if __name__ == "__main__":
    main()