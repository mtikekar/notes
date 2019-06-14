# Running PyTorch on RHEL6

**The problem**: PyTorch requires glibc >= 2.17 while RHEL6 has 2.12

**The solution**: Download packages for glibc 2.17 and patch the `python` executable to use the new ld-linux and glibc. This does not mess with the system installation and does not need root privileges.

```bash
#!/bin/bash

mkdir ~/glibc 
cd ~/glibc

repo=http://copr-be.cloud.fedoraproject.org/results/mosquito/myrepo-el6/epel-6-x86_64/glibc-2.17-55.fc20

get() {
    wget $repo/$1
    rpm2cpio $1 | cpio -idmv
}

get glibc-2.17-55.el6.x86_64.rpm
get glibc-common-2.17-55.el6.x86_64.rpm
get glibc-devel-2.17-55.el6.x86_64.rpm
get glibc-headers-2.17-55.el6.x86_64.rpm

conda install patchelf

patchelf --set-interpreter $HOME/glibc/lib64/ld-linux-x86-64.so.2 --set-rpath $HOME/glibc/lib64:$HOME/glibc/usr/lib64:'$ORIGIN/../lib' /path/to/pytorch/bin/python

conda activate pytorch

python -c 'import torch; print(torch.randn(4))'
```



**Note**: There are a few utilities in `~/glibc/usr/bin` (e.g. `ldd`) that may be needed or useful. Consider prepending it to `PATH`.