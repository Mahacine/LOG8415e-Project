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
    

    """
    threads = []
    
    # Threads Mappers
    for _, instance_ in manager_instances_dict.items():
        load_dotenv()
        manager_ip = os.getenv('MANAGER_IP')
        t = threading.Thread(target=mysql_setup2.mysql_setup, args=(f"./general/{INSTANCE_KEY_NAME}.pem", manager_ip))
        # Add thread to the global list
        threads.append(t)

    # Start threads
    for t in threads:
        t.start()

    # Wait for threads
    for t in threads:
        t.join()

    print('Infrastructure Setup Done')
    """

if __name__ == "__main__":
    main()