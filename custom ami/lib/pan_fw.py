
import time
import yaml

from lib.connector import Connection
from lib.device import Response


class PanosDevice(object):
    def __init__(self, **kwargs):
        self._kwargs = kwargs
        self.name = kwargs.get('name')
        self.host = kwargs.get('host')
        self.connected = 0
        try:
            print(f'*** Connecting to device {self.host} ***')
            if 'password' not in kwargs.keys():
                self.handle = Connection(host=self.host, user=kwargs['user'],
                                         ssh_key_file=kwargs['ssh_key_file'])
            else:
                self.handle = Connection(host=self.host, user=kwargs['user'],
                                         password=kwargs['password'])
        except ConnectionError:
            raise Exception("Cannot connect to Device %s" % self.host)
        self.connected = 1
        print("*** Connection successful ***")
        self.prompt = "> "
        self._setup()

    def _setup(self):
        self.exec(command='set cli scripting-mode on')
        self.exec(command='set cli confirmation-prompt off')
        self.exec(command='set cli terminal width 500')
        output = self.exec(command='set cli terminal height 500')
        self.prompt = output.response().rsplit(' ')[0]

    def execute(self, **kwargs):
        if 'pattern' in kwargs.keys():
            pattern = kwargs.pop('pattern')
        else:
            pattern = self.prompt
        kwargs['pattern'] = pattern
        if 'command' not in kwargs:
            raise Exception('"command" is mandatory for Device.execute()')
        kwargs['device'] = self
        kwargs['cmd'] = kwargs.pop('command')
        return self.handle.execute(**kwargs)

    def exec(self, *args, **kwargs):
        if not kwargs and not args:
            raise Exception('Command for device is not specified')
        if not kwargs and args[0]:
            kwargs['command'] = args[0]
            if len(args) > 1 and args[1]:
                kwargs['timeout'] = args[1]

        if 'command' not in kwargs:
            raise Exception('Command for device not specified')
        try:
            patt_match = self.execute(**kwargs)
            if patt_match == -1:
                raise Exception('Timeout seen while retrieving output')
            else:
                return Response(response=self.response, status=True)
        except TimeoutError:
            raise Exception("Timeout seen while retrieving output")

    def restart_system(self):
        try:
            self.exec(command='request restart system', pattern=['NOW!', 'Broadcast message from root'])
        except Exception as e:
            if 'Timeout seen while retrieving output' in str(e):
                print('Device is now rebooting.')
                self.close()
            else:
                raise Exception('Failed to reboot device.')
        print("Waiting for the device to restart...")
        time.sleep(660)
        try:
            self.__init__(**self._kwargs)
        except:
            print('Unable to connect via ssh. Waiting for 2 minutes before retrying.')
            time.sleep(120)
            self.__init__(**self._kwargs)

    def license(self, auth_code):
        if auth_code:
            if auth_code != '':
                print('*** Licensing VM-Series ***')
                self.exec(f'request license fetch auth-code {auth_code}').response()
                time.sleep(5)
                print('*** Waiting for VM-Series to boot up with the new license ***')
                self.restart_system()
                print('*** Licensing is Complete ***')
                time.sleep(10)
        else:
            print('*** No Auth-code provided. Licensing skipped ***')

    def delicense(self, api_key):
        if api_key:
            if api_key != '':
                print('*** Delicensing VM-Series ***')
                self.exec(f'request license api-key set key {api_key}')
                self.exec(f'request license deactivate VM-Capacity mode auto')
        else:
            print('*** No API Key provided. De-licensing skipped ***')
        return

    def private_data_reset(self):
        try:
            self.exec(command='request system private-data-reset', pattern=['NOW!', 'Broadcast message from root'])
        except Exception as e:
            if 'Timeout seen while retrieving output' in str(e):
                print('Device is now rebooting.')
                self.close()
            else:
                raise Exception('Failed to reboot device.')
        print("Waiting for the device to restart...")
        time.sleep(660)
        try:
            self.__init__(**self._kwargs)
        except:
            print('Unable to connect via ssh. Waiting for 2 minutes before retrying.')
            time.sleep(120)
            self.__init__(**self._kwargs)

    def config(self, **kwargs):
        exec_prompt = self.prompt
        self.prompt = self.prompt[:-1] + "#"
        if 'command' not in kwargs:
            raise Exception('Command for device not specified')
        if 'commit' not in kwargs:
            kwargs['commit'] = True
        get_prompt = self.execute(command='configure')
        if get_prompt == -1:
            raise Exception('Unable to switch to configure mode')
        if isinstance(kwargs['command'], str):
            kwargs['command'] = [kwargs['command']]
        for config_cmd in kwargs['command']:
            get_prompt = self.execute(command=config_cmd)
            if get_prompt == -1:
                raise Exception('Unable to execute command in configure mode.')
        if kwargs['commit']:
            get_prompt = self.execute(command='commit')
            if get_prompt == -1 or 'Configuration committed successfully' not in self.response:
                raise Exception('Unable to execute command in configure mode. ERROR: ' + self.response)
        self.prompt = exec_prompt
        get_prompt = self.execute(command='exit')
        if get_prompt == -1:
            raise Exception('Unable to switch to exec mode')

    def verify_system(self):
        try:
            output = yaml.safe_load(self.exec('show system info').response())
        except:
            raise Exception('Unable to fetch system info.')
        if output['vm-license'] == 'none':
            raise Exception('VM-Series Instance is not licensed.')
        if output['serial'] == 'unknown':
            raise Exception('VM-Series Instance does not have a serial.')
        print('*** System Check Passed ***')
        return True

    def verify_versions(self, sw, plugin, content, av):
        try:
            output = yaml.safe_load(self.exec('show system info').response())
        except:
            raise Exception('Unable to fetch system info.')
        if sw not in output['sw-version']:
            raise Exception(f'Upgraded PanOS version {sw} is not installed properly.')
        if plugin:
            if plugin not in output['vm_series']:
                raise Exception(f'Plugin version {plugin} is not installed properly.')
        if content:
            if content != 'latest':
                content_version = content.split('-')[-2] + '-' + content.split('-')[-1]
                if content_version not in output['app-version']:
                    raise Exception(f'Content version {plugin} is not installed properly.')
        if av:
            if content != 'latest':
                av_version = av.split('-')[-2] + '-' + av.split('-')[-1]
                if av_version not in output['av-version']:
                    raise Exception(f'Anti-Virus version {plugin} is not installed properly.')
        print('*** Version Check Passed ***')
        return True

    def check_job(self, job_id):
        output = self.exec(f'show jobs id {job_id}').response()
        if 'not found' in output:
            raise Exception(f'Job with job id {job_id} not created.')
        time.sleep(10)
        retry = 25
        interval = 30
        while retry >= 0:
            output = self.exec(f'show jobs id {job_id}').response()
            if 'FIN' in output:
                print(f'*** Job {job_id} complete. ***')
                time.sleep(10)
                return True
            elif 'PEND' in output:
                print(f'Job {job_id} is incomplete. Waiting for {str(interval)} seconds before retrying.')
                time.sleep(interval)
            else:
                break
        raise Exception(f'Unable to complete job with job id {job_id}')

    def close(self):
        try:
            self.handle.client.close()
            self.connected = 0
        except ConnectionAbortedError:
            raise Exception("Unable to close Device handle")
        return True
