"""
Command line interface to eidaqc package

Syntax:
    eida <method> <args> <configfile>

    eida templ [configfile]
    eida avail [ignore-missing] configfile
    eida inv {network, station, channel} configfile
    eida rep configfile
    

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


import argparse, pathlib, sys


def eida_templ(parser, args):
    print("EIDA tmpl", args)
    from .eida_config import create_default_configfile
    create_default_configfile(args.outputfile)

def eida_avail(parser, args):
    if any([args.configfile is None]):
        parser.parse_args(["avail", "-h"])
    from . import eida_availability
    eida_availability.run(args.configfile, maxage=None, 
                ignore_missing=args.ignore_missing)

def eida_inv(parser, args):
    print(args)
    if any([args.configfile is None, args.request_level is None]):
        parser.parse_args(["avail", "-h"])   
    
    from . import eida_inventory
    eida_inventory.run(args.request_level, args.configfile)


def eida_rep(parser, args):
    if args.configfile is None:
        parser.parse_args(["rep", "-h"])
    from .eida_config import EidaTestConfig
    from .eida_report import EidaTestReport
    config = EidaTestConfig(args.configfile, "report")
    etr = EidaTestReport(config)
    etr.daily_report()



def main():

    parser = argparse.ArgumentParser(description="Command line " + 
        "interface to eidaqc package",
        epilog="Use `eida subcommand -h` for details and options on each command.")
    subparsers = parser.add_subparsers(title="subcommands", 
        help="one of the subprogram in eidaqc",
        # action="help"
        #choices=["templ", "avail", "inv", "rep"]
        )
    
    templ = subparsers.add_parser("templ", 
        description="Create default files",
        help="Create default files",
            aliases=["template"]
        )
    templ.add_argument("-o", "--outputfile", 
        type=pathlib.Path,
        help="file name for default file. " +
             "If not given file name will be "+
             "'default_config.ini' in current dir.")
    templ.set_defaults(func=eida_templ)


    avail = subparsers.add_parser("avail",
        description="Run availability test",
        help="Run availability test for a randomly selected station.",
            aliases=["availability"])
    avail.add_argument("configfile", 
        type=pathlib.Path,
        help="Configuration file with parameter settings. "+ 
            "Use `eida templ` to create default template.")
    avail.add_argument("-i", "--ignore_missing",
        default=False, action="store_true",
        help="If set missing networks will be ignored, "+ 
            "when inventory is requested from server. "+
            "Use when run for the first time and no cached inventory "+
            "is available ('outdir/chanlist_cache.pickle')")
    avail.set_defaults(func=eida_avail)

    inv = subparsers.add_parser("inv",
        description="Run inventory test",
        help="Tests availability of inventory data at specified "+
            "request level for networks in configfile",
            aliases=["inventory"])
    inv.add_argument("request_level", 
        choices=["network", "station", "channel"],
        help="Level of detail for the requested inventories. "+
            "'network' provides the least information " +
            "(and puts the least amount of load on the servers.")
    inv.add_argument("configfile", 
        type=pathlib.Path,
        help="Configuration file with parameter settings. "+ 
            "Use `eida templ` to create default template.")
    inv.set_defaults(func=eida_inv)


    rep = subparsers.add_parser("rep",
        description="Create report of Eidaqc test results.",
        help="Create report of Eidaqc test results in "+
            "markdown & HTML",
        aliases=["report"])
    rep.add_argument("configfile", 
        type=pathlib.Path,
        help="Configuration file with parameter settings. "+ 
            "Use `eida templ` to create default template.")
    rep.set_defaults(func=eida_rep)

    #print(parser._subparse)
    #print(parser.parse_args())
    args = parser.parse_args()

    # If User enters only 'eida' we show help of 
    # main parser which lists the subprograms
    if len(sys.argv) < 2:
        parser.parse_args(["-h"])
    
    args.func(parser, args)
    
    print('Finish')

if __name__ == "__main__":
    main()