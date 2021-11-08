

.. code-block:: bash

    $ sudo apt install python3-venv python3-pip
    $ python3 -m venv net/EIDAQC
    $ source net/EIDAQC/bin/activate
    $ pip install numpy matplotlib obspy
    $ sudo apt install libgeos-dev
    $ pip install shapely
    $ pip install pyshp
    $ sudo apt-get install proj-bin

    sudo apt install python3-pip
    pip3 install virtualenv
    virtualenv -p /usr/bin/python3 py3
    source py3/bin/activate
    pip install numpy matplotlib obspy
    sudo apt install libgeos-dev
    pip install shapely pyshp
    sudo apt-get install proj-bin
    pip install pyproj
    





Virgin Ubuntu 18.04.6 LTS

.. code-block:: bash
   
    $ sudo apt install wget software-properties-common 
    $ sudo add-apt-repository ppa:deadsnakes/ppa 
    $ sudo apt update
    $ sudo apt install python3.9
    $ # sudo apt install virtualenv
    $ # pip3 install virtualenv
    $ source venv/bin/activate

