

# print("Callin run eida availability")
# print("__PACKAGE__", __package__)
# print("__NAME__", __name__)

# __package__ = "eidaqc"
# print("__PACKAGE__", __package__)


#from eidaqc import eida_config

"""
Command line interface to eidaqc package

Syntax:
    eida <method> <args> <configfile>

method:
    - avail: run availability test
    - inv:   run inventory test
    - rep:   create html and pdf report
    - templ: create templates of config file 
    and html-style file

args:
    - avail: ignore-missing (optional), if given
        missing reference networks after inventory
        update are ignored. Use to force the creation
        of an initial inventory.
    - inv: request level for inventory. Any of
        'network', 'station' or 'channel'
    - rep: none
    - templ: none

configfile:
    - methods 'avail', 'inv', 'rep': 
        mandatory, path to config file
    - method 'templ': 
        optional; file name for default
        file. If not given file name will be 
        "default_config.ini" in current dir.

"""


import sys


def main():
    #print(__doc__)
    if len(sys.argv) < 2:
        print(__doc__)
        sys.exit()

    prg = sys.argv[1]
    print("Starting eida", prg)

    configfile = sys.argv[-1]
    print("Reading configuration from %s" % configfile)
    if "avail" in prg.lower():
        if "ignore-missing" in sys.argv:
            ignore_missing = True
        else:
            ignore_missing = False
        from . import eida_availability
        eida_availability.run(configfile, maxage=None, 
                    ignore_missing=ignore_missing)

    elif "inv" in prg.lower():
        from . import eida_inventory
        eida_inventory.run(sys.argv[-2], configfile)

    elif "rep" in prg.lower():
        from .eida_config import EidaTestConfig
        from .eida_report import EidaTestReport
        config = EidaTestConfig(configfile, "report")
        etr = EidaTestReport(config)
        etr.daily_report()

    elif "templ" in prg.lower():
        from .eida_config import create_default_configfile
        if sys.argv[-1] != prg:
            outfile = sys.argv[-1]
        else:
            outfile = None
        create_default_configfile(outfile)
    else:
        print("Unknown command")
        print(__doc__)
    print('Finish')

if __name__ == "__main__":
    main()