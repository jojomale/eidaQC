#! /usr/bin/env python
#
# file eida_inventory.py
#      ======================
#
# J. Lehr, 29-Oct-2021
# K. Stammler, 17-Jun-2020

"""
Test 'get_stations' response, compare retrieved networks between routing
client and separate requests to EIDA servers directly.

"""

from __future__ import print_function
import os
import sys
import time
import datetime
import logging
import logging.handlers

from obspy import UTCDateTime, _get_version_string
from obspy.clients.fdsn import RoutingClient
from obspy.clients.fdsn.client import Client

from . import eida_config, statuscodes

# print("NAME", __name__)
# print("PACKAGE", __package__)
#print('MAIN', __main__)
#print(sys.path)
#sys.path.append(sys.path[0]+'/../')
from .eida_logger import create_logger, configure_handlers

# print("eida_inventory NAME", __name__)
# print("eida_inventory PCKG", __package__)

legal_reqlevels = ('network','station','channel')


# Initialize logger
logger = create_logger()

module_logger = logging.getLogger(__package__+".eida_inventory")
module_logger.setLevel(logging.DEBUG)
#-------------------------------------------------------------------------------


class Logtext:
    """
    Manage output of results from inventory test

    We use the logging module with a TimedRotatingFileHandler
    to log the results. The handler allows to renew the 
    current logfile at a specified time. A number of backup
    files to be kept, counting from now into the past, can be
    chosen.


    Example
    -----------
    Start a new file at each monday at midnight, keep results
    up to 1 year:

    .. code-block::python
        
        # Renew at Monday
        rotate_log_at = "W0"
        
        # Keep 52 weeks =~ 1 year
        inv_log_bckp_count = 52

        # Set time to midnight (the date doesn't matter here)
        rotate_log_at_time=UTCDateTime("2100-01-01T00:00:00)

    
    From the config file only some arguments of the log handler
    can be accessed, allowing only for rotations after 24h or 
    7 days. However, if used as module you can set all 
    additional parameters.
    """
    
    def __init__( self, datapath, rotate_log_at,
                 inv_log_bckp_count, rotate_log_at_time=None,
                 **kwargs):
        """
        Parameters
        ------------
        datapath : str
            directory for result file
        rotate_log_at: str 
            corresponds to `when`
        inv_log_bckp_count: int
            correspond to `backupCount`
        rotate_log_at_time: None, datetime.time
            corresponds to `atTime`
        kwargs :
            pass additional parameters to 
            TimedRotatingFileHandler


        
        """
        
        
        # This is the logger for info and error messages
        self.logger = logging.getLogger(module_logger.name +
                        ".Logtext")


        # Now we create the logger for the results
        datapath = os.path.join(datapath, "eida_inventory_test")
        datapath = eida_config.expandpath(datapath) 
        
        ## Check if intended directory exists
        if not os.path.exists(datapath):
            self.logger.info("Created directory for results: %s" 
                    % datapath)
            os.makedirs(datapath)
        else:
            self.logger.debug('Assuming directory for results %s'
                    % datapath)
        
        self.results = logging.getLogger('eida_inventory_test')
        self.results.setLevel(logging.INFO)
        
        ## file handler
        fh = logging.handlers.TimedRotatingFileHandler(
                os.path.join(datapath, 'eida_invtest_log'), 
                when=rotate_log_at, 
                backupCount=inv_log_bckp_count, 
                atTime=rotate_log_at_time, **kwargs)
        fh.setLevel(logging.INFO)
        
        ## create formatter
        hformatter = logging.Formatter('%(message)s')
        fh.setFormatter(hformatter)
        self.results.addHandler(fh)
        self.fh = fh

        self.logger.info("Find results in %s" %fh.baseFilename)


    def write( self, text ):
        """
        Write `text` to logger and result file.
        """
        self.logger.info( text )
        self.results.info( "%s" % text ) 


#-------------------------------------------------------------------------------

class EidaInventory():
    """
    Manage inventory test.
    """
    def __init__(self, reqlevel, 
                starttime=UTCDateTime(), 
                endtime=UTCDateTime()-24*3600,
                wanted_channels=('HHZ', 'BHZ', 'EHZ', 'SHZ'),
                timeout=240, ref_networks_servers={},
                datapath=os.getcwd(), rotate_log_at='midnight',
                inv_log_bckp_count=30, rotate_log_at_time=None,
                resultfile_kwargs={}, **kwargs):

        self.logger = logging.getLogger(module_logger.name +
                        ".EidaInventory")
        if reqlevel not in legal_reqlevels:
            self.logger.error( "Legal request levels are %s" % ','.join(legal_reqlevels) )
            raise RuntimeError("%s is not a legal request level" % reqlevel)
        else:
            self.reqlevel = reqlevel
        
        
        self.lt = Logtext(datapath, rotate_log_at,
                 inv_log_bckp_count, rotate_log_at_time,
                 **resultfile_kwargs)
        self.outfile = self.lt.fh.baseFilename
        self.channels = wanted_channels
        self.starttime = starttime
        self.endtime = endtime
        self.timeout = timeout
        self.servers = list(ref_networks_servers.values())


    def server_request(self, servers=None):
        """
        Request inventories from servers directly.

        Uses `obspy.clients.fdsn.client.Client(server)` on each
        server in EidaInventory.servers or `servers` if not `None`.
        
        Returns and sets attribute `snets` which is a set of all 
        networks retrieved.

        """
        if servers is not None:
            self.servers = servers
            self.logger.debug("Changing servers to %s" % servers)
        
        # Loop all EIDA servers for separate requests and store network list.
        snets = set( [] )
        self.logger.debug(servers)
        invpar = {
            'level'              : self.reqlevel,
            'channel'            : ",".join(self.channels),
            'starttime'          : self.starttime,
            'endtime'            : self.endtime,
            'includerestricted'  : False,
        }

        for srv in self.servers:
            self.lt.write( "    reading inventory from server %s" % srv )
            try:
                client = Client( srv, timeout=self.timeout)
                sinv = client.get_stations( **invpar )
            except Exception as e:
                self.lt.write( "        FAILED: %s" % repr(e) )
                continue
            addset = set( sinv.get_contents()['networks'] )
            snets = snets.union( addset )
        self.snets = snets
        return snets


    def routing_request(self):
        """
        Request inventories using
        `obspy.clients.fdsn.RoutingClient( "eida-routing" )`
        
        RoutingClient retrieves all available inventories in
        EIDA virtual network without specifying a server. It
        finds its way to the server "on its own".

        Returns and sets attribute `rnets` which is a set of all 
        networks retrieved.
        """
        # Use RoutingClient.
        self.lt.write( "    reading inventory from routing client" )
        invpar = {
            'level'              : self.reqlevel,
            'channel'            : ",".join(self.channels),
            'starttime'          : self.starttime,
            'endtime'            : self.endtime,
            'includerestricted'  : False,
            'timeout'            : self.timeout
        }
        try:
            roc = RoutingClient( "eida-routing" )
            rinv = roc.get_stations( **invpar )
        except Exception as e:
            self.lt.write( "        FAILED: %s" % repr(e) )
            self.lt.write( "\n==========================================================\n" )
            exit()
        self.rnets = set( rinv.get_contents()['networks'] )
        

    def check4missing_networks(self, reference_networks):
        self.logger.debug("Running check for missing reference networks")
        miss = []
        for net in reference_networks:
            if net not in self.rnets:
                miss.append( net )
        self.missing_ref_networks = sorted(miss)
        return sorted(miss)


    def print_results(self, runtime=99999.9):
        if self.missing_ref_networks:
            self.lt.write( "missing reference networks: %s" % 
                            ','.join(self.missing_ref_networks) )
        self.lt.write( "rnets (%d) %s" % (len(self.rnets),', '.join(sorted(self.rnets))) )
        self.lt.write( "snets (%d) %s" % (len(self.snets),', '.join(sorted(self.snets))) )
        self.lt.write( "rnets-snets %s" % ', '.join(sorted(self.rnets-self.snets)) )
        self.lt.write( "snets-rnets %s" % ', '.join(sorted(self.snets-self.rnets)) )
        self.lt.write( "runtime %3.1fs" % runtime )
        self.lt.write( "\n==========================================================\n" )



def run(reqlevel, configfile):
    config = eida_config.EidaTestConfig(configfile, which="inv")
    configure_handlers(logger, **config.loghandlers)
    module_logger.debug('Running eida_inventory.run()')
    stamp = time.time()
    ei = EidaInventory(reqlevel, 
             **config.get_invtest_dict())
    ei.lt.write( "\neida_inventory_test.py started at %s MEST, level %s (obspy %s) timeout %d (timeout bugfix, no restricted)"
        % (datetime.datetime.now().strftime("%d-%b-%Y_%T"),
        reqlevel, _get_version_string(), 
        config.invtest['timeout']) )
    ei.server_request()
    ei.routing_request()
    missref = ei.check4missing_networks(
        config.invtest['reference_networks'])
    runtime = time.time() - stamp
    # Write results.
    # if missref:
    #     ei.lt.write( "missing reference networks: %s" % ','.join(missref) )
    # ei.lt.write( "rnets (%d) %s" % (len(ei.rnets),', '.join(sorted(ei.rnets))) )
    # ei.lt.write( "snets (%d) %s" % (len(ei.snets),', '.join(sorted(ei.snets))) )
    # ei.lt.write( "rnets-snets %s" % ', '.join(sorted(ei.rnets-ei.snets)) )
    # ei.lt.write( "snets-rnets %s" % ', '.join(sorted(ei.snets-ei.rnets)) )
    # ei.lt.write( "runtime %3.1fs" % runtime )
    # ei.lt.write( "\n==========================================================\n" )
    ei.print_results(runtime)
    
    

    


if __name__ == '__main__':
    # Retrieve parameter from command line.
    if len(sys.argv) < 2:
        print( __doc__ )
        exit()
    
    #print(sys.argv)
    reqlevel = sys.argv[-1]
    #print(reqlevel)

    
    run(reqlevel)
    

