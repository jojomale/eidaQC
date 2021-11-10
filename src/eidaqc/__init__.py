"""
Run test on data request processing in Eida virtual network.

This package provides two different tests to check the availability
of waveform data and the processing of meta data requests on the 
EIDA network. The tests are intended to be run on a regular 
basis, e.g. via a cron job. The package also creates an
automatic summary report of the results.




Installation
================
Eidaqc runs on **Python 3.6 or higher**.
You need `pip 
<https://pip.pypa.io/en/latest//>`_ to install eidaqc.

Eidaqc was developed on Python 3.9.7 and Linux Mint 20 (based on
Ubuntu 20.04). 
It should run on lower versions of Python 3 (tested Python 3.6, 
requires additional package importlib_resources). Python 2 
is not supported.


Install dependencies
--------------------------
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
manual.
    
- https://packaging.python.org/guides/installing-using-linux-tools/#installing-pip-setuptools-wheel-with-linux-package-managers
- venv: https://docs.python.org/3/library/venv.html


On **Ubuntu**, you can install obspy from an `apt repository 
<https://github.com/obspy/obspy/wiki/Installation-on-Linux-via-Apt-Repository/>`_. 
This should install all necessary libraries including 
numpy, matplotlib and basemap.





Install eidaqc
------------------
eidaqc can be installed via pip from Github:

.. code-block:: console

    $ pip install git+https://github.com/jojomale/eidaQC.git

If you do not want pip to install dependencies, e.g. because you
want to use system packages installed via **apt**, use:

.. code-block:: console

    $ pip install --no-deps git+https://github.com/jojomale/eidaQC.git


Afterwards the command ``eida`` should be available.    

If you run Python<=3.7, this will additionally install 
`importlib_resources 
<https://importlib-resources.readthedocs.io/en/latest/index.html/>`_.



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
- ``avail``: run availability test (:py:mod:`eidaqc.eida_availability`)
- ``inv``:   run inventory test (:py:mod:`eidaqc.eida_inventory`)
- ``rep``:   create html and pdf report (:py:mod:`eidaqc.eida_report`)
- ``templ``: create templates of config file 
  and html-style file (:py:mod:`eidaqc.eida_config`)

args:
`````````
- ``avail``: [ignore-missing]
    Optional. Forces creation
    of new inventory despite missing reference networks.
    Useful, if run for the first time.
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



In cron job
-----------------
The tests are intended to be run on a regular basis. E.g.
we run the availability test every minute and the inventory
test every hour.

On Linux, the command line interface can be used to run 
tests regularly as `cron job 
<https://help.ubuntu.com/community/CronHowto/>`_.

If you run eidaqc without conda, you can insert the CLI commands
directly in the crontab. If you run on conda, you may need to 
first activate the environment, in which eidaqc lives, with the
cron task. We use a bash script that combines the activation
of conda and the eida command (file eida_conda_cron.sh in 
GitHub repo):

.. code-block:: bash

    #!/bin/bash/

    # Call as:
    # $ run_eida_avail <prg>
    # <prg> can be `avail`, `inv` or `rep`

    # Path to config file
    configfile=~/Work/config_eidatests.ini
    invlevel="channel"
    echo "running eida test with "$configfile

    # Activate conda environment with eidaqc
    source ~/miniconda3/etc/profile.d/conda.sh
    conda activate eidaQC

    # Run CLI
    if [ $1 == "avail" ]; then
    eida avail $configfile
    elif [ $1 == "inv" ]; then
    eida inv $invlevel $configfile
    elif [ $1 == "rep" ]; then
    eida rep $configfile
    else
    echo "Unknown argument" $1
    fi

    # Deactivate conda again
    conda deactivate



Our corresponding cron tab looks like this:

.. code-block:: bash

    # Shell variable for cron
    SHELL=/bin/bash
    # PATH variable for cron
    PATH=~/miniconda3/bin:/home/lehr/miniconda3/condabin:/usr/local/bin:/usr/local/sbin:/sbin:/usr/sbin>
    # m h  dom mon dow   command
    * * * * * conda activate eidaQC; bash ~/Work/run_eida_avail.sh avail>> ~/Work/cronlog.txt
    1 * * * * conda activate eidaQC; bash ~/Work/run_eida_avail.sh inv>> ~/Work/cronlog_inv.txt





"""