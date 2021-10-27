"""
Run test on data request processing in Eida virtual network.

This package provides two different tests to check the availability
of data and the processing of data requests on the 
EIDA network. The tests are intended to be run on a regular 
basis, e.g. via a cron job. The package also creates an
automatic summary report of the results.




Installation
================
After installing the dependencies, eidaqc can be installed 
via pip:

From BGR's SVN-server:

.. code-block:: console

    $ pip install pip install svn+svn://svn.hannover.bgr.de/EidaQualityCheck/trunk/eidaQC#egg=eidaqc
    

From source distribution:

.. code-block:: console

    $ pip install eidaqc-0.0.1.tar.gz



Install dependencies
--------------------------
- https://scitools.org.uk/cartopy/docs/latest/installing.html
- https://github.com/obspy/obspy/wiki#installation
- https://docs.conda.io/projects/conda/en/4.6.0/_downloads/52a95608c49671267e40c689e0bc00ca/conda-cheatsheet.pdf

Using conda
-------------
eidaqc itself will be installed via pip. However conda makes
the installation of the required packages a lot easier,
notably for cartopy.

You may want to create a virtual environment first:

.. code-block:: console

    $ conda create -n myeidaqc pip
    $ conda activate myeidaqc
        `

.. code-block:: console

    $ conda install -c conda-forge cartopy obspy matplotlib numpy
    $ pip install eidaqc-0.0.1.tar.gz


Without conda
---------------
Virtual environments can also be managed e.g. `virtualenv`.
Installing the package including its dependencies directly from
pip doesn't work because the dependencies have dependencies of
their own. 
In particular cartopy requires a installation of its dependencies
in the right order, so please refer to their installation
manual.
Obspy wasn't tested so far.
So after installing cartopy,obspy,numpy and matplotlib run:
    
 .. code-block:: console

    $ pip install eidaqc-0.0.1.tar.gz
    



Usage
=======

1. as API
2. as command line tool:

.. code-block:: console

    eida <method> <args> <configfile>


Command line options
---------------------------
Method
`````````````
- ``avail``: run availability test
- ``inv``:   run inventory test
- ``rep``:   create html and pdf report
- ``templ``: create templates of config file 
  and html-style file

args:
`````````
- ``avail``: -
- ``inv``: <level>
    request level for inventory. Any of
    'network', 'station' or 'channel'
- ``rep``: -
- ``templ``: -

configfile:
`````````````
- methods ``avail``, ```inv``, ``rep``: mandatory,
        path to config file
- method ``templ``: optional; file name for default
    file. If not given file name will be 
    "default_config.ini" in current dir.


"""