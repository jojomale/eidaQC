"""
Definitions of status codes for EIDA network
"""

TIMEFMT = "%d-%m-%Y_%H:%M"


# Status codes
STATUS_OK = 0
STATUS_NOSERV = 1
STATUS_METAFAIL = 2
STATUS_NODATA = 3
STATUS_FRAGMENT = 4
STATUS_INCOMPLETE = 5
STATUS_RESTFAIL = 6

# Names of status codes
error_names = {
    STATUS_OK         : 'OK',
    STATUS_NOSERV     : 'NOSERV',
    STATUS_METAFAIL   : 'METAFAIL',
    STATUS_NODATA     : 'NODATA',
    STATUS_FRAGMENT   : 'FRAGMENT',
    STATUS_INCOMPLETE : 'INCOMPL',
    STATUS_RESTFAIL   : 'RESTFAIL',
}

REFERENCE_NETWORKS = {
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