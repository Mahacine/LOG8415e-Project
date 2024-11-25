import boto3
import time
import os
from dotenv import load_dotenv

INSTANCE_KEY_NAME = "key-pair-lab2"
key_pair_names = [INSTANCE_KEY_NAME]
security_group_names = ['lab_sec_grp', 'trusted_host_sg', 'proxy_sg', 'cluster_sg']

# Connect to ec2 client
ec2_client = boto3.client('ec2')
cloudwatch_client = boto3.client('cloudwatch', region_name='us-east-1')

# Delete key pairs by specified names
def delete_key_pairs(key_pair_names):
    try:
        for key_name in key_pair_names:
            print(f"Deleting key pair: {key_name}")
            ec2_client.delete_key_pair(KeyName=key_name)
        print("Key pairs deleted successfully!")
    except Exception as e:
        print(f"Error deleting key pairs: {e}")


# Delete security groups by names
def delete_security_groups(security_group_names, max_retries=5, retry_delay=5):
    try:
        # Retrieve all security groups
        security_groups = ec2_client.describe_security_groups()
        
        # Get the security groups' names and IDs in a dictionary
        sg_map = {sg['GroupName']: sg['GroupId'] for sg in security_groups['SecurityGroups']}
        
        # Iterate over the list of security group names to delete
        for sg_name in security_group_names:
            if sg_name in sg_map:
                sg_id = sg_map[sg_name]
                print(f"Attempting to delete security group: {sg_id} ({sg_name})")
                attempt = 0
                # When deleting security groups:
                # They may still be associated with network interfaces that haven't been deleted yet
                # Retry the deletion process until all dependencies are cleared, allowing the security groups to be deleted successfully
                while attempt < max_retries:
                    try:
                        ec2_client.delete_security_group(GroupId=sg_id)
                        print(f"Deleted security group: {sg_id}")
                        break 
                    except Exception as e:
                        print(f"Error deleting security group {sg_id}: {e}")
                        attempt += 1
                        if attempt < max_retries:
                            print(f"Retrying in {retry_delay} seconds...")
                            time.sleep(retry_delay)
                        else:
                            print(f"Failed to delete security group {sg_id} after {max_retries} attempts.")
            else:
                print(f"Security group name '{sg_name}' not found.")
        
        print("Security group deletion process completed.")
    except Exception as e:
        print(f"Error processing security groups: {e}")

# Terminate running EC2 instances
def terminate_instances():
    try:
        instances = ec2_client.describe_instances(Filters=[{'Name': 'instance-state-name', 'Values': ['running']}])
        for reservation in instances['Reservations']:
            for instance in reservation['Instances']:
                instance_id = instance['InstanceId']
                print(f"Terminating instance: {instance_id}")
                ec2_client.terminate_instances(InstanceIds=[instance_id])
        print("Instances terminated successfully!")
    except Exception as e:
        print(f"Error terminating instances: {e}")

def delete_instance_connect_endpoint():
    """Delete the specified Instance Connect endpoint."""
    # Load environment variables from the .env file
    load_dotenv(override=True)
    endpoint_id = os.getenv('ENDPOINT_ID')
    try:
        response = ec2_client.delete_instance_connect_endpoint(
            InstanceConnectEndpointId=endpoint_id
        )
        print(f'Successfully deleted Instance Connect Endpoint: {endpoint_id}')
        return response
    except Exception as e:
        print(f"Error deleting Instance Connect Endpoint: {e}")
        return None

def delete_nat_gateway(nat_gateway_id):
    print(f"Deleting NAT Gateway with ID: {nat_gateway_id}...")
    ec2_client.delete_nat_gateway(NatGatewayId=nat_gateway_id)
    
    # Wait until the NAT Gateway is fully deleted
    """
    while True:
        nat_gateways = ec2_client.describe_nat_gateways(NatGatewayIds=[nat_gateway_id])
        if not nat_gateways['NatGateways']:
            print("NAT Gateway has been deleted.")
            break
        time.sleep(10)
    """

def delete_route_table(route_table_id):
    print(f"Deleting route table with ID: {route_table_id}...")
    ec2_client.delete_route_table(RouteTableId=route_table_id)
    print("Route table deleted successfully.")

def delete_private_subnet(subnet_id, max_retries=15, delay=10):
    print(f"Attempting to delete subnet with ID: {subnet_id}...")

    for attempt in range(max_retries):
        try:
            # Attempt to delete the subnet
            ec2_client.delete_subnet(SubnetId=subnet_id)
            print("Subnet deleted successfully.")
            return  # Exit the function if successful
        except Exception as e:
            print(f"Error deleting subnet: {e}")
            if "DependencyViolation" in str(e):
                print("Subnet still has dependencies. Retrying...")
                time.sleep(delay)  # Wait before retrying
            else:
                print("Non-recoverable error encountered. Aborting.")
                return

    print("Max retries reached. Could not delete the subnet.")

def delete_network_infra():
    load_dotenv()
    subnet_id = os.getenv('PRIVATE_SUBNET')

    # Get the subnet details to find associated route table and NAT Gateway
    subnet_info = ec2_client.describe_subnets(SubnetIds=[subnet_id])
    
    if not subnet_info['Subnets']:
        print(f"No subnet found with ID: {subnet_id}")
        return
    
    route_table_id = os.getenv('ROUTE_TABLE_ID')
    nat_gateway_id = os.getenv('NAT_GATEWAY')
    
    # Delete NAT Gateway
    if nat_gateway_id:
        delete_nat_gateway(nat_gateway_id)

    # Delete Subnet
    delete_private_subnet(subnet_id)

    # Delete Route Table
    delete_route_table(route_table_id)

def release_all_elastic_ips():
    try:
        # Retrieve all Elastic IP addresses
        response = ec2_client.describe_addresses()
        addresses = response['Addresses']

        # Release each Elastic IP address
        for address in addresses:
            allocation_id = address['AllocationId']
            print(f'Releasing Elastic IP: {address["PublicIp"]} (Allocation ID: {allocation_id})')
            ec2_client.release_address(AllocationId=allocation_id)
        
        print("All Elastic IPs released successfully.")
        
    except Exception as e:
        print("Error releasing Elastic IPs:", e)

def cleanup_aws_resources():
    print("Starting cleanup of AWS resources...")

    # Terminate instances
    terminate_instances()
    
    # Cleanup key pairs
    delete_key_pairs(key_pair_names)

    # cleanup endpoints
    # delete_instance_connect_endpoint()

    delete_network_infra()
    
    # Cleanup security groups
    delete_security_groups(security_group_names, 15, 10)

    release_all_elastic_ips()

    print("AWS resource cleanup completed.")


if __name__ == "__main__":
    # Run cleanup
    cleanup_aws_resources()