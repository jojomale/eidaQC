"""
Run test on data request processing in Eida virtual network.

This package provides two different tests to check the availability
of data and the processing of data requests on the 
EIDA network. The tests are intended to be run on a regular 
basis, e.g. via a cron job. The package also creates an
automatic summary report of the results.




Installation
================

Install dependencies
--------------------------
You need `pip <https://pip.pypa.io/en/latest//>`_ to install eidaqc.

The following packages are required to run eidaqc:

- `Numpy <https://numpy.org/install//>`_
- `Matplotlib <https://matplotlib.org/stable/users/installing.html/>`_
- `Obspy <https://github.com/obspy/obspy/wiki#installation/>`_

Cartopy and obspy themselves depend on a number of packages 
including numpy and matplotlib.



Using conda
````````````
eidaqc itself will be installed via pip. However conda makes
the installation of the required packages a lot easier,
especially for cartopy.


Installing conda:

.. code-block:: console
    
    mkdir -p ~/miniconda3
    wget https://repo.anaconda.com/miniconda/Miniconda3-latest-Linux-x86_64.sh -O ~/miniconda3/miniconda.sh
    bash ~/miniconda3/miniconda.sh -b -u -p ~/miniconda3
    rm -rf ~/miniconda3/miniconda.sh
    ~/miniconda3/bin/conda init bash
    source ~/.bashrc


After ``source`` your command line should change to:

.. code-block:: console

    (base) me@mymachine:~$ 


``(base)`` indicates that you are in the base environement
of conda.


You may want to create a new virtual environment for eidaqc:

.. code-block:: console

    $ conda create -n myeidaqc pip
    $ conda activate myeidaqc
        `

.. code-block:: console

    $ conda install -c conda-forge numpy matplotlib obspy cartopy




Without conda
````````````````````````````
Virtual environments can also be managed e.g. `virtualenv`.
Installing the package including its dependencies directly from
pip doesn't work because the dependencies have dependencies of
their own. 
In particular cartopy requires a installation of its dependencies
in the right order, so please refer to their installation
manual. Obspy wasn't tested so far.

*If you can provide a working installation order please let us know.*
    
- https://packaging.python.org/guides/installing-using-linux-tools/#installing-pip-setuptools-wheel-with-linux-package-managers
- venv: https://docs.python.org/3/library/venv.html



.. code-block:: bash

    $ sudo apt install python3-venv python3-pip
    $ python3 -m venv net/EIDAQC
    $ source net/EIDAQC/bin/activate
    $ pip install numpy matplotlib obspy
    $ sudo apt install libgeos-dev
    $ sudo apt-get install proj-bin









 

Install eidaqc
------------------
After installing the dependencies, eidaqc can be installed 
via pip from Github:

.. code-block:: console

    $ pip install git+https://github.com/jojomale/eidaQC.git


Afterwards the command ``eida`` should be available.    




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