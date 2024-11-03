import boto3

# Initialize the EC2 client
ec2 = boto3.resource('ec2')

# Create a VPC
vpc = ec2.create_vpc(CidrBlock='10.0.0.0/16')
vpc.wait_until_available()
print(f"Created VPC: {vpc.id}")

# Create an Internet Gateway and attach it to the VPC
igw = ec2.create_internet_gateway()
vpc.attach_internet_gateway(InternetGatewayId=igw.id)
print(f"Created and attached Internet Gateway: {igw.id}")

# Create subnets
public_subnet = ec2.create_subnet(VpcId=vpc.id, CidrBlock='10.0.1.0/24')
private_subnet1 = ec2.create_subnet(VpcId=vpc.id, CidrBlock='10.0.2.0/24')  # Trusted Host
private_subnet2 = ec2.create_subnet(VpcId=vpc.id, CidrBlock='10.0.3.0/24')  # Proxy
private_subnet3 = ec2.create_subnet(VpcId=vpc.id, CidrBlock='10.0.4.0/24')  # Cluster
print(f"Created Public Subnet: {public_subnet.id}, Trusted Host Subnet: {private_subnet1.id}, Proxy Subnet: {private_subnet2.id}, Cluster Subnet: {private_subnet3.id}")

# Create a route table for the public subnet
route_table = ec2.create_route_table(VpcId=vpc.id)
route_table.create_route(DestinationCidrBlock='0.0.0.0/0', GatewayId=igw.id)
route_table.associate_with_subnet(SubnetId=public_subnet.id)

# Create Security Groups
public_sg = ec2.create_security_group(GroupName='PublicSG', Description='Public Security Group', VpcId=vpc.id)
public_sg.authorize_ingress(IpProtocol='tcp', FromPort=22, ToPort=22, CidrIp='0.0.0.0/0')  # Allow SSH from anywhere

private_sg = ec2.create_security_group(GroupName='PrivateSG', Description='Private Security Group', VpcId=vpc.id)
private_sg.authorize_ingress(IpProtocol='tcp', FromPort=22, ToPort=22, SourceGroupId=public_sg.id)  # Allow SSH from Gatekeeper

# Proxy Security Group
proxy_sg = ec2.create_security_group(GroupName='ProxySG', Description='Proxy Security Group', VpcId=vpc.id)
proxy_sg.authorize_ingress(IpProtocol='tcp', FromPort=22, ToPort=22, SourceGroupId=private_sg.id)  # Allow SSH from Trusted Host

# Cluster Security Group
cluster_sg = ec2.create_security_group(GroupName='ClusterSG', Description='Cluster Security Group', VpcId=vpc.id)
cluster_sg.authorize_ingress(IpProtocol='tcp', FromPort=22, ToPort=22, SourceGroupId=proxy_sg.id)  # Allow SSH from Proxy

# Launch the EC2 instances
gatekeeper_instance = ec2.create_instances(
    ImageId='ami-0abcdef1234567890',  # Replace with your AMI ID
    InstanceType='t2.micro',
    MinCount=1,
    MaxCount=1,
    KeyName='your-key-pair',  # Replace with your key pair
    SubnetId=public_subnet.id,
    SecurityGroupIds=[public_sg.id]
)[0]

trusted_host_instance = ec2.create_instances(
    ImageId='ami-0abcdef1234567890',  # Replace with your AMI ID
    InstanceType='t2.micro',
    MinCount=1,
    MaxCount=1,
    KeyName='your-key-pair',
    SubnetId=private_subnet1.id,
    SecurityGroupIds=[private_sg.id]
)[0]

proxy_instance = ec2.create_instances(
    ImageId='ami-0abcdef1234567890',  # Replace with your AMI ID
    InstanceType='t2.micro',
    MinCount=1,
    MaxCount=1,
    KeyName='your-key-pair',
    SubnetId=private_subnet2.id,
    SecurityGroupIds=[proxy_sg.id]
)[0]

# Launch cluster instances
cluster_instances = ec2.create_instances(
    ImageId='ami-0abcdef1234567890',  # Replace with your AMI ID
    InstanceType='t2.micro',
    MinCount=3,
    MaxCount=3,
    KeyName='your-key-pair',
    SubnetId=private_subnet3.id,
    SecurityGroupIds=[cluster_sg.id]
)

print(f"Launched Gatekeeper: {gatekeeper_instance.id}")
print(f"Launched Trusted Host: {trusted_host_instance.id}")
print(f"Launched Proxy: {proxy_instance.id}")
for instance in cluster_instances:
    print(f"Launched Cluster Instance: {instance.id}")

# Wait until the instances are running
gatekeeper_instance.wait_until_running()
trusted_host_instance.wait_until_running()
proxy_instance.wait_until_running()
for instance in cluster_instances:
    instance.wait_until_running()

# Output the public IP of the Gatekeeper
gatekeeper_instance.reload()
print(f"Gatekeeper Public IP: {gatekeeper_instance.public_ip_address}")