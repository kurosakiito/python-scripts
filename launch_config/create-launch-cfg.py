#!/usr/bin/python

import boto3
import sys
ec2 = boto3.client('ec2')
asg = boto3.client('autoscaling')
instance_name="CGEBSD01A1"
instance_name=instance_name+"*"

def lambda_handler(event, context):

	ami_response = ec2.describe_images(Filters=[{'Name': 'tag:Name', 'Values': [instance_name]},{'Name': 'state', 'Values': ['available']}])
	ec2_response = ec2.describe_instances(Filters=[{'Name': 'tag:Name', 'Values': [instance_name]}])
	
	sg_list=[]
	for reservation in ec2_response['Reservations']:
		for instance in reservation['Instances']:
			instance_type = instance['InstanceType']
			for mon in instance['Monitoring']:
				instance_monitoring = mon['State']
				print instance_monitoring
				if instance_monitoring == 'disabled':
					instance_monitoring = 'false'
				elif instance_monitoring == 'enabled':
					instance_monitoring = 'true'
				else:	
					print ("Monitoring setting is still in progress")
					sys.exit(2)
				break
			for sg in instance['SecurityGroups']:
				sg_id = sg['GroupId']
				print sg_id
				sg_list.append(sg_id)

	list_of_ami = []
	for ami in ami_response['Images']:
		for tag in ami['Tags']:
			if tag['Key'] == 'Name':
				ami_name=tag['Value']
				ami_name=ami_name[:-19]
				list_of_ami.append({'date':ami['CreationDate'], 'ami_id': ami['ImageId']}) 
	try:
		newlist = sorted(list_of_ami, key=lambda k: k['date'], reverse=True)
		latest_ami_id=(newlist)[0]['ami_id']
		print ("Latest AMI: " + latest_ami_id)
	except IndexError:
		newlist = 'null'
		print "No AMI found"
		sys.exit(2)
	
	launch_response = asg.create_launch_configuration(LaunchConfigurationName=ami_name,
ImageId=latest_ami_id,
InstanceType=instance_type,
SecurityGroups=sg_list,
InstanceMonitoring={'Enabled': instance_monitoring})

	print "Launch configuration created for AMI " + latest_ami_id
lambda_handler(1,1)	
