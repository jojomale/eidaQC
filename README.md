Run test on data request processing in Eida virtual network.

This package provides two different tests to check the availability
of data and the processing of data requests on the 
EIDA network. The tests are intended to be run on a regular 
basis, e.g. via a cron job. The package also creates an
automatic summary report of the results.

# Documentation

https://eidaqc.readthedocs.io/

(in progress)

# Installation

## Install dependencies
-You need `pip` to install eidaqc.

The following packages are required to run eidaqc:
- Cartopy: https://scitools.org.uk/cartopy/docs/latest/installing.html
- Obspy: https://github.com/obspy/obspy/wiki#installation
- Numpy
- Matplotlib

Cartopy and obspy themselves depend on a number of packages 
including numpy and matplotlib.

### Using conda
eidaqc itself will be installed via pip. However conda makes
the installation of the required packages a lot easier,
notably for cartopy.

You may want to create a virtual environment first:

    ```
    $ conda create -n myeidaqc pip
    $ conda activate myeidaqc
    ```

    ```
    $ conda install -c conda-forge cartopy obspy matplotlib numpy
    ```


## Without conda
Virtual environments can also be managed e.g. `virtualenv`.
Installing the package including its dependencies directly from
pip doesn't work because the dependencies have dependencies of
their own. 
In particular cartopy requires a installation of its dependencies
in the right order, so please refer to their installation
manual. Obspy wasn't tested so far.

*If you can provide a working installation order please let us know.*


## Install eidaqc

After installing the dependencies, eidaqc can be installed 
via pip from Github:


    ```
    $ pip install git+https://github.com/jojomale/eidaQC.git
    ```

# Usage

1. as API
2. as command line tool:
    ```
    eida <method> <args> <configfile>
    ```

## Command line options
### Method
- `avail`: run availability test
- `inv`:   run inventory test
- `rep`:   create html and pdf report
- `templ`: create templates of config file 
            and html-style file

### args:
- `avail`: -
- `inv`: <level>
    request level for inventory. Any of
    'network', 'station' or 'channel'
- `rep`: -
- `templ`: -

### configfile:
- methods 'avail', 'inv', 'rep': mandatory,
        path to config file
- method 'templ': optional; file name for default
    file. If not given file name will be 
    "default_config.ini" in current dir.


# Build documentation
Documentation is build using sphinx and the readthedocs-template. You need to install both:

```bash
$ conda install sphinx
$ pip install sphinx-rtd-theme
```

Then you can run:
```bash
$ mkdir doc
$ cd doc
$ sphinx-quickstart 
```
which asks for some user input. It creates a sceleton structure for
the documentation and an initial configuration file `conf.py`.

Edit `conf.py` as follows:

```python
import os
import sys
sys.path.insert(0, os.path.abspath('../src'))

[...]

extensions = ['sphinx.ext.autodoc', 
              'sphinx.ext.napoleon']

[...]

html_theme = 'sphinx_rtd_theme'
```

Then run:
```bash
$ sphinx-apidoc -e -M -f -o . ../src/eidaqc
$ sphinx-build -b html . html
```

The first lays out the package structure in `modules.rst`
and `eidaqc.rst`.
The second command builds a HTML-page in a subdirectory `html`.

# Resources

## Build and packaging
```bash
$ python -m build
```
- https://packaging.python.org/tutorials/packaging-projects/
- https://packaging.python.org/guides/distributing-packages-using-setuptools/
- https://setuptools.pypa.io/en/latest/userguide/datafiles.html
- https://packaging.python.org/discussions/install-requires-vs-requirements/#install-requires-vs-requirements-files
- https://github.com/pypa/sampleproject


## Access data 
- https://stackoverflow.com/questions/779495/access-data-in-package-subdirectoryhttps://stackoverflow.com/questions/779495/access-data-in-package-subdirectory
- https://stackoverflow.com/questions/6028000/https://stackoverflow.com/questions/6028000/how-to-read-a-static-file-from-inside-a-python-package
- https://docs.python.org/3/library/importlib.html#module-importlib.resources
- https://importlib-resources.readthedocs.io/en/latest/using.html

## Entry points
- https://setuptools.pypa.io/en/latest/userguide/entry_point.html#dynamic-discovery-of-services-and-plugins

## Project Layout
- https://realpython.com/python-application-layouts/
- https://github.com/pypa/sampleproject

## Import horror
- https://docs.python.org/3/reference/import.html
- https://realpython.com/python-import/

## Docs
- https://sphinx-rtd-tutorial.readthedocs.io/en/latest/index.html