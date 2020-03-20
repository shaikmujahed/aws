
import sys
import paramiko
import re
from select import select
import time


class Connection(paramiko.client.SSHClient):

    def __init__(self, **kwargs):
        host = kwargs.get('host')
        user = kwargs.get('user')
        password = kwargs.get('password', None)
        ssh_key_file = kwargs.get('ssh_key_file', None)
        if password is None and ssh_key_file is None:
            raise Exception("Either password or an ssh_key needs to be provided to log into " + host)
        port = kwargs.get('port', None)
        try:
            super(Connection, self).__init__()
            self.set_missing_host_key_policy(paramiko.AutoAddPolicy())
            if port is None:
                if ssh_key_file is None:
                    self.connect(hostname=host, username=user, password=password)
                else:
                    self.connect(hostname=host, username=user, key_filename=ssh_key_file)
            else:
                if ssh_key_file is None:
                    self.connect(hostname=host, username=user, password=password, port=port)
                else:
                    self.connect(hostname=host, username=user, port=port, key_filename=ssh_key_file)
            tnh = self.invoke_shell(width=160)
            self.client = tnh
            got = []
            while True:
                rd, wr, err = select([tnh], [], [], 10)
                if rd:
                    data = tnh.recv(32767)
                    try:
                        data = data.decode('utf-8')
                    except UnicodeDecodeError:
                        data = data.decode('iso-8859-1')
                    got.append(data)
                    if re.search(r'{0}\s?$'.format(r'(\$|>|#|%)'), data):
                        break
        except Exception as error:
            raise Exception("Cannot create a SSH connection to Device %s: %s: username=%s" % (host, error, user))

    def execute(self, **kwargs):
        cmd = kwargs.get('cmd')
        pattern = kwargs.get('pattern')
        device = kwargs['device']
        timeout = kwargs.get('timeout', 100)
        if timeout < 100:
            timeout = 100
        raw_output = kwargs.get('raw_output', False)
        if isinstance(pattern, str):
            pattern = [pattern]
        pattern_new = ''
        for pat in pattern:
            pattern_new = pattern_new + pat + ","
        pattern_new = pattern_new[:-1]
        tnh = self.client
        cmd_send = cmd + '\n'
        if not hasattr(device, 'shelltype'):
            device.shelltype = 'sh'
        cmd_re = cmd + '\s?\r{1,2}\n'
        cmd_re = re.sub('\$', '\\$', cmd_re)
        cmd_re = re.sub('\|', '\\|', cmd_re)
        cmd_re = re.sub('-', '\-', cmd_re)
        print("Command: " + cmd_send)
        tnh.send(cmd_send)
        match = -1
        if 'no_response' in kwargs and kwargs['no_response']:
            device.response = ''
            match = 1
        else:
            (output, resp) = self.read_until(expected=pattern,
                                             shell=device.shelltype,
                                             timeout=timeout)
            response = ''
            while '--(more)--' in resp:
                response += re.sub('\n--\(more\)--', '', resp, 1)
                tnh.send('\r\n')
                (output, resp) = self.read_until(expected=pattern,
                                                 shell=device.shelltype,
                                                 timeout=timeout)
            response += resp
            if not raw_output:
                response = re.sub(cmd_re, '', response)
            if not output:
                print("Sent '%s' to %s, expected '%s', "
                      "but got:\n'%s'" % (cmd, device.host,
                                          pattern_new,
                                          response))
                match = -1
            else:
                for pat in pattern:
                    match += 1
                    if re.search(pat, response):
                        break
            if not raw_output:
                for pat in pattern:
                    response = re.sub('\n.*' + pat, '', response)
                response = re.sub('\r\n$', '', response)
            device.response = response
            print("Output: \n" + response + "\n")
        return match

    def read_until(self, expected='\s\$', timeout=60, shell='sh'):
        time.sleep(0.5)
        timeout -= 2
        tnh = self.client
        time_int = 10
        time_out = 0
        got = ''
        timeout_occ = 0
        if isinstance(expected, list):
            if shell == 'csh':
                for i, j in enumerate(expected):
                    expected[i] = re.sub('\s$', '(\s|\t)', expected[i])
            expected = '|'.join(expected)
        while True:
            start_time = time.time()
            rd, wr, err = select([tnh], [], [], time_int)
            if rd:
                data = tnh.recv(4096)
                try:
                    data = data.decode('utf-8')
                except UnicodeDecodeError:
                    data = data.decode('iso-8859-1')
                got = got + data
            end_time = time.time()
            sys.stdout.flush()
            if re.search(r'{0}\s?$'.format(expected), got):
                break
            time_out += (end_time - start_time)
            if int(time_out) > timeout:
                timeout_occ = 1
                break
        if timeout_occ:
            return False, got
        return True, got
