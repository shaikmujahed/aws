
import yaml
import time
from lib.device import Device
from lib.aws_client import CloudAws


with open(r'config.yaml') as file:
    config = yaml.load(file, Loader=yaml.FullLoader)

ami_id = config['ami-id']
mgmt_subnet_id = config['mgmt-subnet-id']
sg_id = config['sg-id']
key_pair_name = config['key-pair-name']
instance_type = config['instance-type']

aws_access_key_id = config['secret-key-id']
aws_secret_access_key = config['secret-access-key']
region = config['region']
pkey = config['instance-pkey']

plugin = config.get('vm-series-plugin-version', None)
content_version = config.get('content-version', None)
av_version = config.get('antivirus-version', None)
api_key = config.get('delicensing-api-key', None)
auth_code = config.get('auth-code', None)
sw_version = config['software-version']
version = sw_version.split('vm-')[1]

aws = CloudAws(aws_access_key_id=aws_access_key_id,
               aws_secret_access_key=aws_secret_access_key,
               region_name=region)

instance = aws.create_instance(ami_id, mgmt_subnet_id, sg_id, key_pair_name, instance_type)

instance_id = instance['instance_id']
host = instance['ip']
user = instance['user']

print('*** Waiting for Instance to come up ***')
time.sleep(960)
try:
    pavm = Device(name='pavm', host=host, user=user, ssh_key_file=pkey, os='panos')
except:
    print('Device not ready. Waiting for 5 min and retrying...')
    time.sleep(300)
    pavm = Device(name='pavm', host=host, user=user, ssh_key_file=pkey, os='panos')
print('*** VM-Series Instance is up and running ***')

pavm.license(auth_code)

pavm.verify_system()

if plugin:
    print('*** Checking for Available Plugins ***')
    pavm.exec('request plugins check')

    print(f'*** Downloading {plugin} ***')
    plugin_job = pavm.exec(
        f'request plugins download file {plugin}').job_id()
    pavm.check_job(plugin_job)
    print(f'*** {plugin} Download Complete ***')

    print(f'*** Installing {plugin} ***')
    plugin_job = pavm.exec(
        f'request plugins install {plugin}').job_id()
    pavm.check_job(plugin_job)
    print(f'*** {plugin} Installation Complete ***')


if content_version:
    print('*** Checking for Available Content ***')
    pavm.exec('request content upgrade check')

    print(f'*** Downloading {content_version} ***')
    if content_version.lower() == 'latest':
        content_job = pavm.exec(
            f'request content upgrade download latest').job_id()
    else:
        content_job = pavm.exec(
            f'request content upgrade download file {content_version}').job_id()
    pavm.check_job(content_job)
    print(f'*** {content_version} Download Complete ***')

    print(f'*** Installing {content_version} ***')
    if content_version.lower() == 'latest':
        content_job = pavm.exec(
            f'request content upgrade install version latest').job_id()
    else:
        content_job = pavm.exec(
            f'request content upgrade install file {content_version}.tgz').job_id()
    pavm.check_job(content_job)
    print(f'*** {content_version} Installation Complete ***')

try:
    if av_version:
        print('*** Checking for Available Anti-virus ***')
        pavm.exec('request anti-virus upgrade check')

        print(f'*** Downloading {av_version} ***')
        if av_version.lower == 'latest':
            av_job = pavm.exec(
                f'request anti-virus upgrade download latest').job_id()
        else:
            av_job = pavm.exec(
                f'request anti-virus upgrade download file {av_version}').job_id()
        pavm.check_job(av_job)
        print(f'*** {av_version} Download Complete ***')

        print(f'*** Installing {av_version} ***')
        if av_version.lower == 'latest':
            av_job = pavm.exec(
                f'request anti-virus upgrade install version latest').job_id()
        else:
            av_job = pavm.exec(
                f'request anti-virus upgrade install file {av_version}.tgz').job_id()
        pavm.check_job(av_job)
        print(f'*** {av_version} Installation Complete ***')
except:
    print('*** Unable to upgrade anti-virus; Skipping step *** ')

if sw_version:
    print('*** Checking for Available PANOS Versions ***')
    pavm.exec('request system software check')

    print(f'*** Downloading {sw_version} ***')
    sw_dw_job = pavm.exec(
        f'request system software download file {sw_version}').job_id()
    pavm.check_job(sw_dw_job)
    print(f'*** {sw_version} Download Complete ***')

    print(f'*** Installing {sw_version} ***')
    sw_dw_job = pavm.exec(
        f'request system software install version {version}').job_id()
    pavm.check_job(sw_dw_job)
    print(f'*** {sw_version} Installation Complete ***')
else:
    raise Exception('"software-version" config variable cannot be empty.')


pavm.restart_system()

pavm.verify_versions(sw=version, plugin=plugin, content=content_version, av=av_version)

pavm.delicense(api_key)

pavm.private_data_reset()

pavm.verify_versions(sw=version, plugin=plugin, content=content_version, av=av_version)

pavm.close()

print('*** Stopping Instance ***')
aws.stop_instance(instance_id=instance_id)
print('*** Instance Stopped ***')

print('*** Creating Custom AMI ***')
aws.create_image(instance_id=instance_id, name=f'PanOS-{version}')
print('*** Custom AMI Creation Complete ***')

print('*** Terminating Base Instance ***')
aws.terminate_instance(instance_id=instance_id)
print('*** Termination Complete ***')
