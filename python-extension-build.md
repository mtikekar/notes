# Building a Python package with C/C++ extensions

Extensions are just libraries that are dynamically loaded by Python. But not all libraries bundled with a Python package are extensions. Depending on the use-cases listed below, each library may need to be compiled and linked differently.

1. Python extensions - python can `import` a library as a Python module if defines a function `PyInit_<modulename>`. There are libraries such as `pybind11`, `cffi`, `cython`, `boost.python` that can make it easy to wrap a C/C++ library into a Python extension. But this note is not about how to write the extension or wrappers, but about how to build them.
2. C/C++ library required by a python extension. Typically, this is the library that is being wrapped into Python.
3. C/C++ library that is not a python extension but needs to be linked to libpython anyway - maybe some of the C/C++ to Python interface code got leaked into that library.
4. C/C++ library with or without libpython linked that also needs to be available to external programs to link against. 4 is not so different from 2.
5. Python extension that needs to be available to external programs to link against.


Use-case 1 and 2 are common. Use-case 4 is in [cocotb](https://github.com/cocotb/cocotb) which also has 1, 2, 3. I haven't seen use-case 5. In principle, 3 and 4 are not so different from 1 and 2 but there are some OS-specific quirks to be aware of when building them.


## Relocatability

To distribute pre-built packages to users, the libraries should use relative paths to look for their local dependencies i.e. other libraries in the same package.

- Linux: use `$ORIGIN` in rpath (e.g. with `-Wl,-rpath,$ORIGIN` as gcc flag). `ldd` is a useful diagnostic tool to see if dependencies are being found correctly. In a pinch, `patchelf` can be used to view and modify `rpath` post-build.
- macOS: use `@loader_path ` in rpath and `@rpath` in `install_name` of libraries. Use `otool -L` and `otool -l exe_or_lib | grep -A2 LC_RPATH` to see if they're correctly set. Can also use env vars `DYLD_PRINT_LIBRARIES=1 DYLD_PRINT_LIBRARIES_POST_LAUNCH=1 DYLD_PRINT_RPATHS=1` at run-time. `install_name_tool` is the equivalent of `patchelf`.
- Windows: `%PATH%` environment variable works or use `AddDllDirectory()` (wrapped as `os.add_dll_directory` in Python)

On macOS, `@loader_path` is sometimes used instead of `@rpath` in the `install_name` of a library. This works, but only if all the libraries that link to it are in the same directory. Using `@rpath` in `install_name` and `@loader_path` in `rpath` is more general. See [this post](https://medium.com/@donblas/fun-with-rpath-otool-and-install-name-tool-e3e41ae86172) to learn more about library resolution on macOS.


## Tools for building Python extensions

- distutils - comes built into Python. It basically knows the right compile and link flags to use and does the build and install steps. The flags and paths can be gotten from `sysconfig.get_config_vars` and `get_paths` functions  or from `python -m sysconfig` on the command-line. However, not all config_vars are available on all OSes/distributions (e.g. `LIBDIR` is not available on Windows). 

  Other tools builds on top of distutils. In principle, distutils is all that is needed to run `python setup.py install|build|develop`, but python docs recommend using setuptools instead of distutils.

- setuptools - comes with pip. pip will automatically inject setuptools in place of distutils in your setup.py.  pip also installs dependencies. `pip >= 19` also supports build-time dependencies through `pyproject.toml`. This is especially needed if `setup.py` imports the build-time dependency and so cannot be parsed to get `setup_requires` from that file.

- [setuptools_dso](https://github.com/mdavidsaver/setuptools_dso) - provides an easy way to build libraries that aren't extensions (use-case 2). It will analyse the dependencies to set the right `rpath` flags. Unfortunately, it doesn't handle use-case 3, but it should be possible to add to it. It is also a relatively small module (600 lines over 2 files), so it can just be copied into your project to avoid the hassles of a build-time dependency.

- CMake - has a FindPython feature. pybind11 also has CMake integration. See [polygames](https://github.com/facebookincubator/Polygames) for example. Getting pip install to work is a simple matter of calling `cmake` in `setup.py` like [so](https://github.com/pybind/cmake_example/blob/master/setup.py).

- Make - in principle, you only need the compile and link flags from Python. You can do the rest yourself. See [this]( http://notes.secretsauce.net/notes/2017/11/14_python-extension-modules-without-setuptools-or-distutils.html) for example. Make can be integrated with pip in the same way as CMake above.

- Conda - provides packages for compilers, make, cmake and many other system libraries which enables having a consistent build environment. I typically use conda for my development/test/build environment but build the package with pip. 



## Finding the right compile/link flags

In principle, we just need to know the full paths to `Python.h` and `libpython<version>.<a/so/dll/dylib>`. As far as I can tell, there are no special compile or link flags needed for building a Python extension. 

`Python.h` is always at `sysconfig.get_path("include")` if it exists. On Linux, if you're using the system python, you need to install the development package.

Unfortunately, there is no standard platform-independent method to find the libpython for a python executable. To get the directory, see these [answers](https://stackoverflow.com/questions/47423246/get-pythons-lib-path) for how numpy, cmake and scikit-build do it, and this [300 line code](https://github.com/JuliaPy/PyCall.jl/blob/master/deps/find_libpython.py) for embedding Python in Julia. For now, I'm inclined to try numpy's simple method: `sys.prefix + '/libs' if windows else sysconfig.get_config_var('LIBDIR')`

The library name to link against can be gotten from `sysconfig.get_config_var("LDLIBRARY")` (except for macOS quirk below).



**Linux quirks**

- Distro's python statically links to `libpython.a`. But anaconda python is built linked to `libpython.so`. Not really a problem usually as `libpython.so` is still available.



**macOS quirks**

- OS and Homebrew python are linked against Python Framework, so `LDLIBRARY` is `Python.framework/Versions/<version>/Python`. You can use `LIBRARY` and replace `.a` with `.dylib`

- extensions are bundles and not libraries.
- extensions don't link to libpython. Python symbols are found via dynamic lookup because python has already loaded libpython before importing the extension.

Note: `python -m sysconfig | grep LDSHARED` gives the link flags to use for an extension. Look for `-bundle -undefined dynamic_lookup`

Due to the 3rd point, it is hard to get use-case 3 working on macOS reliably. The flags that are used for linking an extension (which is what `distutils/sysconfig` provide) cannot be used to link a library with libpython. We have to resort to finding libpython independently.



**Windows quirks**

- `sysconfig` doesn't have the `LIBDIR` variable.



A note about tox: tox does not play well with build-time dependencies because it's first step is to package up the source files with `python setup.py sdist` at which point the dependency is not yet available. So your `setup.py` needs to work without that dependency for that first step.