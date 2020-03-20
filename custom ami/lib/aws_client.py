
import os
import time

import boto3


class CloudAws(object):
    def __init__(self, aws_access_key_id, aws_secret_access_key, region_name):
        self.name = 'aws'
        self.region = region_name
        print('Connecting to AWS...')
        try:
            self.client = boto3.client(
                'ec2',
                aws_access_key_id=aws_access_key_id,
                aws_secret_access_key=aws_secret_access_key,
                region_name=region_name)
            self.resource = boto3.resource(
                'ec2',
                aws_access_key_id=aws_access_key_id,
                aws_secret_access_key=aws_secret_access_key,
                region_name=region_name)
            self.id = os.getpid()
            print('Connection Successful.')
        except Exception as e:
            print(f'Unable to connect to AWS: {str(e)}')

    def _get_public_ip(self, instance_id):
        response = self.client.describe_instances(InstanceIds=[instance_id])
        public_ip = response['Reservations'][0]['Instances'][0]['PublicIpAddress']
        return public_ip

    def create_instance(self, ami_id, mgmt_subnet_id, sg_id, key_pair_name, instance_type='m4.xlarge'):
        waiter = self.client.get_waiter('instance_running')
        print(f'*** Creating Instance ***')
        try:
            instance_request = self.resource.create_instances(
                ImageId=ami_id,
                MinCount=1,
                MaxCount=1,
                KeyName=key_pair_name,
                InstanceType=instance_type,
                NetworkInterfaces=[
                    {
                        'DeviceIndex': 0,
                        'AssociatePublicIpAddress': True,
                        'SubnetId': mgmt_subnet_id,
                        'Groups': [sg_id, ],
                    }
                ]
            )
            time.sleep(30)
            instance_id = instance_request[0].id
            waiter.wait(InstanceIds=[instance_id])
            print('*** Instance Creation Successful ***')
            self.resource.create_tags(Resources=[instance_id], Tags=[{
                'Key': 'Name', 'Value': f'CI_Generator_{self.id}'}
            ])
        except Exception as e:
            print(f'ERROR: Unable to deploy the instance: {str(e)}')
        public_ip = self._get_public_ip(instance_id)
        return {'instance_id': instance_id, 'ip': public_ip, 'user': 'admin'}

    def terminate_instance(self, instance_id):
        waiter = self.client.get_waiter('instance_terminated')
        self.client.terminate_instances(InstanceIds=[instance_id])
        print('Waiting for completion...')
        time.sleep(20)
        try:
            waiter.wait(InstanceIds=[instance_id])
        except BaseException:
            print('Unable to terminate instance.')
        return

    def stop_instance(self, instance_id):
        waiter = self.client.get_waiter('instance_stopped')
        stop_request = self.client.stop_instances(InstanceIds=[instance_id])
        print(f'Stopping instance {instance_id} ...')
        try:
            waiter.wait(InstanceIds=[instance_id])
            stop_result = True
            print('Instance stopped.')
        except BaseException:
            stop_result = False
            print('Unable to stop instance.')
        return stop_result

    def create_image(self, instance_id, name):
        waiter = self.client.get_waiter('image_available')
        create_request = self.client.create_image(InstanceId=instance_id,
                                                  NoReboot=False,
                                                  Name=f'{name}-{self.id}',
                                                  Description='Custom Image created by Palo Alto Networks')
        ami_id = create_request["ImageId"]
        print(f'Waiting for the custom AMI {ami_id} to be available.')
        try:
            waiter.wait(ImageIds=[ami_id])
            result = True
            print(f'Custom AMI: {ami_id} has been created in region: {self.region}.')
        except BaseException:
            print('Unable to check availability of the new AMI.')
            result = False
        return result
