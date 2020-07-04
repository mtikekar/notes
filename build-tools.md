## Make

Best practices: https://tech.davis-hansson.com/p/make/
Summary:

```makefile
SHELL := bash
.ONESHELL:
.SHELLFLAGS := -eu -o pipefail -c
.DELETE_ON_ERROR:
MAKEFLAGS += --warn-undefined-variables
MAKEFLAGS += --no-builtin-rules

ifeq ($(origin .RECIPEPREFIX), undefined)
  $(error This Make does not support .RECIPEPREFIX. Please use GNU Make 4.0 or later)
endif
.RECIPEPREFIX = >

# Default - top level rule is what gets ran when you run just `make`
build: out/image-id
.PHONY: build

# Clean up the output directories; since all the sentinel files go under tmp, this will cause everything to get rebuilt
clean:
> rm -rf tmp
> rm -rf out
.PHONY: clean

# Tests - re-ran if any file under src has been changed since tmp/.tests-passed.sentinel was last touched
tmp/.tests-passed.sentinel: $(shell find src -type f)
> mkdir -p $(@D)
> node run test
> touch $@ 

# Webpack - re-built if the tests have been rebuilt (and so, by proxy, whenever the source files have changed)
tmp/.packed.sentinel: tmp/.tests-passed.sentinel
> mkdir -p $(@D)
> webpack ..
> touch $@

# Docker image - re-built if the webpack output has been rebuilt
out/image-id: tmp/.packed.sentinel
> mkdir -p $(@D)
> image_id="example.com/my-app:$$(pwgen -1)"
> docker build --tag="$${image_id}
> echo "$${image_id}" > out/image-id
```

## CMake

CMake is not a make replacement. It is a:

1. Makefile generator. Also generates for other build systems like Ninja
2. Primarily a C++ build tool. It understands C++ standards and toolchains (GCC, Clang, etc.). Also knows about CUDA, pthreads, etc.
3. A layer of abstraction over compiler CLI options
4. Find dependencies and propagate necessary compiler options upwards. Uses global variables to pass info to/from find scripts which is easy to write but hard to read.
5. Creates a cache of variables in the configure step and understands dependencies of those variables. Will re-run configure if needed.

Without cmake:

```bash
./configure
make
```

With cmake:

```bash
mkdir build
cmake ..
cmake --build . # or, make
```

Nice tutorial: https://cliutils.gitlab.io/modern-cmake/

## Redo

Rethinks make: https://github.com/apenwarr/redo/
