import configparser
import logging
import os
import tempfile

# https://realpython.com/python-import/#resource-imports
# https://docs.python.org/3/library/importlib.html#module-importlib.resource
from importlib import resources
# from re import T

from obspy.core.utcdatetime import UTCDateTime

from .eida_logger import create_logger
from . import eida_logger

"""
Manage configuration of Eida Network Tests.


To create template file in current working directory 
use command line:

    ```
    python -m eidaqc.eida_config eidaqc/eida_config.py
    ```

or call `create_default_configfile()` in Python script.

- Maybe this module could also manage verifying and
  initializing files and directories
- 
"""

# Initialize logger
logger = create_logger()
module_logger = logging.getLogger(logger.name+'.eida_config')
module_logger.setLevel(logging.DEBUG)


class EidaTestConfig():
    def __init__(self, configfile, which=None):
        
        configfile = expandpath(configfile)

        # Check if file exists
        # If not raise FileNotFoundError 
        # (otherwise config parser opens an empty file 
        # and raises KeyErrors which is very confusing)
        if not os.path.isfile(configfile):
            raise FileNotFoundError("No config-file %s " % 
                    configfile)

                    
        self.config = configparser.ConfigParser()


        self.config.read(configfile)
        # print(['{}:{}'.format(k, str(v)) for k, v in 
        #         self.config.items()])
        self.paths = self.get_paths()
        self.loghandlers = self.get_logging_handlers()
        
        if which is None:
            which = "invavrep"
        elif not any(["inv" in which, "av" in which, "rep" in which]):
            raise RuntimeError('`which` in EidaTestConfig() is not' +
                                ' specified correctly.')
        if "inv" in which.lower():
            self.invtest = self.get_invtest()
        if "av" in which.lower():
            self.avtest = self.get_avtest()
        if "rep" in which.lower():
            self.invtest = self.get_invtest()
            self.avtest = self.get_avtest()
            self.report = self.get_report()
        

    def get_logging_handlers(self):
        """
        Retrieve logger-related settings.

        Checks if `eia_tmp_path` exists. If it doesn't
        uses current working dir instead.
        """

        sec = self.config["ERROR LOGGING"]
        params = {'loglevel_console': sec.get('loglevel_console').upper(),
                    'loglevel_file': sec.get('loglevel_file').upper(),
                    'log_timeunit': sec.get('log_timeunit'),
                    'log_interval': sec.getint('log_interval'),
                    'log_backupcount': sec.getint('log_backupcount'),
                    'eia_tmp_path': self.paths['eia_tmp_path']
        }

        if not os.path.isdir(params['eia_tmp_path']):
            module_logger.warn("given eia_tmp_path " + 
                    "%s " % params['eia_tmp_path'] + 
                    "is not a valid directory! Using " + 
                    "current working directory instead")
            params['eia_tmp_path'] = os.getcwd()
        return params


    def get_paths(self):
        """
        Process paths section

        TODO: Paths could be tested here instead by 
        each module separately
        """
        #print(self.config["PATHS"])
        sec = self.config["PATHS"]
        
        params = {'eia_tmp_path': sec.get('eia_tmp_path'),
                  'eia_datapath': sec.get('eia_datapath'),
        }
        return params


    def get_invtest(self):
        sec = self.config["Inventory test"]
        params = {
            'timeout': sec.getint("timeout"),
            # 'eida_servers': self._split_ignoring_whitespace(
            #                 sec.get("eida_servers")),
            'endtime': self.get_datetime(sec.get("endtime")),
            'rotate_log_at': sec.get("rotate_log_at"),
            'rotate_log_at_time': self.get_time(
                        sec.get("rotate_log_at_time")),
            'inv_log_bckp_count': sec.getint("inv_log_bckp_count"),
            'granularity': sec.getint("granularity")
        }
        params.update(self.get_networks())        
        params.update({'starttime': self.get_datetime(sec.get("starttime"), 
                                                    params["endtime"]),})        
        params.update({"ref_networks_servers": 
                        self.get_networks_servers()})
        return params


    def get_avtest(self):
        sec = self.config["Availability Test"]
        params= {
            #'global_span': sec.getint("global_span"),
            'maxcacheage': sec.getint("maxcacheage"),
            'minreqlen': sec.getint("minreqlen"),
            'maxreqlen': sec.getint("maxreqlen"),
            'eia_global_timespan_days': sec.getint(
                "eia_global_timespan_days"),
            'eia_timeout': sec.getint("eia_timeout"),
            'eia_min_num_networks': sec.getint("eia_min_num_networks"),
            'inv_update_waittime': sec.getint("inv_update_waittime")
        }
        params.update(self.get_networks())

        return params

    def get_report(self):
        sec = self.config["Report"]
        params = {
            'eia_reqstats_timespan_days': sec.getint(
                "eia_reqstats_timespan_days"),
            'eia_cssfile': sec.get('eia_cssfile'),
            'inv_rep_timespan_days' : sec.getint("inv_rep_timespan_days"),
            'reportbase' : os.path.splitext(
                        expandpath(sec.get("reportfile")))[0],
            'granularity' : sec.getint('granularity')
        }
        return params

    def get_networks(self):
        sec = self.config["NETWORKS"]
        params = {
            'wanted_channels': self._split_ignoring_whitespace(
                                sec.get("wanted_channels")),
            'reference_networks': list(self.get_networks_servers().keys()),
            'exclude_networks': self._split_ignoring_whitespace(
                            sec.get("exclude_networks")),
        }
        return params


    def get_networks_servers(self):
        p = self.config["SERVER_REFERENCE_NETWORKS"]
        return {k.upper(): v for k,v in p.items()}


    def get_datetime(self, t, t0=None):
        """
        Convert time string into UTCDateTime.

        - if t is "now", current time is returned
        - if t is a string that can be handled by UTCDateTime,
            returns given datetime
        - if t is numeric and t0 as UTCDateTime is present,
            returns t0 - t
        
        """
        if t.lower() == "now":
            return UTCDateTime()
        elif t.isnumeric():
            t = int(t)
        else:
            try:
                return UTCDateTime(t)
            except (TypeError, ValueError) as err:
                err("Probably a datetime string was not "+ 
                    "formatted correctly in configfile")
            except:
                raise
        
        if isinstance(t0, UTCDateTime):
            return t0 - t 
        else:
            raise RuntimeError("Need time as UTCDateTime")
        

    def get_time(self, t, msg=""):
        try:
            return UTCDateTime.strptime(t, "%H:%M:%S")
        except ValueError:
            raise ValueError(
                "time data '01:00' of '%s' does not match format '%H:%M:%S'" % 
                msg)
        


    def get_avtest_dict(self):
        params = {k: v for k, v in self.paths.items()}
        params.update(self.avtest)
        params.pop('eia_tmp_path')
        return params

    
    def get_invtest_dict(self):
        params = {k: v for k, v in self.invtest.items()}
        params["datapath"] = self.paths["eia_datapath"]
        
        #params.pop('eia_tmp_path')
        return params



    def _split_ignoring_whitespace(self, s, sep=","):
        """
        Split string at `sep` and remove trailing/leading
        whitespaces around the list elements.
        """
        return [si.strip() for si in s.split(sep)]



def expandpath(p):
    return (os.path.abspath(
                os.path.expanduser(
                    os.path.expandvars(
                        os.path.normpath(p)))))




# Create default config-file

eia_global_timespan_days = 365  # Waveform selections within this day span.
eia_timeout = 60                # Timeout for retrieving station metadata.
eia_datapath = os.path.join( os.getcwd(), 'EidaTest_results' )
eia_min_num_networks = 80       # With uncluderestricted=False.
eia_reqstats_timespan_days = 92 # Request statistics over 3 months back.

# Implementation specific settings for creating reports:
# eia_spec_default_cssfile = "/home/stammler/svn/SzgrfDc/texts/styles/ks.css"

module_path = os.path.dirname(eida_logger.__file__)
eia_spec_default_cssfile = str(resources.files("eidaqc").joinpath("html_report.css"))
eia_tmp_path = tempfile.gettempdir()

# Exclude temporary and not european networks.
exclude_networks = [
    '1N', '1T', '3C', '4H', '5M', '7A', '8C', '9C', '9H', 'XK',
    'XN', 'XT', 'XW', 'YW', 'YZ', 'Z3', 'ZF', 'ZJ', 'ZM', 'ZS',
]
not_european = [
    'AI', 'AW', 'CK', 'CN', 'CX', 'GL', 'IO', 'IQ', 'KC', 'KP', 'MQ',
    'NA', 'ND', 'NU', 'PF', 'WC', 'WI'
]
exclude_networks += not_european

# Reduce probability for selection on large dense networks.
large_networks = {
    'NL' : 0.5,
}

# To check whether all servers responded to channel level full
# EIDA metadata request.
## reference networks are one of the networks that are provided 
## by respective servers. They are representatives.


server_reference_networks = {
    'NL' : 'ODC',
    'GE' : 'GFZ',
    'FR' : 'RESIF',
    'CH' : 'ETH',
    'GR' : 'BGR',
    'BW' : 'LMU',
    'RO' : 'NIEP',
    'KO' : 'KOERI',
    'HL' : 'NOA',
    'NO' : 'http://eida.geo.uib.no', #'UIB/NORSAR',
    'CA' : 'ICGC',
    'IV' : 'INGV',
}

# Create the global logger

loglevel_console = 'DEBUG'
loglevel_file = 'DEBUG'
log_interval = 1
log_timeunit = "H"
log_backupcount = 2


# From EidaAvailability
wanted_channels = ( 'HHZ', 'BHZ', 'EHZ', 'SHZ' )
global_span = ( UTCDateTime()-86400*eia_global_timespan_days,
    UTCDateTime() )
maxcacheage = 5*86400  # Renew inventory file every 5 days
minreqlen = 60         # Waveform request window, minimum length ...
maxreqlen = 600        # ... and maximum length

# from eida_inventory
timeout = 240
# Request interval is last year.
#t2 = UTCDateTime()
#t1 = t2 - 365*86400
t1 = "now"
reqint = 365*86400

# 'get_stations' parameters.
reqlevel = 'network'
invpar = {
        'level'              : reqlevel,
        'channel'            : ','.join(wanted_channels),
        'starttime'          : t1,
        'endtime'            : reqint,
        'includerestricted'  : False,
    }


# NEW variables
inv_update_waittime = 3600
inv_rep_timespan_days = 14  # Timespan in days before now for which inventory test is evaluated
reportfile = "EidaTest_report.md"
granularity = 8  # hours over which inventory results are averaged

# Inventory test log file settings
# We use only 'midnight' and 'W0-6'
rotate_log_at = "midnight"
rotate_log_at_time = "00:00:00"
inv_log_bckp_count = 12


def create_default_configfile(outfile=None):
    """
    Create a config file from default variables.

    - `eia_datapath` is set relative to current work dir.
    - `eia_tmp_path` is set to default temp dir
    - `eia_default_css_file` is copied to cwd or outfile dest.

    """

    if outfile is None:
        outfile = os.path.join(os.getcwd(), "default_config.ini")
    elif isinstance(outfile, str):
        outfile = expandpath(outfile)
    else:
        raise RuntimeError("Give filename as str or set to None")
    outdir = os.path.dirname(outfile)
    module_logger.info("Config template is %s" % outfile)

    # Copy html-style file
    eia_spec_default_cssfile = os.path.join(outdir, 
                                "default_html_template.css")
    load_css_template(eia_spec_default_cssfile)


    config = configparser.ConfigParser()
    section = "NETWORKS"
    config[section] = {}
    config[section]["wanted_channels"] = ", ".join(wanted_channels)
    # config[section]['# representiative networks to check whether all servers' + 
    #     'responded to channel level full' +
    #     'EIDA metadata request\nreference_networks'] = ", ".join(
    #             server_reference_networks.keys())
    config[section]['# networks exclude from testing, e.g. temporary or non-european networks'+
        '\nexclude_networks'] = ", ".join(exclude_networks)
    #config[section]['non_european'] = ", ".join(not_european)

    _large_networks = {k:str(v) for k, v in large_networks.items()}
    config.read_dict({#"# Probability for selection of large dense networks."
                        "PROBABILITIES" : _large_networks})
    config.read_dict({"SERVER_REFERENCE_NETWORKS": 
                    server_reference_networks})


    section = "ERROR LOGGING"
    config[section] = {}
    config[section]["loglevel_console"] = loglevel_console
    config[section]["loglevel_file"] = loglevel_file
    config[section]["# unit of logfile rotation - choose from" + 
                            "\n# S (seconds), M (minutes), H (hours), D (days), midnight)" + 
                            "\nlog_timeunit"] = log_timeunit.lower()
    config[section]["# interval to rotate logfile for units S, M, H, D" + 
                        "\nlog_interval"] = str(log_interval)
    config[section]["# number of logfiles to be kept before oldest one gets deleted"+
                "\nlog_backupcount"] = str(log_backupcount)

    section = "PATHS"
    config[section] = {}
    config[section]["# location of temporary files (error logs, etc)" + 
                    "\neia_tmp_path"] = eia_tmp_path
    config[section]["# location to store results" +
                "\neia_datapath"] = eia_datapath


    section = "Availability Test"
    config[section] = {}
    config[section]["# Select waveforms within the last days" + 
                                    "\neia_global_timespan_days"] = str(eia_global_timespan_days)
    config[section]["# Timeout for retrieving station metadata." + 
                                    "\neia_timeout"] = str(eia_timeout)
    config[section]["# Minimum number of networks to get data before replacing cached inventory." + 
                                    "\neia_min_num_networks"] = str(eia_min_num_networks)
    config[section]["# Age of cached inventory file in seconds. If file is older, inventory is updated" + 
                    "\nmaxcacheage"] = str(maxcacheage)
    config[section]["# minimum length of data for test request, in seconds" +
                    "\nminreqlen"] = str(minreqlen)
    config[section]["# maximum length of data for test request, in seconds" +
                    "\nmaxreqlen"] = str(maxreqlen)
    config[section]["# time to wait until next try if inventory update frm servers failed, in seconds" + 
                    "\ninv_update_waittime"] = str(inv_update_waittime)

    section = "Inventory test"
    config[section] = {}
    config[section]["timeout"]  = str(timeout)
    config[section]["# Endtime of request interval"+
                    "\nendtime"] = t1
    config[section]["# starttime or interval for request, counted backwards from t1 in seconds"+
                    "\nstarttime"] = str(reqint)
    # config[section]["# Servers to ask directly for data (not via RoutingClient)"+
                    # "\neida_servers"] = ", ".join(server_reference_networks.values())#eida_servers)
    config[section]["# Rotate result file at 'midnight' (after 24h) or weekday 'W0-6' (0=Monday)" + 
                    "\nrotate_log_at"] = str(rotate_log_at)
    config[section]["# Time at which rollover occurs (in UTC) " + 
                    "\nrotate_log_at_time"] = str(rotate_log_at_time)
    config[section]["# number of files to keep from the past" + 
                    "\ninv_log_bckp_count"] = str(inv_log_bckp_count)
    

    section = "Report"
    config[section] = {}
    config[section]["# Number of days over which to request statistics for report." + 
                    "\neia_reqstats_timespan_days"] = str(eia_reqstats_timespan_days)
    config[section]["# CSS-style file for html report" + 
                    "\neia_cssfile"] = eia_spec_default_cssfile
    config[section]["# Timespan in days before now for which inventory test is evaluated."+
                    "\ninv_rep_timespan_days"] = str(inv_rep_timespan_days)
    config[section]["# Path and name of report file" +
                    "\nreportfile"] = reportfile
    config[section]["# hours over which inventory results are averaged" +
                    '\ngranularity'] = str(granularity)

    with open(os.path.join(os.getcwd(), outfile), 'w') as cfile:
        config.write(cfile)
    module_logger.info('Creating default config-file in %s' %
                    cfile.name)



# def load_default_config(outfile=None):
#     """
#     Load config template.
#     """
#     if outfile is None:
#         outfile = os.path.join(os.getcwd(), "default_config.ini")
#     elif isinstance(outfile, str):
#         outfile = expandpath(outfile)
#     else:
#         raise RuntimeError("Give filename as str or set to None")

#     module_logger.info("Config template is %s" % outfile)
#     config = configparser.ConfigParser()

#     config.read(str(resources.files("eidaqc").joinpath("config.ini")))

#     # Set paths
#     section = "PATHS"
#     config[section]["# location of temporary files (error logs, etc)" + 
#                 "\neia_tmp_path"] = eia_tmp_path
#     config[section]["# location to store results" +
#                 "\neia_datapath"] = eia_datapath

#     section = "Report"
#     config[section]["# CSS-style file for html report" + 
#                 "\neia_cssfile"] = eia_spec_default_cssfile

#     with open(outfile, 'w') as cfile:
#         config.write(cfile)



def load_css_template(outfile=None):
    if outfile is None:
        outfile = os.path.join(os.getcwd(), 
                    "default_html_report.css")
    elif isinstance(outfile, str):
        outfile = expandpath(outfile)
    else:
        raise RuntimeError("Give filename as str or set to None")

    with open(outfile, 'w') as f:
        with resources.open_text("eidaqc", "html_report.css") as rp:
            for l in rp.readlines():
                f.write(l)



if __name__=="__main__":
    create_default_configfile()