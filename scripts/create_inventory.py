# %%
import logging, pickle, os, sys
from obspy.clients.fdsn.client import Client, FDSNException
from obspy.clients.fdsn import RoutingClient
from eidaqc import eida_config
from obspy import UTCDateTime
from eidaqc.eida_logger import create_logger
#from obspy.core.inventory import Inventory

# %%
# Initialize logger
logger_base = create_logger()
logger = logging.getLogger(logger_base.name+'.create_inv')
logger.setLevel(logging.INFO)


def main(configfile):
    config = eida_config.EidaTestConfig(configfile, which="avinv")
    
    endtime=UTCDateTime()
    starttime=UTCDateTime()-config.avtest['eia_global_timespan_days']
    wanted_channels=config.invtest["wanted_channels"]
    timeout = 240
    invpar = {
                'level'              : "channel",
                'channel'            : ",".join(wanted_channels),
                'starttime'          : starttime,
                'endtime'            : endtime,
                'includerestricted'  : False,
    }

    slist_cache = os.path.join(config.paths["eia_datapath"], 
                            "chanlist_cache.pickle")
    servers = config.invtest['ref_networks_servers']

    logger.info("Paramters for creating inventory:")
    print("Parameters for request:\n", invpar)
    print("Servers by network:\n", servers)
    print("Will write inventory to", slist_cache)

    # %%
    logger.info("Starting eida-routing...")
    roc = RoutingClient( "eida-routing" )
    slist = roc.get_stations( timeout=timeout, **invpar )

    logger.info("Number of networks after eida-routing: %s" % 
            str(len(slist.get_contents()["networks"])))

    
    # %%
    # Update missing servers "manually" using direct FDSN request
    # to the server
    logger.info("Request missing networks from FDSN...")
    for net, srv in servers.items():
        print(net, srv, end=" - ")
        if net not in slist.get_contents()["networks"]:
            print("missing", end=" - ")
            try:
                client = Client( srv, timeout=timeout)
                sinv = client.get_stations( **invpar )
                slist.extend(sinv)
            except FDSNException:
                print("failed")
                continue
            else:
                print("from FDSN")
        else:
            print("available")

    logger.info("Number of networks after FDSN-requests: %s" %
            str(len(slist.get_contents()["networks"])))


    # %%
    # Write results to file
    logger.info("Write inventory to %s" % slist_cache)
    fp = open( slist_cache, 'wb' )
    pickle.dump( slist, fp )
    fp.close()


# %%
if __name__ == "__main__":
    if len(sys.argv) > 1:
        configfile = sys.argv[-1]
        logger.info("Reading paramters from configfile %s" %
            configfile)
    else:
        logger.info("No configfile given. Using default_config.ini")
        configfile = "default_config.ini"
    main(configfile)


