#!/usr/bin/python
#title           :deregister-ami.py
#description     :This will deregister ami's that are past the retention period
#author          :G Ho
#date            :20170801
#version         :0.1
#usage           :python deregister-ami.py --env <first 10 character so of instance> 
#notes           :
#python_version  :2.7
#==============================================================================
import boto3
import datetime

ec2 = boto3.client('ec2')

today=datetime.datetime.now().strftime("%s")

def lambda_handler(event, context):
	
	ami_response = ec2.describe_images(Filters=[{'Name': 'tag:expireDate', 'Values': ['*']}])
	##print ami_response

	for ami in ami_response['Images']:
		for tag in ami['Tags']:
			if tag['Key'] == 'expireDate':
				expireDate=tag['Value']
				if expireDate <= today:
						ami_id=ami['ImageId']
						print ("Deleting "+ami_id+".....")
						deregister_response= ec2.deregister_image(ImageId=ami_id)
						
				else:
						print (ami['ImageId']+" is still valid")

						break



lambda_handler(1,1)
