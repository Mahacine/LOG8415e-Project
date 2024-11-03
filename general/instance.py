import boto3
import botocore.exceptions
import time

# Connect to ec2 resource and client
ec2_resource = boto3.resource('ec2', region_name='us-east-1')
ec2_client = boto3.client('ec2', region_name='us-east-1')


def create_key_pair(key_name):

    # Create the key pair et get the key material
    key_pair = ec2_resource.create_key_pair(KeyName=key_name)
    key_material = key_pair.key_material

    # Write the key material to file
    file_path = f"./general/{key_name}.pem"
    with open(file_path, 'w') as file:
        file.write(key_material)

    return key_pair


def get_default_vpc_id():

    # Filter for the default VPC
    response = ec2_client.describe_vpcs(
        Filters=[
            {
                'Name': 'isDefault',
                'Values': ['true']
            }
        ]
    )

    # Check if any default VPCs are found
    if 'Vpcs' in response and len(response['Vpcs']) > 0:
        default_vpc = response['Vpcs'][0]
        vpc_id = default_vpc['VpcId']
        return vpc_id

# Get subnets of a specific vpc
def get_subnets_ids(vpc_id):
    subnets = ec2_client.describe_subnets(
        Filters=[
            {
                'Name': 'vpc-id', 
                'Values': [vpc_id]
            }
        ]
    )
    subnet_ids = [subnet['SubnetId'] for subnet in subnets['Subnets']]

    return subnet_ids

# Get subnets of a specific vpc
def get_subnets(vpc_id):
    subnets = ec2_client.describe_subnets(
        Filters=[
            {
                'Name': 'vpc-id', 
                'Values': [vpc_id]
            }
        ]
    )
    return [subnet for subnet in subnets['Subnets']]

def has_private_subnet(subnets):
    return any(not subnet.get('MapPublicIpOnLaunch', True) for subnet in subnets)

def convert_subnet_to_private():
    default_vpc_id = get_default_vpc_id()
    
    if default_vpc_id is None:
        print("No default VPC found.")
        return
    
    subnets = get_subnets(default_vpc_id)
    
    if has_private_subnet(subnets):
        print("A private subnet already exists in the default VPC.")
        return

    # Modify the subnet to disable public IP assignment
    try:
        response = ec2_client.modify_subnet_attribute(
            SubnetId=get_subnets_ids(default_vpc_id)[0],
            MapPublicIpOnLaunch={
                'Value': False
            }
        )
        print(f'Subnet {subnet_id} has been successfully converted to a private subnet.')
    except Exception as e:
        print(f'Error converting subnet: {e}')

# Implement security group
def create_security_group(description, name, vpc_id):

    security_group = ec2_client.create_security_group(
        Description=description,
        GroupName=name,
        VpcId=vpc_id
    )

    # Authorize inbound traffic
    ec2_client.authorize_security_group_ingress(
        GroupId=security_group['GroupId'],
        IpPermissions=[
            {
                "FromPort": 22, #SSH
                "ToPort": 22,
                "IpProtocol": "tcp",
                "IpRanges": [{"CidrIp": "0.0.0.0/0"}],
            },
            {
                "FromPort": 80, #HTTP
                "ToPort": 80,
                "IpProtocol": "tcp",
                "IpRanges": [{"CidrIp": "0.0.0.0/0"}],
            },
            {
                "FromPort": 8000, 
                "ToPort": 8000,
                "IpProtocol": "tcp",
                "IpRanges": [{"CidrIp": "0.0.0.0/0"}],
            },
            {
                "FromPort": 443, #HTTPs
                "ToPort": 443,
                "IpProtocol": "tcp",
                "IpRanges": [{"CidrIp": "0.0.0.0/0"}],
            },
            {
                "FromPort": 9000,  # Custom port
                "ToPort": 9000,
                "IpProtocol": "tcp",
                "IpRanges": [{"CidrIp": "0.0.0.0/0"}],
            },
            {
                "FromPort": 50070,  # Custom port
                "ToPort": 50070,
                "IpProtocol": "tcp",
                "IpRanges": [{"CidrIp": "0.0.0.0/0"}],
            },
            {
                "FromPort": 50075,  # Custom port
                "ToPort": 50075,
                "IpProtocol": "tcp",
                "IpRanges": [{"CidrIp": "0.0.0.0/0"}],
            },
            {
                "FromPort": 50090,  # Custom port
                "ToPort": 50090,
                "IpProtocol": "tcp",
                "IpRanges": [{"CidrIp": "0.0.0.0/0"}],
            },
            {
                "FromPort": 8888,  # Custom port
                "ToPort": 8888,
                "IpProtocol": "tcp",
                "IpRanges": [{"CidrIp": "0.0.0.0/0"}],
            },
            {
                "FromPort": 8020,  # Custom port
                "ToPort": 8020,
                "IpProtocol": "tcp",
                "IpRanges": [{"CidrIp": "0.0.0.0/0"}],
            },
            {
                "FromPort": 9870,  # Custom port
                "ToPort": 9870,
                "IpProtocol": "tcp",
                "IpRanges": [{"CidrIp": "0.0.0.0/0"}],
            },
            {
                "FromPort": 8088,  # Custom port
                "ToPort": 8088,
                "IpProtocol": "tcp",
                "IpRanges": [{"CidrIp": "0.0.0.0/0"}],
            },
            {
                "FromPort": 54311,  # Custom port
                "ToPort": 54311,
                "IpProtocol": "tcp",
                "IpRanges": [{"CidrIp": "0.0.0.0/0"}],
            },
        ],
    )
    
    # Outbound traffic is defined in the default rule available upon creation

    return security_group

def create_instance_connect_endpoint(security_group_id):
    default_vpc_id =  get_default_vpc_id()
    # Get the subnets for the default VPC
    subnets = get_subnets(default_vpc_id)
    private_subnet_id = next((subnet['SubnetId'] for subnet in subnets if not subnet['MapPublicIpOnLaunch']),None)
    try:
        # Create the Instance Connect endpoint
        response = ec2_client.create_instance_connect_endpoint(
            SubnetId=private_subnet_id,
            SecurityGroupIds=[security_group_id],
            PreserveClientIp=False,  # Set to True if you need to preserve client IP
            ClientToken='lab-client-token',
            TagSpecifications=[{
                'ResourceType': 'instance-connect-endpoint',
                'Tags': [
                    {
                        'Key': 'Name',
                        'Value': 'MyInstanceConnectEndpoint'
                    },
                ]
            }]
        )

        endpoint_id = response['InstanceConnectEndpoint']['InstanceConnectEndpointId']
        print(f'Created Instance Connect Endpoint: {endpoint_id}')
        return endpoint_id

    except Exception as e:
        print(f"Error creating Instance Connect Endpoint: {e}")
        return None

# Get availability zones names for the current client
def get_availability_zones():
    try:
        # Describe availability zones
        response = ec2_client.describe_availability_zones()
        azs = [az['ZoneName'] for az in response['AvailabilityZones']]
        return azs
    except botocore.exceptions.ClientError as e:
        print(f"An error occurred: {e}")
        return None

# Function to get ubuntu image ID   
def find_ami(image_name):
    try:
        response = ec2_client.describe_images(
            Filters=[
                {
                    'Name': 'name',
                    'Values': [image_name]
                },
                {
                    'Name': 'architecture',
                    'Values': ['x86_64']
                },
                {   'Name': 'root-device-type',
                    'Values': ['ebs']
                }
            ]
        )
        images = response['Images']
        if images:
            return images[1]['ImageId']
        else:
            print("No AMIs found.")
            return None

    except Exception as e:
        print(f"An error occurred: {e}")

def create_ec2_instance(instance_type, key_name, security_group_id, image_id, user_data, availability_zone, vpc_id, is_public):

    default_vpc_id =  get_default_vpc_id()
    # Get the subnets for the default VPC
    subnets = get_subnets(default_vpc_id)
    
    if is_public == False:
        private_subnet_id = next((subnet['SubnetId'] for subnet in subnets if not subnet['MapPublicIpOnLaunch']),None)
        # Create the EC2 instance
        response = ec2_resource.create_instances(
            MinCount = 1,
            MaxCount = 1,
            ImageId = image_id,
            InstanceType = instance_type,
            KeyName = key_name,
            SecurityGroupIds=[security_group_id,],
            UserData=user_data,
            # Placement={
            #     'AvailabilityZone': availability_zone
            # },
            SubnetId=private_subnet_id
        )
    else:
        public_subnet_id = next((subnet['SubnetId'] for subnet in subnets if subnet['MapPublicIpOnLaunch']),None)
        # Create the EC2 instance
        response = ec2_resource.create_instances(
            MinCount = 1,
            MaxCount = 1,
            ImageId = image_id,
            InstanceType = instance_type,
            KeyName = key_name,
            SecurityGroupIds=[security_group_id,],
            UserData=user_data,
            #Placement={
            #    'AvailabilityZone': availability_zone
            #}
            SubnetId=public_subnet_id
        )
    
    instance = response[0]

    # Wait until instance enters the running state
    instance.wait_until_running()

    # Load updated attributes to populate public_ip_address
    instance.reload()

    # enable detailed monitoring
    # ec2_client.monitor_instances(InstanceIds=[instance.instance_id])

    return instance

def create_private_subnet(cidr_block):
    default_vpc_id =  get_default_vpc_id()

    # Create the private subnet
    print(f"Creating a private subnet in VPC {default_vpc_id} with CIDR block {cidr_block}...")
    subnet_response = ec2_client.create_subnet(
        VpcId=default_vpc_id,
        CidrBlock=cidr_block,
        AvailabilityZone='us-east-1a'  # You can specify a different AZ if needed
    )
    
    subnet_id = subnet_response['Subnet']['SubnetId']
    print(f"Private subnet created with ID: {subnet_id}")

    return subnet_id

def create_route_table():
    default_vpc_id =  get_default_vpc_id()
    # Create a new route table for the private subnet
    print("Creating a new route table...")
    route_table_response = ec2_client.create_route_table(VpcId=default_vpc_id)
    route_table_id = route_table_response['RouteTable']['RouteTableId']
    print(f"New route table created with ID: {route_table_id}")

    return route_table_id

def associate_route_table(route_table_id, subnet_id):

    # Associate the new route table with the private subnet
    print(f"Associating route table {route_table_id} with subnet {subnet_id}...")
    ec2_client.associate_route_table(RouteTableId=route_table_id, SubnetId=subnet_id)
    print("Route table associated successfully.")

def create_nat_gateway():

    default_vpc_id =  get_default_vpc_id()
    # Get the subnets for the default VPC
    subnets = get_subnets(default_vpc_id)
    public_subnet_id = next((subnet['SubnetId'] for subnet in subnets if subnet['MapPublicIpOnLaunch']),None)

    # Create the NAT Gateway
    print("Creating NAT Gateway...")
    nat_gateway_response = ec2_client.create_nat_gateway(
        SubnetId=public_subnet_id,
        AllocationId=allocate_eip(ec2_client)  # Allocate an Elastic IP for the NAT Gateway
    )
    
    nat_gateway_id = nat_gateway_response['NatGateway']['NatGatewayId']
    print(f"NAT Gateway created with ID: {nat_gateway_id}")

    # Wait until the NAT Gateway is available
    wait_for_nat_gateway(ec2_client, nat_gateway_id)

    return nat_gateway_id

def allocate_eip(ec2):
    print("Allocating Elastic IP...")
    eip_response = ec2.allocate_address(Domain='vpc')
    allocation_id = eip_response['AllocationId']
    print(f"Elastic IP allocated with Allocation ID: {allocation_id}")
    return allocation_id

def wait_for_nat_gateway(ec2, nat_gateway_id):
    print("Waiting for NAT Gateway to become available...")
    while True:
        nat_gateway = ec2.describe_nat_gateways(NatGatewayIds=[nat_gateway_id])
        status = nat_gateway['NatGateways'][0]['State']
        if status == 'available':
            print("NAT Gateway is available.")
            break
        time.sleep(10)  # Wait for 10 seconds before checking again

def update_route_table(nat_gateway_id):
    default_vpc_id =  get_default_vpc_id()
    # Get the subnets for the default VPC
    subnets = get_subnets(default_vpc_id)
    private_subnet_id = next((subnet['SubnetId'] for subnet in subnets if not subnet['MapPublicIpOnLaunch']),None)

    # Get the route table associated with the private subnet
    route_tables = ec2_client.describe_route_tables(Filters=[{'Name': 'association.subnet-id', 'Values': [private_subnet_id]}])
    route_table_id = route_tables['RouteTables'][0]['RouteTableId']

    # Update the route table to route internet-bound traffic through the NAT Gateway
    print(f"Updating route table {route_table_id} for private subnet {private_subnet_id}...")
    ec2_client.create_route(
        RouteTableId=route_table_id,
        DestinationCidrBlock='0.0.0.0/0',
        NatGatewayId=nat_gateway_id
    )
    print("Route table updated successfully.")