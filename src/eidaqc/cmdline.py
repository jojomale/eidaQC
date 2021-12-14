"""
Command line interface to eidaqc package

The general syntax is:

.. code-block:: console

    eida <subcommand> <args> <configfile>


So, the commands work similar to svn or git commands.
The options for ``<args>`` and ``<configfile>`` depend 
on the subcommand.
For details see :ref:`here <cli>` .

Technical notes
----------------
Parsing of command line arguments is handled using
argparse. Subcommands are handled as subparsers, each
of which has ``func`` set as default which points to 
a small function that executes the corresponding 
command of the eiqaqc API.


"""


import argparse, pathlib, sys


def _eida_templ(parser, args):
    """
    Executed if subparser *templ* is called.
    """
    from .eida_config import create_default_configfile
    create_default_configfile(args.outputfile)


def _eida_avail(parser, args):
    """
    Executed if subparser *avail* is called.
    """
    if any([args.configfile is None]):
        parser.parse_args(["avail", "-h"])
    from . import eida_availability
    eida_availability.run(args.configfile, maxage=None, 
                ignore_missing=args.ignore_missing)


def _eida_inv(parser, args):
    """
    Executed if subparser *inv* is called.
    """
    print(args)
    if any([args.configfile is None, args.request_level is None]):
        parser.parse_args(["avail", "-h"])   
    
    from . import eida_inventory
    eida_inventory.run(args.request_level, args.configfile)


def _eida_rep(parser, args):
    """
    Executed if subparser *rep* is called.
    """
    if args.configfile is None:
        parser.parse_args(["rep", "-h"])
    from .eida_config import EidaTestConfig
    from .eida_report import EidaTestReport
    config = EidaTestConfig(args.configfile, "report")
    etr = EidaTestReport(config)
    etr.daily_report()



def main():
    """
    Main routine that defines the parsers and calls
    the subroutines depending on user input (i.e.
    parsed arguments)
    """

    # Main parser
    parser = argparse.ArgumentParser(description="Command line " + 
        "interface to eidaqc package",
        epilog="Use `eida subcommand -h` for details and options on each command.")
    subparsers = parser.add_subparsers(title="subcommands", 
        help="one of the subprogram in eidaqc",
        )
    
    # Define arguments for subparsers
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
    templ.set_defaults(func=_eida_templ)

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
    avail.set_defaults(func=_eida_avail)

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
    inv.set_defaults(func=_eida_inv)

    rep = subparsers.add_parser("rep",
        description="Create report of Eidaqc test results.",
        help="Create report of Eidaqc test results in "+
            "markdown & HTML",
        aliases=["report"])
    rep.add_argument("configfile", 
        type=pathlib.Path,
        help="Configuration file with parameter settings. "+ 
            "Use `eida templ` to create default template.")
    rep.set_defaults(func=_eida_rep)


    args = parser.parse_args()

    # If User enters only 'eida' we show help of 
    # main parser which lists the subprograms
    if len(sys.argv) < 2:
        parser.parse_args(["-h"])
    
    # Otherwise we call the respective subroutine
    args.func(parser, args)
    
    print('Finish')


if __name__ == "__main__":
    main()