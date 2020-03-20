
class Device(object):
    def __new__(cls, **kwargs):
        name = kwargs.get('name', 'Unnamed Device')
        host = kwargs.get('host', None)
        user = kwargs.get('user', None)
        password = kwargs.get('password', None)
        ssh_key_file = kwargs.get('ssh_key_file', None)
        port = kwargs.get('port', None)
        os = kwargs.get('os', 'panos')
        if ssh_key_file is not None:
            password = None
        if user is None:
            raise Exception("'user' parameter is mandatory for Device()")
        if host is None:
            raise Exception("'host' parameter is mandatory for Device()")
        if os is None:
            raise Exception("'os' parameter is mandatory for Device(). os='panos', os='linux'")
        if password is None and ssh_key_file is None:
            raise Exception("Either 'password' or 'ssh_key_file' needs to be provided for Device()")
        if port is None:
            port = 22
        if password is not None:
            new_kwargs = {'name': name, 'host': host, 'user': user, 'port': port, 'password': password}
        else:
            new_kwargs = {'name': name, 'host': host, 'user': user, 'port': port, 'ssh_key_file': ssh_key_file}

        if os.upper() == 'PANOS':
            from lib.pan_fw import PanosDevice
            return PanosDevice(**new_kwargs)
        else:
            raise Exception('OS type not supported.')


class Response(object):
    def __init__(self, **kwargs):
        self.resp = kwargs.get('response')
        self.stat = kwargs.get('status')

    def response(self):
        return self.resp

    def status(self):
        return self.stat

    def job_id(self):
        return self.resp.split('\n')[-2].replace('\r', '')

    def __bool__(self):
        return self.stat

    def __nonzero__(self):
        return self.__bool__()
