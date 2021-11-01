#! /usr/bin/env python
#
# file eida_report.py
#      ===================
#
# K. Stammler, 17-Jun-2020
# J. Lehr, 13-Oct-2021
#
# 

"""
Create report of Eida inventory test and Eida availability test.

For creation of reports, needs 'pandoc' and 'convert' (imagemagick).
This also requires implementation specific code, see variables eia_spec_...

Create report with:

```Python
import EidaAvailability
ar = EidaAvailability.AvailabilityReport()
ar.make_md_report( 'avreport.md' )
pdfreport = ar.make_pdf_report( 'avreport.md' )
```
"""


from __future__ import print_function
import os
import sys
# import time
# import signal
import datetime
# import pickle
import logging
import logging.handlers

# import pkg_resources
# print(pkg_resources.)
# css = pkg_resources.resource_filename("eidaqc", "html_report.css")
# print(css)

# import numpy as np
# from obspy.clients.fdsn import RoutingClient
# from obspy import UTCDateTime
import matplotlib.pyplot as plt
import cartopy.crs as ccrs
import cartopy.feature as cfeature

from .eida_logger import create_logger
from .eida_availability import EidaAvailability
from .eida_inventory import EidaInventory
# Temporyry workaround to get parameter settings from eida_availability
#from .eida_parameters import *
from . import statuscodes


# Create the global logger
logger = create_logger()
module_logger = logging.getLogger(logger.name+'.eida_report')

# Retrieve absolute path to default css-file
module_path = os.path.dirname(statuscodes.__file__)
eia_spec_default_cssfile = os.path.join(module_path, "html_report.css")


class BaseReport():
    """
    Provides utilities to create a report.
    """

    def __init__(self, loggername="BaseReport"):
        self.mdstr = ""
        self.logger = logging.getLogger(module_logger.name+
                            '.'+loggername)
        self.logger.setLevel(logging.DEBUG)
        self.etime = datetime.datetime.now()
        self.etimestr = self.etime.strftime(statuscodes.TIMEFMT)
        self.fp = None
        self.mdfile = None

    def repprint(self, text=""):
        #print(text)
        if not isinstance(text, str):
            text = str(text)
        self.mdstr = self.mdstr + "\n" + text 


    def newpage( self ):
        self.repprint( "\n\n\\newpage\n\n" )


    def dump2mdfile(self, mdfilename, mdstr=None):
        """
        Writes `mdstr` or `self.mdstr` to `mdfilename`.

        Manages also if the file already exists and/or
        is already open for writing. Sets `self.mdfile`
        and `self.fp` to file handler.

        **`self.fp` is not closed!!!*
        """

        if mdstr is None:
            mdstr = self.mdstr

        if self.fp is None:
            self.fp = open(mdfilename, 'w')
            self.logger.debug("Writing to new file %s" % mdfilename)
        elif self.fp.name != mdfilename:
            self.logger.debug("Filename %s is different from the one I used before %s" %
                                (mdfilename, self.fp.name, ))
            self.fp = open(mdfilename, 'w')
            self.logger.debug("Writing to new file %s" % mdfilename)
        elif self.fp.closed:
            self.fp = open(mdfilename, 'a')
            self.logger.debug("Appending to file %s" % mdfilename)
        elif not self.fp.closed:
            ## Just checking if this option works
            self.logger.debug("Writing to still open file")
        self.mdfile = mdfilename
        self.fp.write(mdstr)


    def make_html_report( self, mdfile=None, cssfile=None ):
        """
        Convert markdown to html report using pandoc.

        Parameters
        ----------------------
        mdfile : str or None
            if None we look for self.mdfile which is set after
            self.running dump2mdfile()
        cssfile : str or None
            CSS-style file. If None we use the one in the package
        """
        self.logger.debug("Running 'make_html_report()'")
        mdfile = self._check_mdfile(mdfile)

        if cssfile is None:
            cssfile = eia_spec_default_cssfile
        if not os.path.exists(cssfile):
            raise FileNotFoundError("Could not find given CSS file %s " %
                        cssfile + "Use `cssfile=None` for default style!")
            # self.logger.info( "Need existing css file for HTML output" )
            # self.logger.info( "Specified file '%s' not found" % cssfile )
            #return

        htmlfile = os.path.splitext(mdfile)[0] + '.html'
        htmltitle = "EIDA Test Report"
        shellcmd = "cd %s; pandoc -s -c %s --metadata title='%s' -o %s %s" % (
            os.path.dirname(mdfile),cssfile,htmltitle,htmlfile,mdfile)
        self.logger.debug( "executing shellcmd '%s' " % shellcmd )
        self.logger.info( "Creating HTML file '%s'" % htmlfile )
        os.system( shellcmd )
        self.logger.info("Finished HTML-Report")
        return htmlfile
        

    def make_pdf_report( self, mdfile=None, pdfengine="pdflatex"):
        """
        Convert markdown report to pdf via pandoc.

        Pandoc and a valid pandoc pdf-engine and the necessary
        latex packages must be installed. 
        See https://pandoc.org/MANUAL.html#creating-a-pdf

        On Ubuntu you may use e.g. the texlive-latex-extra package
        (info updated 10/2021):
            ```
            apt install texlive-latex-extra
            ```
        Smaller texlive versions do not ship all necessary latex
        packages.


        Parameters
        ---------------
        mdfile : str or None
            if None, we use self.mdfile which is set after running
            self.dump2mdfile()
        pdfengine : str
            passed to pandoc flag --pdf-engine.
        """
        self.logger.debug("Running 'make_pdf_report()'")
        mdfile = self._check_mdfile(mdfile)

        pdffile = os.path.splitext(mdfile)[0] + '.pdf'
        shellcmd = "pandoc -V papersize=a4 " \
            +"-V mainfont=Verdana "\
            +"-V fontsize=10pt --pdf-engine %s " % (pdfengine) \
            +"-o %s %s" % (pdffile,mdfile)
        # alternative fonts: Verdana, NimbusSanL-Regu
        self.logger.debug( "executing shellcmd '%s' " % shellcmd )
        self.logger.info( "Creating pdf file '%s'" % pdffile )
        os.system( shellcmd )
        return pdffile


    def display_pdf_report( self, pdffile ):
        os.system( "evince %s" % pdffile )
    

    def _legacy_plot_save(self, outfile):
        """
        Original procedure to save plots.

        Seems overly complicated and involves external
        program magic. The main utility seems to be to
        trim the white frame around the figures. This
        can be achieved internally with pyplot by setting
        `plt.savefig(...,bbox_inches="tight")`.
        """
        plt.savefig(outfile)
        tmpfile = os.path.join( os.path.dirname(outfile),
            'xxx_'+os.path.basename(outfile) )
        shellcmd = "convert %s -trim %s; mv %s %s" % (outfile,
            tmpfile,tmpfile,outfile)
        self.logger.debug( "executing shellcmd '%s' " % shellcmd )
        os.system( shellcmd )


    def _check_mdfile(self, mdfile):
        if mdfile is None: 
            if self.mdfile is None:
                raise RuntimeError("No md-report available")
            else:
                mdfile = self.mdfile

        if not os.path.isfile(mdfile):
            raise FileNotFoundError("No markdown file %s" 
                            % mdfile)
        mdfile = os.path.abspath(mdfile)
        return mdfile



class AvailabilityReport(BaseReport):
    """
    Create statistics from Eida Availability test results.

    **Most likely, you want to call 
    `AvailabilityReport.results2mdstr()`.**
    
    It creates two matplotlib-figures
    
    - `AvailabilityReport.availability_map` and 
    - `AvailabilityReport.hitplot`

    and a text summary in Markdown available as 
    `AvailabilityReport.mdstr` 

    `mdstr` has two open string formatters, intended to provide
    filenames of the figures as 
        
        ```python
        mdstr % (figfile1, figfile2)
        ```

    We assume that the availability test was run with the same
    parameters as in the config-file for the report. An object
    `eida_availability.EidaAvailability()` is created for the 
    report.

    Notes
    -------------
    - The plotting functions extract and provide vital informations
      for the statistics. A cleaner separation of functionality
      might be helpful.
    """

    # Geometry of map plot.
    mapgeometry = {
        #'projection':  ccrs.Mercator(),
        'lonmin':    -11.,
        'latmin':    29.,
        'lonmax':    50.,
        'latmax':    71.5,
        'resolution':   'i',
        'lat_ts':       45.,
    }
    mapgeometry['projection'] = ccrs.Mercator(
            central_longitude=(mapgeometry['lonmax']-mapgeometry['lonmin'])/2,
            min_latitude=mapgeometry['latmin'],
            max_latitude=mapgeometry['latmax'])
    # Status codes evaluated for color translation in map plot.
    okwords = ('OK',)
    failwords = ('NODATA','FRAGMENT','INCOMPL','METAFAIL','RESTFAIL')
    # Here is the file database.
    

    def __init__( self, config):
        super().__init__("AvailabilityReport")
        
        self.eia = EidaAvailability(**config.get_avtest_dict())
        
        # Path to eia test results
        self.fileroot = os.path.join(self.eia.eia_datapath, 'log' )
        self.inv = self.eia.get_inventory(force_cache=True)
        self.logger.info( "inventory: "
            +"found %d networks, %d stations (with excluded networks)" % (
            len(set(self.inv.get_contents()['networks'])),
            len(set(self.inv.get_contents()['stations']))) )

        self.linecnt = 0
        self.reqstat = {}
        self.netstat = {}
        self.current_network = None
        self.repfp = None
        
        self.stime = self.etime \
            - datetime.timedelta( 
                days=config.report["eia_reqstats_timespan_days"] )
        self.minreqtime = None
        # self.report_outpath = None

    
    def parse_yearfile( self, fname, okcnt, failcnt ):
        """Parse a single file in the file database and return the sum of
        evaluated status codes as well as a location.
        """
        lat = lon = None
        for line in open(fname):
            tmp = line.split()
            if len(tmp) < 2:
                continue
            try:
                reqtime = datetime.datetime.strptime( tmp[0], "%Y%m%d_%H%M" )
            except:
                self.logger.exception( "Error parsing file '%s'" % fname )
                continue
            if reqtime < self.stime:
                # If waveform request is too old, ignore.
                continue
            if self.minreqtime is None or self.minreqtime > reqtime:
                self.minreqtime = reqtime
            keyw = tmp[1]
            if lat is None and len(tmp) > 4:
                chan = tmp[4]
                chan = chan[:-1] + 'Z'
                try:
                    coo = self.inv.get_coordinates( chan )
                except:
                    #if not chan.startswith('unknow'):
                    #    pass
                    continue
                if 'latitude' in coo.keys():
                    lat = coo['latitude']
                if 'longitude' in coo.keys():
                    lon = coo['longitude']
            if keyw in self.okwords:
                okcnt += 1
            elif keyw in self.failwords:
                failcnt += 1
            self.linecnt += 1
            self.add_keyword( keyw )
        return (okcnt,failcnt,lat,lon)

    def add_keyword( self, keyw ):
        """Store status codes for network statistics."""
        if keyw not in statuscodes.error_names.values():
            return
        if not self.current_network in self.netstat.keys():
            self.netstat[self.current_network] = {}
            for errmsg in statuscodes.error_names.values():
                self.netstat[self.current_network][errmsg] = 0
        self.netstat[self.current_network][keyw] += 1

    def parse_years( self, fpath ):
        """Parse all files of a station."""
        okcnt = failcnt = 0
        lincnt = self.linecnt
        for fname in sorted(os.listdir(fpath)):
            fullname = os.path.join( fpath, fname )
            okcnt, failcnt, lat, lon = self.parse_yearfile( fullname,
                okcnt, failcnt )
        if okcnt == 0 and failcnt == 0:
            return (None,None,None)
        okperc = 100. * float(okcnt) / float(okcnt+failcnt)
        self.add_stats( self.linecnt - lincnt )
        return (okperc,lat,lon)
    
    def loop_files( self ):
        """Loop all networks and stations in file database, 
        return availability and location.

        Output is used for plotting
        """
        data = []
        for netdir in sorted(os.listdir(self.fileroot)):
            if len(netdir) != 2:
                continue
            self.current_network = netdir
            stapath = os.path.join( self.fileroot, netdir )
            for stadir in sorted(os.listdir(stapath)):
                fpath = os.path.join( stapath, stadir )
                okperc, lat, lon = self.parse_years( fpath )
                if None in (okperc,lat,lon):
                    continue
                data.append( (okperc,lat,lon) )
        return data
    
    def add_stats( self, cnt ):
        """Hit count statistics, how many stations have how many hits."""
        if not cnt in self.reqstat.keys():
            self.reqstat[cnt] = 0
        self.reqstat[cnt] += 1
    
    def total_number_of_stations( self ):
        """Determine total number of stations, remove double entries and
        stations of excluded networks.
        """
        stalist = []
        double_entries = 0
        for statext in self.inv.get_contents()['stations']:
            netsta = statext.split()[0]
            net, sta = netsta.split('.')
            if net in self.eia.exclude_networks:
                continue
            if netsta in stalist:
                double_entries += 1
            else:
                stalist.append( netsta )
        return (len(stalist),double_entries)
    
    def dump_netstat( self ):
        """ Write networks status statistics in different formats. """
        def print_header( skeys ):
            xkeys = ["`%s`" % k for k in skeys]
            header = '|net ' + ' '.join(["| %10s" % k for k in xkeys]) + ' |'
            self.repprint( '+----+' + '+'.join(len(skeys)*['------------']) + '+' )
            self.repprint( header )
            self.repprint( '+:===+' + '+'.join(len(skeys)*['===========:']) + '+' )
        skeys = sorted( statuscodes.error_names.values() )
        skeys.remove( statuscodes.error_names[statuscodes.STATUS_OK] )
        skeys.remove( statuscodes.error_names[statuscodes.STATUS_NODATA] )
        skeys = [statuscodes.error_names[statuscodes.STATUS_OK],statuscodes.error_names[statuscodes.STATUS_NODATA]] + skeys
        self.newpage()
        tableheader = "Request status statistics of networks"
        maxlen = 45
        for netnum,net in enumerate(sorted(self.netstat.keys())):
            if netnum % maxlen == 0:
                self.repprint( "\n" )
                self.repprint( "\n**%s:**\n" % tableheader )
                if netnum == 0:
                    tableheader += " (continued)"
                print_header( skeys )
            netline = "| %s " % net \
                + ' '.join(["| %10d" % self.netstat[net][k] for k in skeys]) + ' |'
            self.repprint( netline )
        self.repprint( '+----+' + '+'.join(len(skeys)*['----------']) + '+' )
        self.repprint( "\nStatus codes used in above statistics:\n" )
        self.repprint( "`OK`       \n: data delivery and restitution successful\n" )
        self.repprint( "`NODATA`   \n: no data available\n" )
        self.repprint( "`FRAGMENT` \n: returned data not contigous\n" )
        self.repprint( "`INCOMPL`  \n: returned time interval less than requested\n" )
        self.repprint( "`METAFAIL` \n: restituted data contain illegal values (`Nan`s)\n" )
        self.repprint( "`NOSERV`   \n: station metadata request failed\n" )
        self.repprint( "`RESTFAIL` \n: removing response failed\n" )
    

    def makeavailplot( self, outfile=None, mapgeo=None):
        """
        Parameters
        -----------
        outfile : str
            file name
        mapgeo : dict
            same as self.mapgeometry

        Comments (5.10.21)
        ------------------
        - I don't think we need to call scatterplot twice.
            If data is sorted the plot order should be the same
        
        """
        fig = plt.figure( figsize=(14,10) )
        if mapgeo is None:
            mapgeo = self.mapgeometry

        xmap = fig.add_subplot(1,1,1,
                    projection=mapgeo['projection'])
        xmap.set_extent([mapgeo['lonmin'], mapgeo['lonmax'],
                         mapgeo['latmin'], mapgeo['latmax']],
                         crs=ccrs.PlateCarree())
        xmap.add_feature(cfeature.LAND, color='#EEEEFF')
        xmap.add_feature(cfeature.OCEAN)
        xmap.add_feature(cfeature.COASTLINE)
        xmap.add_feature(cfeature.BORDERS, lw=0.25, linestyle='-')
        xmap.add_feature(cfeature.LAKES, alpha=0.5)
        xmap.add_feature(cfeature.RIVERS, lw=0.25)    
        # xmap.drawcoastlines(linewidth=0.25, zorder=3)
        # xmap.drawcountries(linewidth=0.25, zorder=3)
        # xmap.fillcontinents( color='#FFFFFF', lake_color='#EEEEFF', zorder=2 )
        # xmap.drawmapboundary( fill_color='#EEFEFF' )
        data = self.loop_files()
        ##cols, lats, lons = zip( *data )  # plot nice colors at last.
        # Plot first the red dots, then overlain by other colors.
        redcols, redlats, redlons = ([],[],[])
        nonredcols, nonredlats, nonredlons = ([],[],[])
        for col,lat,lon in data:
            if col < 0.1:
                redcols.append( col )
                redlats.append( lat )
                redlons.append( lon )
            else:
                nonredcols.append( col )
                nonredlats.append( lat )
                nonredlons.append( lon )
        xmap.scatter(redlons, redlats, c=redcols, 
                transform=ccrs.PlateCarree(), vmin=0, vmax=100,
                edgecolor=None, cmap='RdYlGn', 
                s=10, zorder=5)
        xmap.scatter(nonredlons, nonredlats, c=nonredcols, 
                transform=ccrs.PlateCarree(), vmin=0, vmax=100,
                edgecolor=None, cmap='RdYlGn', 
                s=10, zorder=6)
        datestr = datetime.datetime.now().strftime("%y-%m-%d")
        plt.title( "EIDA waveform response statistics (%s)" % datestr )
        
        self.availability_map = fig

        if outfile:
            plt.savefig( outfile, format="png", bbox_inches="tight" )
            self.logger.info("Availability map saved as %s" % outfile)
        else:
            plt.show()
        return len(data)
    
    def makehitplot( self, outfile=None ):
        # Legacy: hitstats = self.reqstats
        fig = plt.figure( figsize=(8,6) )
        ax = fig.add_subplot( 111 )
        xvals = sorted( self.reqstat.keys() )
        yvals = [self.reqstat[x] for x in xvals]
        ax.plot( xvals, yvals, c='r' )
        ax.set_xlabel( "number of hits" )
        ax.set_ylabel( "number of stations" )
        self.hitplot = fig
        if outfile:
            plt.savefig( outfile, format="png", bbox_inches="tight" )
            self.logger.info("Hit plot saved as %s" % outfile)
        else:
            plt.show()


    def results2mdstr(self, figfilenames=None, 
                        ):
        """ 
        Create markdown formatted string from results.

        Parameters
        ----------------
        figfilenames: list of 2 str or None
            filenames for the 2 figures 
        """
        
        if figfilenames is None:
            figfilenames = [None, None]

        numstations = self.makeavailplot(outfile=figfilenames[0]) # figfile )
        
        self.makehitplot(outfile=figfilenames[1]) # self.reqstat, figfile2 
        begtime = max( self.minreqtime, self.stime )
        begtimestr = begtime.strftime( "%d-%b-%Y" )
       
        self.repprint( "# EIDA Availability Report\n" )
        self.repprint( "## Created at %s\n" % self.etimestr.replace('_',' ') )
        self.repprint( "This document contains results of automated tests\n"
            +"of the waveform availability of European EIDA stations and the\n"
            +"responsiveness of the EIDA servers to metadata requests.\n"
            )

        self.repprint( "## Description of waveform test program" )
        self.repprint( __doc__ )
        self.repprint( "\n## Statistics on waveform tests\n" )
        self.repprint( "Statistics on random requests between %s and %s" % (
            begtimestr,self.etimestr.replace('_',' ')) )
        self.repprint( "using station metadata valid since %s.\n" % 
            (datetime.datetime.now()-datetime.timedelta(days=365)).strftime("%d-%b-%Y") )
        totstations, doublesta = self.total_number_of_stations()
        self.repprint( "\n**Counters:**\n" )
        self.repprint( "- unrestricted stations offering channels `%s`: %d"
            % (','.join(self.eia.wanted_channels),totstations) )
        self.repprint( "- evaluated stations: %d" % numstations )
        self.repprint( "- number of requests: %d" % self.linecnt )
        self.newpage()

        self.repprint( "## Waveform availability plot\n" )
        self.repprint( "Color coded plot of evaluated EIDA stations. " )
        self.repprint( "Shows results of %d random requests between %s and %s."
            % (self.linecnt,begtimestr,self.etimestr.split('_')[0]) )
        self.repprint( "The availability displayed is computed as the relative number\n"
            +"of request results with status `OK` (see table below) compared\n"
            +"to the number of all requests to this station.\n"
        )
        self.repprint( "![Availability of stations: green 100%%, yellow 50%%, "\
            +"red 0%%](%s){width=100%%}" % figfilenames[0] #os.path.basename(figfile) 
            )
        self.newpage()
        
        #self.repprint( "## Network statistics\n" )
        self.dump_netstat()
        self.newpage()

        self.repprint( "\n## Waveform requests, random hit distribution\n" )
        self.repprint( "How many stations have how many hits of random " )
        self.repprint( "requests.\n" )
        #self.repprint( "  No. of hits   Stations with this number of hits" )
        #self.repprint( "-------------   -----------------------------------------------" )
        #for k in sorted(self.reqstat.keys()):
        #    self.repprint( "       %4d    %4d" % (k,self.reqstat[k]) )
        self.repprint( "![Request hit statistics showing the distribution of "
            +"the %d requests on the %d evaluated stations]"
            % (self.linecnt,numstations) +
            "(%s){width=100%%}" % figfilenames[1]#,os.path.basename(figfile2)) 
            )
        self.repprint( "\n" )
        self.newpage()



class InventoryReport(BaseReport):
    """
    Evaluate and plot results of inventory test.
    """
    
    def __init__(self, config, reference_networks={}, stime=None) -> None:
        
        super().__init__("InventoryReport")
        self.logger.info("Creating InventoryReport")
        
        self.einv = EidaInventory("network", 
                            **config.get_invtest_dict())

        self.fig = None
        self.reference_networks = reference_networks
        if isinstance(stime, str):
            self.stime = self.parse_time(stime)
        else:
            self.stime = self.etime - datetime.timedelta(
                    days=config.report["inv_rep_timespan_days"])

        self.mdstr = self._mdstrbody()

        self.roclifailures = 0
        self.noerrorcnt = 0
        self.directcnt = 0
        self.routecnt = 1  # first is missed in loop
        self.directfail = {}
        self.routefail = {}
        self.currsrv = None


    def _mdstrbody(self):
        invtest_text = "## Failure rate of inventory requests\n\n" \
            + "This section contains results of inventory test \n" \
            + "requests on network, station and channel level.\n" \
            + "A few times per hour all servers get direct\n" \
            + "metadata requests followed by a metadata request\n" \
            + "using the routing client of obspy. It is checked\n" \
            + "whether all servers respond to the direct requests\n" \
            + "and whether all servers contribute to the routed\n" \
            + "request. The following results refer to tests carried\n" \
            + "out since %s.\n\n" % self.stime.strftime("%d-%b-%Y %T")
        return invtest_text

    
    def _md_add_figure(self, figfile):
        mdfigtext = "\n![Responsiveness of all servers plotted with a " \
            +"granularity of 8h; green = 0% errors, orange = 10%, " \
            +"brown = 50%%, black = 100%%](%s){width=100%%}" % (
            os.path.basename(figfile))
        return mdfigtext


    def results2mdstr(self, respplot=None, mode="normal" ):
        skip = False
        routeactive = False
        missnet = ""
        failedlist = []

        if self.stime and respplot:
            mrp = MetaResponsePlot( self.stime, 8, respplot )
        else:
            mrp = None
       
        # Process content of log file
        with open(self.einv.outfile, 'r') as file:
            self.logger.debug("Reading inventory test results from\n" + 
                            "%s" % self.einv.outfile)
            for line in file.readlines():
                if line.startswith('eida_inventory_test.py started at'):
                    timestr = line.split()[3]
                    currtime = datetime.datetime.strptime( timestr, 
                                        statuscodes.TIMEFMT+':%S' )
                    if self.stime is not None and currtime < self.stime:
                        skip = True
                        continue
                    else:
                        skip = False
                    if mrp:
                        mrp.set_time( currtime )
                    self.directcnt += 1
                    if routeactive:
                        self.routecnt += 1
                        if mrp:
                            mrp.inc_total_count( 'ALL' )
                elif skip:
                    continue
                elif 'reading inventory from server' in line:
                    srv = line.split()[4]
                    if srv == 'http://eida.geo.uib.no':
                        srv = 'UIB/NORSAR'
                    elif srv == 'https://eida.bgr.de':
                        srv = 'BGR'
                    if mrp:
                        mrp.inc_total_count( srv )
                elif 'reading inventory from routing client' in line:
                    srv = None
                elif 'FAILED:' in line:
                    if srv is None:
                        self.roclifailures += 1
                    else:
                        failedlist.append( srv )
                        if mrp:
                            mrp.inc_fail_count( srv )
                elif line.startswith('missing reference networks'):
                    routeactive = True
                    missnet = line.split()[3]
                elif line.startswith('============'):
                    timestr = currtime.strftime( "%d-%b-%Y_%T" )
                    tmissnet = self.transref(missnet)
                    if not failedlist and not missnet:
                        self.noerrorcnt += 1
                    if mode == 'normal':
                        self.repprint( "%s %20s %20s" % (timestr,','.join(failedlist),tmissnet) )
                    self.cumulate_failures( failedlist, tmissnet.split(','), 
                                        self.directfail, self.routefail )
                    if tmissnet and mrp:
                        for srv in tmissnet.split(','):
                            mrp.inc_fail_count( srv )
                    failedlist = []
                    missnet = ""
        
        if mrp: mrp.finish_index()

        self.logger.debug("Direct fails are \n %s" % self.directfail)
        self.logger.debug("Number of direct requests is %3.1f" % self.directcnt  )
        self.repprint( "totals: direct requests %d, routed requests %d" % 
                (self.directcnt, self.routecnt) )
        self.print_failure_rates( self.directfail, self.routefail, self.directcnt, 
            self.routecnt,
            self.noerrorcnt, self.roclifailures, mode )
        if mrp:
            mrp.makeplot()
            self.repprint(self._md_add_figure(mrp.plotname))



    def transref(self, missnet):
        if missnet == '':
            return ''
        srvlist = []
        for net in missnet.split(','):
            srvlist.append( self.reference_networks[net] )
        #if 'ICGC' in srvlist:
        #    srvlist.remove( 'ICGC' )
        return ','.join(sorted(srvlist))

    
    def print_failure_rates(self, directfail, routefail, directcnt, 
                        routecnt, noerrcnt, roclifailures, mode ):
        self.repprint( "\nNumber of failed requests and failure rates of servers:" )
        self.repprint()
        if mode == 'normal':
            self.repprint( "server    direct          routed" )
        else:
            self.repprint()
            self.repprint( "| server  |  direct       |  routed       |" )
            self.repprint( "|--------:|--------------:|--------------:|" )
        for srv in sorted(self.reference_networks.values()):
            #if srv == 'ICGC': continue
            dnum = directfail.get( srv, 0 )
            dperc = 100.0*float(dnum)/float(directcnt)
            rnum = routefail.get( srv, 0 )
            rperc = 100.0*float(rnum)/float(routecnt)
            if mode == 'normal':
                line = " %5s %5d (%4.1f%%)  %5d (%4.1f%%)" % (srv,dnum,dperc,rnum,rperc)
                self.repprint( line )
            else:
                line = "| %5s   | %5d (%4.1f%%) | %5d (%4.1f%%) |" % (srv,dnum,dperc,rnum,rperc)
                self.repprint( line )
        noerrperc = 100.*float(noerrcnt)/float(directcnt)
        self.repprint( "\nfailures of routing client: %d" % roclifailures )
        if mode == 'report':
            self.repprint()
        self.repprint( "runs without errors: %d (%3.1f%%)" % (noerrcnt,noerrperc) )


    def cumulate_failures(self, dfail, rfail, ddict, rdict ):
        for srv in dfail:
            if not srv in ddict.keys():
                ddict[srv] = 0
            ddict[srv] += 1
        for srv in rfail:
            if not srv in rdict.keys():
                rdict[srv] = 0
            rdict[srv] += 1


    def parse_time(self, timestr ):
        try:
            stime = datetime.datetime.strptime( timestr, statuscodes.TIMEFMT )
        except:
            stime = None
        if stime is None:
            try:
                stime = datetime.datetime.strptime( timestr, 
                                    statuscodes.TIMEFMT+":%S" )
            except:
                stime = None
        if stime is None:
            try:
                stime = datetime.datetime.strptime( timestr, "%d-%b-%Y" )
            except:
                stime = None
        return stime




class MetaResponsePlot:

    """Create a plot with response info of all servers."""

    def __init__( self, stime, granularity, plotname ):
        self.stime = stime   # start time of plot, end time is now
        self.granularity = float(granularity)   # in hours
        self.plotname = os.path.abspath(plotname)
        self.totcnt = {}   # counter per server
        self.failcnt = {}  # counter per server
        self.currtime = None
        self.curridx = None
        self.lastidx = None
        self.plotinfo = {}  # dict of dicts
        self.incall_on_none = False
        self.fig = None
    
    def set_time( self, ctime ):
        if ctime == self.currtime:
            return
        self.currtime = ctime
        difftime = ctime - self.stime
        diffsec = difftime.seconds + difftime.days*86400
        self.curridx = int((diffsec/3600.)/self.granularity)
        if self.lastidx != self.curridx:
            self.finish_index()
            self.lastidx = self.curridx
    
    def time_label( self, tm ):
        difftime = tm - self.stime
        diffsec = difftime.seconds + difftime.days*86400
        return ((diffsec/3600.)/self.granularity)
    
    def inc_total_count( self, server ):
        if server == 'ALL':
            if self.totcnt == {}:
                self.incall_on_none = True
            else:
                for k in self.totcnt.keys():
                    self.totcnt[k] += 1
                if self.incall_on_none:
                    for k in self.totcnt.keys():
                        self.totcnt[k] += 1
                    self.incall_on_none = False
            return
        if not server in self.totcnt.keys():
            self.totcnt[server] = 0
        self.totcnt[server] += 1

    def inc_fail_count( self, server ):
        if not server in self.failcnt.keys():
            self.failcnt[server] = 0
        self.failcnt[server] += 1
    
    def finish_index( self ):
        for k in self.totcnt.keys():
            if k in self.failcnt.keys():
                fcnt = self.failcnt[k]
            else:
                fcnt = 0
            if k not in self.plotinfo.keys():
                self.plotinfo[k] = {}
            #if k == 'NIEP':
            #    print( "dbg: fcnt, totcnt", fcnt, self.totcnt[k] )
            self.plotinfo[k][self.curridx] = float(fcnt)/float(self.totcnt[k])
        self.totcnt = {}
        self.failcnt = {}
    
    def makeplot( self ):
        fig = plt.figure( figsize=(8,6) )
        ax = fig.add_subplot( 111 )
        ypos = 0.5
        ylabs = []
        yticks = []
        for srv in sorted(self.plotinfo.keys(),reverse=True):
            for idx in range(min(self.plotinfo[srv]),max(self.plotinfo[srv])+1):
                ax.plot( (idx,idx+0.2), (ypos,ypos), c=self.getcol(srv,idx),
                    linewidth=9 )
            yticks.append( ypos )
            ylabs.append( srv )
            ypos += 0.5
        plt.yticks( yticks, ylabs )
        xtickpos = datetime.datetime( self.stime.year, self.stime.month,
            self.stime.day, 0 ) + datetime.timedelta( days=1 )
        xticks = []
        xlabs = []
        while xtickpos < datetime.datetime.now():
            xticks.append( self.time_label(xtickpos)+1. )
            xlabs.append( xtickpos.strftime("%d-%b") )
            xtickpos += datetime.timedelta( days=4 )
        ax.set_title( "responsitivity to metadata requests (%d)"
            % self.stime.year )
        plt.xticks( xticks, xlabs )
        #plt.show()
        self.fig = fig
        plt.savefig( self.plotname, format="png", bbox_inches="tight" )
    
    def getcol( self, srv, idx ):
        if not srv in self.plotinfo.keys():
            return 'gray'
        elif not idx in self.plotinfo[srv].keys():
            return 'gray'
        val = self.plotinfo[srv][idx]
        col1r = 0.
        col1g = 1.0
        col2r = 1.0
        col2g = 0.5
        col3r = 0.
        col3g = 0.
        thresh1 = 0.1
        if val < thresh1:
            fac = val/thresh1
            colr = col1r + fac * (col2r-col1r)
            colg = col1g + fac * (col2g-col1g)
        else:
            fac = (val-thresh1)/(1.-thresh1)
            colr = col2r + fac * (col3r-col2r)
            colg = col2g + fac * (col3g-col2g)
        xcolr = int(colr * 255)
        xcolg = int(colg * 255)
        return '#%02x%02x00' % (xcolr,xcolg)
    
    def dump( self ):
        print( "dbg: mrp plotinfo:", self.plotinfo )





class EidaTestReport(BaseReport):
    """
    Create report of Eida availability test 
    and inventory test.
    """
    def __init__(self, config) -> None:

        super().__init__("EidaTestReport")

        # self.repfp = None
        self.datapath = config.paths["eia_datapath"]
        
        self.reportbase = config.report['reportbase']
        self.repfile = self.reportbase + ".md"

        self.logger.debug("filebase for output %s" % self.reportbase)
        self.inventory_report = InventoryReport(config,
                    config.get_networks_servers(),
                    #_stime  
                     )
        self.availability_report = AvailabilityReport(config)
        

    def infostr(self):
        """
        Returns text incl. creation time and pandoc version
        """

        text = "\n\n## Remarks\n\n" \
           + "A history of these daily reports (in pdf format)" \
           + "as well as request logs on station level are available at " \
           + "<ftp://www.szgrf.bgr.de/pub/EidaAvailability>," \
           + "files `history_eida_availability_reports.tgz` and " \
           + "`stationlogs_eida_availability.tgz`, respectively." \
           + "\n\nThis report was automatically created at %s MEST using" \
                % self.etimestr.replace('_',' ') \
           + "%s.\n" % os.popen('pandoc --version').readline().strip()
            
        return text


    def make_md_report(self):
        """
        Create markdown file of summary report on
        availability and inventory test.

        - Runs `results2mdstr` on both reports.
        - Runs `dump2mdfile()` on both reports.
        - Adds own info string on creation time
        - names figure files as 
            `self.reportbase_fig123.png`
        """
        
        self.logger.debug("Running 'make_md_report()'")
    
        # Add Availability report
        self.availability_report.results2mdstr(
            [self.reportbase+"_"+f for f in ["fig1.png", "fig2.png"]])

        self.dump2mdfile(self.repfile, self.availability_report.mdstr)
       
        # Add Inventory report
        self.inventory_report.results2mdstr( 
                    mode='report', 
                    respplot=self.reportbase+'_fig3.png')
        self.dump2mdfile(self.repfile, self.inventory_report.mdstr)
       
        # Finale
        self.dump2mdfile(self.repfile, self.infostr())
        self.fp.close()

        self.logger.info("Finished MD-Report")



    def daily_report( self,# outpath=None, 
            pdfengine="pdflatex" ):
        """
        Convenience function to create markdown,
        html and pdf report at once.

        Parameters
        -----------
        pdfengine : str
            see BaseReport.make_pdf_report()
        """
        # if outpath is None:
        #     outpath = os.getcwd()
        # self.report_outpath = outpath
        # repname = "eida_availability_report.md"
        # if outpath:
        #     frepname = os.path.join( outpath, repname )
        # else:
        #     frepname = repname
        self.make_md_report()
        self.make_pdf_report(self.repfile, pdfengine)
        self.make_html_report(self.repfile)
        #os.remove( frepname )


    # def make_html_report( self, mdreport=None, cssfile=None ):
    #     if mdreport is None and self.repfile is None:
    #         raise RuntimeError("No md-report available")

    #     if mdreport is not None:    
    #         mdreport = os.path.abspath(mdreport)
    #     else:
    #         mdreport = self.repfile

    #     if cssfile is None:
    #         cssfile = eia_spec_default_cssfile
    #     if not os.path.exists(cssfile):
    #         self.logger.info( "Need existing css file for HTML output" )
    #         self.logger.info( "Specified file '%s' not found" % cssfile )
    #         return
        
    #     # Why copy the css-file????
    #     # if self.report_outpath:
    #     #     os.system( "cp %s %s/" % (cssfile,self.report_outpath) )
    #     # else:
    #     #     os.system( "cp %s ." % cssfile )
    #     # lcssfile = os.path.basename( cssfile )
    #     htmlfile = os.path.splitext(mdreport)[0] + '.html'
    #     htmltitle = "EIDA Availability Report"
    #     shellcmd = "cd %s; pandoc -s -c %s --metadata title='%s' -o %s %s" % (
    #         os.path.dirname(mdreport),cssfile,htmltitle,htmlfile,mdreport)
    #     self.logger.debug( "executing shellcmd '%s' " % shellcmd )
    #     self.logger.info( "Creating HTML file '%s'" % htmlfile )
    #     os.system( shellcmd )
    #     self.logger.info("Finished HTML-Report")
    #     return htmlfile



    # def repprint( self, text ):
    #     if self.repfp is None:
    #         print( text )
    #     else:
    #         self.repfp.write( "%s\n" % text )


#   self.repprint( "\n\n## Remarks\n\n" )
#         self.repprint( "A history of these daily reports (in pdf format)" )
#         self.repprint( "as well as request logs on station level are available at " )
#         self.repprint( "<ftp://www.szgrf.bgr.de/pub/EidaAvailability>," )
#         self.repprint( "files `history_eida_availability_reports.tgz` and " )
#         self.repprint( "`stationlogs_eida_availability.tgz`, respectively." )
#         self.repprint( "\n\nThis report was automatically created at %s MEST using"
#             % self.etimestr.replace('_',' ') )
#         self.repprint( "%s.\n" % os.popen('pandoc --version').readline().strip() )
        


        # sday = datetime.datetime.now() - datetime.timedelta( days=30 )
        # invtest_report = self.add_inventory_test_report(sday, figfile3 )
        # if invtest_report:
        #     self.newpage()
        #     self.repprint( invtest_report )

        # self.repprint( "\n\n## Remarks\n\n" )
        # self.repprint( "A history of these daily reports (in pdf format)" )
        # self.repprint( "as well as request logs on station level are available at " )
        # self.repprint( "<ftp://www.szgrf.bgr.de/pub/EidaAvailability>," )
        # self.repprint( "files `history_eida_availability_reports.tgz` and " )
        # self.repprint( "`stationlogs_eida_availability.tgz`, respectively." )
        # self.repprint( "\n\nThis report was automatically created at %s MEST using"
        #     % self.etimestr.replace('_',' ') )
        # self.repprint( "%s.\n" % os.popen('pandoc --version').readline().strip() )
        # fp.close()
        # self.reffp = None
    

    # def add_inventory_test_report(self, sday, respfig ):
    #     """
    #     Retrieve statistics on the EIDA inventory test and include it
    #     in the report. 
    #     """
    #     fname = os.path.join(self.eia.eia_datapath, "eida_inventory_test.log")
    #     invtest_data = ""
    #     try:
    #         with open(fname, 'r') as f:
    #             for line in f.readlines():
    #                 invtest_data += "\t"+ line.strip() + "\n"

    #     except FileNotFoundError:
    #         self.logger.warning("Could not find results of inventory test. Looking for %s" 
    #                     % fname)
    #         invtest_text = "## Failure rate of inventory requests\n\n" \
    #                         + "No inventory test results found."
    #         return invtest_text
    #     except:
    #         raise


    #         # self.logger.debug("invtest content %s" % invtest_data)
    #     ## I think this whole section is not necessary 
    #     # if len(invtest_data) < 10:
    #     #     # Should not happen, something with the parsing went wrong.
    #     #     self.logger.warning( "*** Could not parse inventory test logfile. ***" )
    #     #     if os.path.exists(logfilename):
    #     #         # Why would we want to remove this file?
    #     #         #os.remove( logfilename )
    #     #         #self.logger.debug("Removing inventory test results in %s" % logfilename)
    #     #         self.logger.debug("Inventory test result exist but are damaged")
    #     #     else:
    #     #         self.logger.warning("No results of inventory test found. Looking for %s" 
    #     #                 % logfilename)
    #     #     return None
    #     invtest_text = "## Failure rate of inventory requests\n\n" \
    #         + "This section contains results of inventory test \n" \
    #         + "requests on network, station and channel level.\n" \
    #         + "A few times per hour all servers get direct\n" \
    #         + "metadata requests followed by a metadata request\n" \
    #         + "using the routing client of obspy. It is checked\n" \
    #         + "whether all servers respond to the direct requests\n" \
    #         + "and whether all servers contribute to the routed\n" \
    #         + "request. The following results refer to tests carried\n" \
    #         + "out since %s.\n\n" % sday.strftime("%d-%b-%Y %T")
    #     respfigtext = "\n![Responsiveness of all servers plotted with a " \
    #         +"granularity of 8h; green = 0% errors, orange = 10%, " \
    #         +"brown = 50%%, black = 100%%](%s){width=100%%}" % (
    #         os.path.basename(respfig))

    #     ## Why is the logfile removed
    #     #if os.path.exists(logfilename):
    #     #    os.remove( logfilename )
    #     return invtest_text+invtest_data+respfigtext
