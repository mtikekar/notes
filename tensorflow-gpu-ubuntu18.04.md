# Install Tensorflow-GPU on Ubuntu 18.04

I find the official instructions and the various blog posts for installing Tensorflow with GPU support too complicated. I prefer these instructions for the following reasons.

- This setup uses the "system" NVIDIA graphics drivers that Ubuntu recommends.
- Except for the graphics drivers, everything is installed in the user's directory. Dependencies like CUDA, and CUDNN are installed in the Python environment with Tensorflow.



# Understanding dependencies

Installing Tensorflow's dependencies can be very confusing. This is my simplified flow:

1. The official version of tensorflow-gpu (to be installed with pip) needs CUDA 9.0.
2. CUDA 9.0 needs [graphics drivers >= 384](https://docs.nvidia.com/deploy/cuda-compatibility/index.html)
3. Tensorflow also needs CUDNN. We will install CUDNN 7.1.2 as that works with CUDA 9.0.
4. Other dependencies will be installed with CUDA.



# Graphics drivers

If you have already installed the graphics drivers (>= 384) from Nvidia's deb/runfiles, graphics-drivers PPA or the Ubuntu's default repository, you can skip this part.

Starting with 18.04, Ubuntu has Nvidia graphics drivers in its repositories by default. The version I have installed is 390. Note that you'll need Secure Boot disabled from your BIOS to install these drivers.

Also, it is best to disable nouveau drivers. Put a file at `/etc/modprobe.d/blacklist-nouveau.conf` with:

```
blacklist nouveau
options nouveau modeset=0
```



# Tensorflow

The Anaconda version of tensorflow-gpu installs all its dependencies, but it is not compiled for any advanced CPU instructions like SSE, AVX, AVX2. The pip version of tensorflow-gpu does come with AVX support - but not AVX2 support.

So the plan is to install all the dependencies from Anaconda and finally pip install tensorflow-gpu. The pip version of tensorflow-gpu requires cuda-9.0 while the latest on Anaconda uses a newer cuda. So we will make sure to install cuda-9.0 with conda.

```bash
conda create -n tf python=3.6 # or -p path/to/tf/env
conda activate tf # or source activate tf
conda install matplotlib ipykernel tensorboard
conda install --only-deps tensorflow-base cudnn=7.1.2 # make sure it installs cudatoolkit 9.0 and not 9.2
pip install tensorflow-gpu
```



The following python code should now run:

```python
import tensorflow as tf

a = tf.constant([1.0, 2.0, 3.0, 4.0, 5.0, 6.0], shape=[2, 3], name='a')
b = tf.constant([1.0, 2.0, 3.0, 4.0, 5.0, 6.0], shape=[3, 2], name='b')
c = tf.matmul(a, b)

sess = tf.Session(config=tf.ConfigProto(log_device_placement=True))

print(sess.run(c))
```

This should print a warning about the CPU supporting AVX2 and FMA but tensorflow not compiled to use them. It should also print that the variables and the matrix multiplication operator were mapped to the GPU.



# Multiple GPUs

Run `conda install nccl` to get NVIDIA's GPU-GPU communication library. I haven't tested that the installed version of tensorflow actually uses it. Tensorflow's official install instructions list it as an optional dependency. If you do test it, let me know.