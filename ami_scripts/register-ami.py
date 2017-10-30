#!/usr/bin/python
#title           :register-ami.py
#description     :Creates an AMI from the latest snapshot of the environment specified 
#author          :G Ho
#date            :20170801	
#version         :0.1
#usage           :python register-ami.py --env "first 10 characters of instance"
#notes           :
#python_version  :2.7
#==============================================================================


import boto3
from botocore.exceptions import ClientError
import datetime
import getopt
import sys
import time

ec2 = boto3.client('ec2')

expire_days=30
today=datetime.datetime.now().strftime("%Y%m%d%H%M%S")
now = datetime.datetime.now()
expire_date = now + datetime.timedelta(expire_days)
epoc = expire_date.strftime("%s")

def lambda_handler(event, context):
        opts, args = getopt.getopt(sys.argv[1:],"e",["env="])
	for o, a in opts:
		if o in ("-e", "--env") and len(a) > 9:
			instance_name = a+"*"
			#print instance_name
			break			
		elif len(a) < 10:
			print "Minimum of 10 characters needed to identify instance"
			sys.exit(2)
        else:
		print 'Usage: create-ami-lambda.py --env <instance_name>'
		sys.exit(2)

	snapshot_response = ec2.describe_snapshots(Filters=[{'Name': 'tag:Name', 'Values': [instance_name]},{'Name': 'status','Values': ['completed']}])

	## Loops through the list of snaps for the specified instance
        list_of_snaps = []
        for snapshot in snapshot_response['Snapshots']:
                for tag in snapshot['Tags']:
                        if tag['Key'] == 'Name':
                                snap_name=tag['Value']
                                #print tag['Value']
                                #print snapshot['SnapshotId']
                                #print snapshot['StartTime']
                                list_of_snaps.append({'date':snapshot['StartTime'], 'snap_id': snapshot['SnapshotId'], 'l_snap': tag['Value']})
			        break  
	try:
		newlist = sorted(list_of_snaps, key=lambda k: k['date'], reverse=True)
		latest_snap_id=(newlist)[0]['snap_id']
		latest_snap_name=(newlist)[0]['l_snap']
	except IndexError:
		newlist = 'null'
		print "No snapshot found"
		sys.exit(2)        

	#print latest_snap_id
        print "Now trying to create AMI from: "+latest_snap_name
	print "Checking if ami exists from " + latest_snap_name

	## Checking if an AMI has been created from the snapshot already.
	ami_response = ec2.describe_images(Filters=[{'Name': 'tag:Name', 'Values':[latest_snap_name+"*"]}])	
	for ami in ami_response['Images']:
		if ami['Name'] is not None:
			print "AMI from from snapshot "+latest_snap_name+" already exists, exiting...."
			sys.exit(2)

	##Configuration for the AMI	 
        ami_name=latest_snap_name+"_"+today+"_AMI"
        BlockDeviceMapping = [{'DeviceName': '/dev/xvda','Ebs': {'SnapshotId': latest_snap_id}}]
        response_register = ec2.register_image(Name=ami_name,Description="Test",RootDeviceName='/dev/xvda',BlockDeviceMappings=BlockDeviceMapping,DryRun=False)	
	ami_id = response_register['ImageId']
	waiter = ec2.get_waiter('image_available')
	waiter.wait(ImageIds=[ami_id])
	
	##Adding tags to newly created ami
	response_tag = ec2.create_tags(Resources=[ami_id], Tags=[{'Key':'expireDate', 'Value':epoc},{'Key':'Name', 'Value':ami_name}],)
	
	print "AMI creation successfully completed"
		 
lambda_handler(1,1)
