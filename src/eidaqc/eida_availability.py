#! /usr/bin/env python
#
# file EidaAvailability.py
#      ===================
#
# K. Stammler, 17-Jun-2020
# J. Lehr, 13-Oct-2021
#
# For creation of reports, needs 'pandoc' and 'convert' (imagemagick).
# This also requires implementation specific code, see variables eia_spec_...
#
# Create report with:
# import EidaAvailability
# ar = EidaAvailability.AvailabilityReport()
# ar.make_md_report( 'avreport.md' )
# pdfreport = ar.make_pdf_report( 'avreport.md' )

"""
Test availability of data on random station in 
European Integrated Data Archive.



- Conducts random waveform requests to single channels of EIDA stations.
- Requested time span randomly selected from last year, span length between
  60 and 600 s.
- Station randomly selected from the subset of unrestricted 
  European EIDA
  stations offering at least one out of channels `HHZ`, `BHZ`, `EHZ` or `SHZ`.
- Request full station metadata from selected station and choose channel
  randomly, restricted to channels `HH?`, `BH?`, `EH?` and `SH?`.
- On successful request apply a restitution to the waveform data.
- Evaluate and store result of request in a file database.
- Plot and statistically analyze content of file database.
- Intended use case is to regularly run the request e.g. via cron job
  to build up a data base. The results can be evaluated using the
  module `eida_report`.

The code does not use the waveform catalog, therefore empty waveform returns
are due to data gaps or due to problems in data access and delivery.

An inventory of available EIDA stations is created regularly.
"""


from __future__ import print_function
import os
# import sys
import time
import signal
import datetime
import pickle
import logging
import tempfile

import numpy as np
from obspy.clients.fdsn import RoutingClient
from obspy import UTCDateTime

from .eida_logger import create_logger, configure_handlers
from . import statuscodes, eida_config

# Initialize logger
logger = create_logger()
module_logger = logging.getLogger(logger.name+'.eida_availability')
module_logger.setLevel(logging.DEBUG)
# print("MLOGGERNAME", module_logger.name)


#-------------------------------------------------------------------------------
class EidaAvailability:
    """
    Manage and execute random data requests.

    The main methods to use are:
    - random_request()
    - process_request()

    Parameters
    --------------
    eia_datapath : str, None
        path to output directory. In this directory results
        are placed in a sub-directory `log` 
    wanted_channels : tuple of str
        channels used to create inventory. However for actual 
        request any of available channels at a station is selected.
        Default: ('HHZ', 'BHZ', 'EHZ', 'SHZ'),
    eia_global_timespan_days : int [365]
        days into the past for which data requests will be created 
    maxcacheage : int, [5*86400]
        age of cached inventory in seconds. If inventory file is
        older, a new one is created from service. 
    minreqlen : int, [60]
        minimum length of waveform to request, in seconds
    maxreqlen: int, [600]
        maximum length of waveform, in seconds
    eia_timeout : int, [60]
        timeout in seconds for server requests, passed to
        `RoutingClient( "eida-routing" ).get_stations()`
    eia_min_num_networks : int [80]
        minimum number of networks in new inventory to accept it 
    reference_networks : list of str []
        list of reference networks, that must be present to accept
        the automatic inventory from service 
    exclude_networks : list of str []
        list of networks to exclude from selection for data request.
        Can be e.g. non-european networks that are available through
        the Eida-routing client; or very small or temporary networks
    large_networks : dict
        indicate probability for selection for specific networks.
        E.g. set `large_networks = {'NL':0.5}` to reduce probability
        for selecting a station from network 'NL'
    inv_update_waittime : int [3600]
        seconds to wait until update of inventory from service is
        tried again after failure. 
    ignore_missing : bool [False]
        ignore missing reference networks when inventory is 
        updated from service. Useful to create an initial 
        inventory.


    Notes
    --------
    - *Channels*: 
        ``wanted_channel`` is only used when an inventory
        of metadata is created by the obspy routing client. From
        this inventory a station is selected randomly. Subsequently,
        meta data at response level is requested again specifically
        for the targeted station. From this new meta data, a random
        channel is selected randomly for which data is requested.
        In other words, even if ``wanted_channels`` contains only 
        z-components, data will be requested for other components 
        as well.
    - *reference networks*: 
        These should be large networks, which
        are representative for different servers. If one of these
        networks is missing in the inventory after update from
        service, the cached inventory is used, unless 
        ``ignore_missing=True``. Most likely the
        server which provides this network was not available to
        the routing client at the time of request. Assuming that
        the old inventory is more complete, it is used until a
        successfull update yields all reference networks.
        This may however be problematic at the beginning when no
        cached inventory is available. For this purpose, use
        ``ignore_missing=True``
    - *large networks*: 
        By default, all networks have equal chance
        of 1 to be selected for a data request. However, this may 
        lead to overrepresentation of very large networks in the
        statistics. A common setting might be ``{'NL': 0.5}``.
    - *Meta data (inventory) update*:
        Meta data (names of networks,
        available stations and channels) is obtained using 
        `routing_client.RoutingClient("eida-routing").get_stations() 
        <https://docs.obspy.org/packages/autogen/obspy.clients.fdsn.routing.routing_client.RoutingClient.html#obspy.clients.fdsn.routing.routing_client.RoutingClient/>`_
        from `obspy.clients.fdsn <https://docs.obspy.org/packages/obspy.clients.fdsn.html#module-obspy.clients.fdsn/>`_
        We ask regularly (``maxcacheage``) for all meta data at channel level 
        (i.e. network, station
        and channel names). The inventory is stored as ``chanlist_cache.pickle``
        in the output directory. This cached inventory is used until it is
        older than `maxcacheage` seconds. Then a new inventory is requested
        from servive.
        Ideally, all servers contributing to EIDA
        respond and a full inventory of all networks in EIDA is obtained.
        This is approximately tested by checking if all reference networks
        are present. Moreover a minimum number of ``eia_min_num_networks``
        should be present.
        If this is not the case, we reuse the old inventory for now, but
        try to update the inventory from service every 
        ``inv_update_waittime`` seconds. 
        Please choose `inv_update_waittime` and `maxcacheage` carefully
        since these routing requests place a significant
        load in the servers and should not be called more often than 
        necessary.
    """

    def __init__( self, eia_datapath=None, 
                 wanted_channels=('HHZ', 'BHZ', 'EHZ', 'SHZ'),
                 eia_global_timespan_days=365, maxcacheage=5*86400,
                 minreqlen=60, maxreqlen=600, eia_timeout=60,
                 eia_min_num_networks=80, 
                 reference_networks=[], exclude_networks=[], 
                 large_networks={},
                 inv_update_waittime=3600, 
                 ignore_missing=False):


        self.logger = logging.getLogger(module_logger.name+'.EidaAvailability')
        self.logger.setLevel(logging.DEBUG)
        self.logger.debug("logger of EidaAvailability is called %s" %
                            self.logger.name)

        self.wanted_channels = wanted_channels
        self.global_span = (UTCDateTime()-86400*eia_global_timespan_days, 
                            UTCDateTime())
        
        self.maxcacheage = maxcacheage
        self.minreqlen = minreqlen
        self.maxreqlen = maxreqlen

        self.eia_timeout = eia_timeout
        self.eia_min_num_networks = eia_min_num_networks
        self.reference_networks = reference_networks
        self.exclude_networks = exclude_networks
        self.large_networks = large_networks

        self.eia_datapath = self._check_path(eia_datapath,
                                            'eia_datapath')
        
        self.slist_cache = os.path.join(self.eia_datapath, 'chanlist_cache.pickle' )
        self.roc = RoutingClient( "eida-routing" )
        self.meta_time = None
        self.wave_time = None
        self.status = None
        self.requestpar = None
        self.trymgr = RetryManager( 'eidainventory', inv_update_waittime )
        # self._check_datapath()
        self.ignore_missing = ignore_missing


    def _check_path(self, pname, varname=''):
        """
        Manage path to results.

        Parameters
        --------------
        pname : str
            If ``pname`` is `None`, results are written to
            current working directory.
            If ``pname`` is string, it should be a valid path to 
            a directory. 
        varname : str
            Explanatory text, passed to error and log messages.


        We check for existence of this directory
        and create new one if absent. Expands users and variables
        in path.
        """
        if not isinstance(pname, str) and pname is not None:
            pname = os.getcwd()
            raise UserWarning("%s is not str. Using current working directory." % varname)
        
        if pname is None:
            pname = os.getcwd()
            self.logger.warning("No %s specified. Setting to %s" % (varname, pname))
        else:
            pname = os.path.expanduser(os.path.expandvars(
                os.path.normpath(os.path.abspath(pname))))
            self.logger.debug("%s is %s" % (varname, pname))
            self.logger.debug('Checking for path %s' % pname)
            if not os.path.exists(pname):
                os.makedirs(pname)
                self.logger.info('Created directory %s for results' % pname)
            else:
                self.logger.debug('Results are stored in %s' % pname)

        return pname


    def _get_inventory_from_service( self ):
        """
        Retrieve station inventory from EIDA routing client.
        
        Requests a full inventory of all available networks,
        stations, channels in EIDA.

        Calls:

        .. code-block:: python
        
            slist = RoutingClient( "eida-routing" ).get_stations( 
                level='channel',
                channel=','.join(self.wanted_channels),
                starttime=UTCDateTime()-86400*eia_global_timespan_days, 
                endtime=UTCDateTime(),
                timeout=self.eia_timeout, includerestricted=False )


        Returns
        -------------
        obspy inventory or None

        
        If total number of networks in ``slist`` 
        is > ``eia_min_num_networks`` and no networks from 
        ``reference_networks`` are missing, the inventory is stored as
        pickle ``'chanlist_cache.pickle'`` to be used by 
        ``_get_inventory_from_cache()``.
        Returns ``None`` if any of the above fails.
        """
        try:
            self.logger.info('updating inventory from service')
            slist = self.roc.get_stations( level='channel',
                channel=','.join(self.wanted_channels),
                starttime=self.global_span[0], endtime=self.global_span[1],
                timeout=self.eia_timeout, includerestricted=False )
        except:
            self.logger.exception( "update of inventory failed, routing service failed" )
            return None
        if self.number_of_networks(slist) < self.eia_min_num_networks:
            self.logger.warning( "update of inventory failed, number of networks %d"
                % self.number_of_networks(slist) )
            return None
        elif self._servers_missing(slist):
            if self.ignore_missing:
                self.logger.warning( "Ignoring missing servers %s " %
                        ','.join(self._servers_missing(slist)) )
            else:
                self.logger.warning( "update of inventory failed, servers missing %s"
                    % ','.join(self._servers_missing(slist)) )
                return None
        fp = open( self.slist_cache, 'wb' )
        pickle.dump( slist, fp )
        fp.close()
        return slist
    

    def _get_inventory_from_cache( self, overrideage=False ):
        """
        Read station inventory from cached pickle 
        ``self.slist_cache``.
        
        Returns ``None`` if 

        - no cached pickle file is found or
        - if file is too old and ``overrideage=False`` (default)
        
        Else inventory is read from file.
        """
        if not os.path.exists(self.slist_cache):
            return None
        fileage = time.time() - os.stat(self.slist_cache).st_mtime
        if fileage > self.maxcacheage and not overrideage:
            return None
        self.logger.info('taking inventory from cache')
        fp = open( self.slist_cache, 'rb' )
        slist = pickle.load( fp )
        fp.close()
        return slist
    

    def get_inventory( self, force_cache=False ):
        """
        Read inventory from cache or from routing client.
        """

        # slist is an inventory object or None
        # _get_inventory_from_cache() checks for existence and 
        # age of file 
        if force_cache:
            slist = self._get_inventory_from_cache(overrideage=True)
            if slist is None:
                self.logger.warning("No inventory in cache")
            else:
                return slist

        if self.trymgr.new_retry():
            slist = self._get_inventory_from_cache()
        else:
            slist = self._get_inventory_from_cache( overrideage=True )
        if slist is None:
            newinv = self._get_inventory_from_service()
            if newinv is None:
                self.trymgr.try_failed()
                return self._get_inventory_from_cache( overrideage=True )
            else:
                return newinv
        return slist
    
    
    def _servers_missing( self, inv ):
        """
        Check inventory ``inv`` for reference networks.
        
        reference networks = main network of each server.
        """
        rnets = inv.get_contents()['networks']
        miss = []
        # self.logger.debug(self.reference_networks)
        for net in self.reference_networks:
            if net not in rnets:
                miss.append( net )
        return miss
    

    def number_of_networks( self, inv ):
        """
        Get number of networks in inventory ``inv``.
        """
        return len(set(inv.get_contents()['networks']))
    

    def select_random_station( self ):
        """
        Select random station from inventory.
        
        Notes
        -------
        - Calls ``get_inventory()``
        - Uses ``self.large_networks()``
        """
        slist = self.get_inventory()
        stalist = list( set(slist.get_contents()['stations']) )
        while True:
            try:
                selsta = stalist[np.random.randint(0,len(stalist))].split()[0]
                net, sta = selsta.split('.')
            except:
                continue
            if net in self.large_networks.keys():
                # Throw dice to scale down probability
                if np.random.random() > self.large_networks[net]:
                    continue
            # Accept only operating stations in networks not excluded.
            if net not in self.exclude_networks and self.is_operating(slist,net,sta):
                break
        return selsta
    

    def is_operating( self, fullinv, network, station ):
        """
        Check in inventory if station is currently operating.

        Parameters
        -----------------------
        fullinv : obspy inventory
            inventory (usually the full Eida inventory
            obtained from cache or routing client)
        network : str
        station : str
        """
        selinv = fullinv.select( network=network, station=station )
        if len(selinv) < 1:
            return False
        now = UTCDateTime()
        for episode in selinv[0]:
            if episode.end_date is None or episode.end_date > now:
                return True
        return False
    
    def _get_random_request_length( self ):
        randspan = self.maxreqlen - self.minreqlen
        return self.minreqlen + np.random.randint(0,randspan)
    
    def _get_random_request_interval( self ):
        reqspan = self._get_random_request_length()
        totalspan = int( self.global_span[1] - self.global_span[0] )
        totalspan -= reqspan
        randstart = self.global_span[0] + np.random.randint(0,totalspan)
        randend = randstart + reqspan
        return (randstart,randend)
    

    def get_station_meta( self, netsta, reqspan ):
        """
        Retrieve full inventory including response of selected station.

        Parameters
        ----------------
        netsta : str
            network and station as `net.sta`
        reqspan : list-like, len=2
            start and end time for request interval
        """
        net, sta = netsta.split('.')
        try:
            self.logger.debug("Requesting meta data for %s" % netsta)
            stamp = time.time()
            inv = self.roc.get_stations( level='response', network=net,
                station=sta, starttime=reqspan[0], endtime=reqspan[1],
                timeout=self.eia_timeout )
            self.meta_time = time.time() - stamp
        except Exception as e:
            self.logger.exception( "requesting inventory for %s failed"
                % netsta)
            self.status = statuscodes.STATUS_NOSERV
            self.logresult( e, netsta, reqspan )
            return None
        return inv
    

    def select_random_station_channel( self, stainv, infotext='' ):
        """
        Randomly select channel from station inventory.

        Parameters
        -------------------
        stainv : obspy inventory
        infotext : str
            passed to logger message
        """
        
        self.logger.debug("Selecting random channel")
        wchan = [c[0:2] for c in self.wanted_channels]
        sellist = []
        for chan in set(stainv.get_contents()['channels']):
            curchan = chan.split('.')[-1]
            if curchan[0:2] in wchan:
                sellist.append( chan )
        if len(sellist) == 0:
            cont = stainv.get_contents()
            self.logger.warning( "channel selection failed (%s): %s"
                % (infotext,repr(cont['channels'])) )
            return None
        return sellist[np.random.randint(0,len(sellist))]
    

    def random_request( self ):
        """
        Create random request parameters and return them.
        
        This is one of the main workers. It selects a random
        station, chooses an interval for the request,
        collects station meta data, randomly selects a
        channel from meta data and returns all as variables.
        Also available as ``self.requestpar``.

        Returns ``None`` at any point where no info is found.

        Returns
        ----------
        selchan, stainv, reqspan or None


        Collective call of 

        - ``self.select_random_station()``
        - ``self._get_random_request_interval()``
        - ``self.get_station_meta( sta, reqspan )``
        - ``select_random_station_channel( stainv, infotext )``
        """

        ## For constency, shouldn't these methods either all start
        ## with _ or none of them?
        self.logger.debug('Selecting random station')
        sta = self.select_random_station()
        reqspan = self._get_random_request_interval()
        stainv = self.get_station_meta( sta, reqspan )
        if stainv is None:
            return None  # Metadata request failed, error set above
        if stainv.get_contents()['channels'] == []:
            return None  # Station closed, no error
        infotext = "%s-%s" % (sta,reqspan[0].strftime('%y%m%d'))
        selchan = self.select_random_station_channel( stainv, infotext )
        if selchan is None:
            return None
        self.requestpar = (sta, selchan, stainv, reqspan)
        return (selchan,stainv,reqspan)
    

    def process_request( self, channel, stainv, reqspan ):
        ## `station` is never used!!! (JL)
        """
        Retrieve and evaluate waveform data, result is a status code.
        
        Second main worker. Takes output of `random_request()` and 
        executes the request.

        Status codes are stored in `self.status`. At the end, this 
        info is written to a log file.

        Parameters
        --------------
        Takes output of ``random_request()``.
        station : 
            not used
        channel : str
            string giving 'network.station.location.channel'
        stainv : inventory
            corresponding inventory
        reqspan : list-like, len 2
            start and end time

        Returns
        ---------
        status, meta_time, wave_time

        """
        net, sta, loc, chan = channel.split('.')
        ## Try to collect requested waveform snippet
        try:
            self.logger.debug("Requesting waveform data for %s" % channel)
            stamp = time.time()
            st = self.roc.get_waveforms( network=net, station=sta, location=loc,
                channel=chan, starttime=reqspan[0], endtime=reqspan[1] )
            self.wave_time = time.time() - stamp
        except Exception as e:
            self.logger.warning( "requesting waveforms for %s failed with %s"
                % (channel,repr(e)))
            st = None
        
        ## Process outcome of waveform request. We want a 
        # single trace (1 channel of 1 station without gaps (len(traces)>1))
        if st is None:
            status = statuscodes.STATUS_NODATA
        else:
            if len(st) < 1:
                status = statuscodes.STATUS_NODATA
            elif len(st) > 1:
                status = statuscodes.STATUS_FRAGMENT
            else:
                trc = st[0]
                reqlen = reqspan[1] - reqspan[0]
                trc.trim( *reqspan )
                datalen = trc.stats.delta * len(trc.data)
                
                # Did we get the whole requested time window?
                if (datalen/reqlen) < 0.99:  # FR&G&RD deliver only 0.99, why? (KS)
                    status = statuscodes.STATUS_INCOMPLETE
                    self.logger.warning( "incomplete: %s (data:%4.2f,req:%4.2f)" % (
                        channel,datalen,reqlen) )
                else: # If yes, try restitution
                    try:
                        self.logger.debug('trying to remove response')
                        trc.remove_response( inventory=stainv )
                        restfailed = False
                    except:
                        restfailed = True
                    if restfailed:
                        self.logger.debug('response removal failed!')
                        status = statuscodes.STATUS_RESTFAIL
                    else:
                        self.logger.debug('response removal succeeded!')
                        if (trc.data[0] != trc.data[0]): # How is this possible (JL)
                            status = statuscodes.STATUS_METAFAIL
                        else:
                            status = statuscodes.STATUS_OK
        self.status = status
        self.logresult()
        return (status,self.meta_time,self.wave_time)
    
    def logresult( self, exc=None, sta=None, reqspan=None ):
        """
        Write result of request into a file database.
        
        Called by 
        - ``process_request()`` to store request result
        - ``get_station_meta()`` 
        """
        if self.requestpar is None:
            netsta = sta
            try:
                reqstart, reqend = reqspan
            except:
                reqstart = None
                reqend = None
            channel = 'unknown'
        else:
            netsta = self.requestpar[0]
            reqstart, reqend = self.requestpar[-1]
            channel = self.requestpar[1]
        net, sta = netsta.split('.')
        outpath = os.path.join( self.eia_datapath, 'log', net, sta )
        if not os.path.exists(outpath):
            os.makedirs( outpath )
        year = datetime.datetime.now().year
        outfile = os.path.join( outpath, "%d_%s.dat" % (year,netsta) )
        ctimestr = datetime.datetime.now().strftime("%Y%m%d_%H%M")
        if reqstart is None:
            rtimestr = '--------_----'
            reqlen = 0.
        else:
            rtimestr = reqstart.strftime("%Y%m%d_%H%M")
            reqlen = (reqend - reqstart) / 60.
        if self.meta_time is None:
            mtimestr = "    -"
        else:
            mtimestr = "%5.1f" % self.meta_time
        if self.wave_time is None:
            wtimestr = "    -"
        else:
            wtimestr = "%5.1f" % self.wave_time
        fp = open( outfile, 'a' )
        if exc is None:
            fp.write( "%s %-8s %s %5.2f %-15s %s %s\n" % (ctimestr,
                statuscodes.error_names[self.status],rtimestr,reqlen,channel,mtimestr,
                wtimestr) )
        else:
            fp.write( "%s %-8s %s %5.2f %-15s %s\n" % (ctimestr,
                statuscodes.error_names[self.status],rtimestr,reqlen,channel,repr(exc)) )
        fp.close()
    
    

#-------------------------------------------------------------------------------



#-------------------------------------------------------------------------------


class DoubleProcessCheck:
    """
    Check if a process is already running.

    Process id is stored in a temporary file 
    while program is running.
    """

    def __init__( self, maxage=300 ):
        self.logger = logging.getLogger(module_logger.name+'.DoubleProcessCheck')
        self.logger.setLevel(logging.DEBUG)
        self.pidfile = os.path.join(tempfile.gettempdir(), 'EidaAvailability.pid')
        self.logger.debug("Pid file is in %s" % self.pidfile)
        self.maxage = maxage
    
    def create_pidfile( self ):
        fp = open( self.pidfile, 'w' )
        fp.write( "%d\n" % os.getpid() )
        fp.close()
    
    def process_active( self ):
        if not os.path.exists(self.pidfile):
            return False
        fileage = time.time() - os.stat(self.pidfile).st_mtime
        if fileage < self.maxage:
            return True
        try:
            pid = int( open(self.pidfile).readline().strip() )
        except:
            os.remove( self.pidfile )
            return False
        try:
            #timestr = datetime.datetime.now().strftime("%d-%b-%Y_%T")
            self.logger.info( "killing process %d" % (pid) )
            os.kill( pid, signal.SIGTERM )
            time.sleep( 5 )
            os.kill( pid, signal.SIGKILL )
        except:
            pass
        os.remove( self.pidfile )
        return False
    
    def should_exit( self ):
        """
        True, if instance is up and running. If not, a process file
        is created, returns False. Subsequent calls should return True.
        """
        if self.process_active():
            return True
        self.create_pidfile()
        return False
    
    def release( self ):
        if os.path.exists(self.pidfile):
            os.remove(self.pidfile)


#-------------------------------------------------------------------------------


class RetryManager:
    """
    Manages age of inventory
    """
    def __init__( self, name, waittime=3600 ):
        self.logger = logging.getLogger(module_logger.name+'.RetryManager')
        self.logger.setLevel(logging.DEBUG)
        self.name = name
        self.waittime = float(waittime)
        self.flagfile = os.path.join(tempfile.gettempdir(), 
                                    "retrymanager_%s.flag" % self.name)
    
    def try_failed( self ):
        """ Mark a failed try by touching the flag file. """
        os.system( "touch %s" % self.flagfile )
        self.logger.debug("Retry failed, touching %s" % self.flagfile)
    
    def new_retry( self ):
        """ 
        Return True/False depending on age of flag file. 

        Also try again if no flagfile exists.
        """
        if not os.path.exists(self.flagfile):
            return True
        fileage = time.time() - os.stat(self.flagfile).st_mtime

        # Try again only if file is older than some time. 
        retry = (fileage > self.waittime)
        if retry:
            os.remove( self.flagfile )
        return retry


#-------------------------------------------------------------------------------
def run(configfile, maxage=60, ignore_missing=False): 
    """
    Execute EIDA data availability test using parameters
    from ``configfile``

    - Reads configuration file
    - configures logging handler (error messages and 
        runtime info)
    - initializes ``EidaAvailability``
    - selects a random station from available meta data
      via ``random_request()``
    - requests test data and tries to apply restitution
      via ``process_request()``

    
    Parameters
    ---------------
    configfile : str, path-like
        path and name of configuration file. Passed to
        ``eida_config``
    maxage : int
        does not run if another process is found which 
        started less than ``maxage`` seconds ago.
        Passed to ``DoubleProcessCheck()``
    ignore_missing : bool [False]
        Whether missing reference networks in inventory
        should be ignored when updating from service.
        Helpful to force creation of an initial inventory
        cache.



    Notes
    -----------
    Only runs if no other instance is found (``DoubleProcessCheck()``)
    """ 

    ## Run Check
    pcheck = DoubleProcessCheck(maxage=maxage)
    if pcheck.should_exit():
        pcheck.logger.debug('Another instance is running')
        exit()
    
    config = eida_config.EidaTestConfig(configfile, which='av')
    configure_handlers(logger, **config.loghandlers)
    module_logger.info(10*'-'+'Starting new request'+10*'-')
    
    params = config.get_avtest_dict()
    module_logger.debug("Parameters for EidaAvailability are\n %s" % 
        "\n".join(["\t{} : {}".format(k,str(v)) for k, v in params.items()]))
    
    stamp = time.time()
    eia = EidaAvailability(ignore_missing=ignore_missing, **params)
    rr = eia.random_request()
    if rr is not None:
        eiaresult = eia.process_request( *rr )
        runtime = time.time() - stamp
        eia.logger.info( "status %s %s %3.1fs" % (rr[1], repr(eiaresult), runtime ) )
    else:
        eia.logger.warning('No random station generated')
    pcheck.release()
    #logger.handlers.clear()
    #logging.shutdown()


if __name__ == '__main__':
    print(__doc__)