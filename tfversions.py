import subprocess as sp
import json

v = sp.check_output(['conda', 'info', '--json', 'tensorflow-base'])
v = json.loads(v)
v = v['tensorflow-base']

def is_gpu(pkg):
    for dep in pkg['depends']:
        if dep.startswith('cudatoolkit'):
            return True
    return False

def is_revoked(pkg):
    for dep in pkg['depends']:
        if dep == 'package_has_been_revoked':
            return True
    return False

for pkg in v:
    if is_revoked(pkg) or not is_gpu(pkg):
        continue

    print(pkg['version'], end=' ')
    for dep in pkg['depends']:
        if dep.startswith('python') or dep.startswith('cudatoolkit'):
            print(dep, end=' ')
    print()
