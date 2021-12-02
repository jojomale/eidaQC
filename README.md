*This project is in still in development. It is usable but not*
*all errors are handled properly*


Run tests on the 
[European Integrated Data Archive](http://www.orfeus-eu.org/data/eida/) 
for seismological data
to check the availability of waveform data and the processing of metadata requests.

This package provides two different tests to check the availability of waveform data and the processing of 
meta data requests on EIDA. 
The tests are intended to be run on a regular 
basis, e.g. via a cron job. The package also creates an
automatic summary report of the results.

# Documentation

https://eidaqc.readthedocs.io/

(in progress)

# Installation

For more details, take a look at https://eidaqc.readthedocs.io/en/latest/eidaqc.html#installation

## Install dependencies
You need `pip` or `pipenv` to install eidaqc. Eidaqc was developed on Python 3.9.7 but
should run on lower versions of Python 3 (tested Python 3.6, requires additional package importlib_resources). Python 2 is not supported.

The following packages are required to run eidaqc:
- Obspy: https://github.com/obspy/obspy/wiki#installation
- Numpy
- Matplotlib

Their **installation will be forced** along the installation of eidaqc if not already present.


Optionally, if you want your results plotted on a nice map, you should install one of these mapping libraries:
- Cartopy: https://scitools.org.uk/cartopy/docs/latest/installing.html
- Basemap Matplotlib Toolkit: https://matplotlib.org/basemap/

They are **not installed automatically** with eidaqc if not already available to your Python.

Cartopy is recommended and preferred, but on an older system (Ubuntu 18.04)
installation of its predecessor basemap might be easier. However, development of basemap has stopped and shifted to cartopy.


## Install eidaqc

After installing the dependencies, eidaqc can be installed 
via pip from Github (also recommended if you use conda):


    ```
    $ pip install git+https://github.com/jojomale/eidaQC.git
    ```


Alternatively can also use pipenv:

    ```
    $ pipenv install git+https://github.com/jojomale/eidaQC.git#egg=eidaqc
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
- `avail`: optionally `ignore-missing`. Forces creation
    of new inventory despite missing reference networks
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
