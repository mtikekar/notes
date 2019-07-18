# Install Tensorflow-GPU on Ubuntu 18.04

I find the official instructions and the various blog posts for installing Tensorflow with GPU support too complicated. I prefer these instructions for the following reasons.

- This setup installs NVIDIA graphics drivers from an apt source (the graphics-drivers PPA) instead of a runfile from NVIDIA. This makes it easy to choose any version and to upgrade.
- Everything else i.e. TensorFlow, CUDA, CUDNN, etc. are installed in an Anaconda Python environment.
- Anaconda's TensorFlow uses MKL for CPU operations which is [faster](https://www.anaconda.com/tensorflow-in-anaconda) than Google's pip package.


# Understanding dependencies

Using Anaconda greatly simplifies installing TensorFlow as it manages all dependencies except for the graphics driver. For a given TensorFlow version, Anaconda has multiple packages each compiled for a different CUDA and Python version. Each CUDA version requires a minimum graphics driver version.

<table>
    <tr>
        <th>TensorFlow</th>
        <th colspan=4>Python</th>
        <th colspan=5>CUDA, Graphics driver</th>
    </tr>
    <tr>
        <th></th>
        <th>2.7</th><th>3.5</th><th>3.6</th><th>3.7</th>
        <th>8.0, >=375</th><th>9.0, >=384</th><th>9.2, >=396</th><th>10.0, >=410</th><th>10.1, >=418</th>
    </tr>
    <tr>
        <td>1.14.0</td>
        <td>✓</td><td> </td><td>✓</td><td>✓</td>
        <td> </td><td>✓</td><td>✓</td><td>✓</td><td>✓</td>
    </tr>
    <tr>
        <td>1.13.1</td>
        <td>✓</td><td> </td><td>✓</td><td>✓</td>
        <td> </td><td>✓</td><td>✓</td><td>✓</td><td> </td>
    </tr>
    <tr>
        <td>1.12.0</td>
        <td>✓</td><td> </td><td>✓</td><td> </td>
        <td> </td><td>✓</td><td>✓</td><td> </td><td> </td>
    </tr>
    <tr>
        <td>1.11.0</td>
        <td>✓</td><td> </td><td>✓</td><td> </td>
        <td> </td><td>✓</td><td>✓</td><td> </td><td> </td>
    </tr>
    <tr>
        <td>1.10.0</td>
        <td>✓</td><td>✓</td><td>✓</td><td> </td>
        <td>✓</td><td>✓</td><td>✓</td><td> </td><td> </td>
    </tr>
    <tr>
        <td>1.9.0</td>
        <td>✓</td><td>✓</td><td>✓</td><td> </td>
        <td>✓</td><td>✓</td><td> </td><td> </td><td> </td>
    </tr>
    <tr>
        <td>1.8.0</td>
        <td>✓</td><td>✓</td><td>✓</td><td> </td>
        <td>✓</td><td>✓</td><td> </td><td> </td><td> </td>
    </tr>
</table>

To install a different version of TensorFlow, first determine the available CUDA versions with: `conda info tensorflow-base=<version> | grep cudatoolkit`. Next, look up the graphics driver version needed in NVIDIA's [compatibility table](https://docs.nvidia.com/deploy/cuda-compatibility/index.html#binary-compatibility__table-toolkit-driver). The installed graphics driver version can be checked with `nvidia-smi`.


# Install graphics drivers

You typically want the latest version as it supports the most number of GPU families and the most number of CUDA versions. I installed `nvidia-410` from the graphics-drivers PPA. Note that you'll need Secure Boot disabled in your BIOS for these drivers to work. Once you've rebooted, you can test that your driver works with the `nvidia-smi` command. It should list your graphics card. You can now safely disable the nouveau drivers. Put a file at `/etc/modprobe.d/blacklist-nouveau.conf` with:

```
blacklist nouveau
options nouveau modeset=0
```


# Install TensorFlow

```bash
conda create -n tf # or -p path/to/tf/env
conda activate tf # or source activate tf
conda install python=3.6 tensorflow-gpu=1.13.1 matplotlib ipykernel ...
```

If you have an older graphics driver, you need to specify the CUDA version it supports instead of letting `conda` pick the latest version.

```bash
conda install python=3.6 tensorflow-gpu=1.13.1 cudatoolkit=9.0 ...
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

It should print that the variables and the matrix multiplication operator were mapped to the GPU.

This might also print a warning that the CPU supports AVX, AVX2, etc. and that TensorFlow was not compiled to use them. You can ignore this warning - all compute intensive CPU operations are actually off-loaded to MKL which does use the latest CPU features. See [Intel's guide](https://software.intel.com/en-us/articles/intel-optimization-for-tensorflow-installation-guide) for more info.


# Multiple GPUs

Run `conda install nccl` to get NVIDIA's GPU-GPU communication library. I haven't tested that the installed version of tensorflow actually uses it. Tensorflow's official install instructions list it as an optional dependency. If you do test it, let me know.
