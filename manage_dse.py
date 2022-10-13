import os
import subprocess

import fire


def disable(path_dir='C:/Windows/SysWOW64/5097', client='DSEClient.exe', service='DSEService.exe'):
    path_client = os.path.join(path_dir, client)
    if os.path.exists(path_client):
        os.rename(path_client, path_client + '.bak')
    
    path_service = os.path.join(path_dir, service)
    if os.path.exists(path_service):
        os.rename(path_service, path_service + '.bak')


def enable(path_dir='C:/Windows/SysWOW64/5097', client='DSEClient.exe', service='DSEService.exe'):
    path_client = os.path.join(path_dir, client)
    if os.path.exists(path_client + '.bak'):
        os.rename(path_client + '.bak', path_client)
    
    path_service = os.path.join(path_dir, service)
    if os.path.exists(path_service + '.bak'):
        os.rename(path_service + '.bak', path_service)


def restart():
    subprocess.run(['shutdown', '-r', '-t', '0'])


def operation(task, *args, **kwargs):
    globals()[task](*args, **kwargs)
    restart()


if __name__ == '__main__':
    fire.Fire(operation)
