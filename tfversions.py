import subprocess as sp
import json

def is_gpu(pkg):
    return any(dep.startswith('cudatoolkit') for dep in pkg['depends'])

def is_revoked(pkg):
    return any(dep == 'package_has_been_revoked' for dep in pkg['depends'])

v = sp.check_output(['conda', 'info', '--json', 'tensorflow-base'])
v = json.loads(v)
v = v['tensorflow-base']

for pkg in v:
    if is_revoked(pkg) or not is_gpu(pkg):
        continue

    print(pkg['version'], end='\t')
    for dep in pkg['depends']:
        if dep.startswith('python') or dep.startswith('cudatoolkit'):
            print(dep, end='\t')
    print()
