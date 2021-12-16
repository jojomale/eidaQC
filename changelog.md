# Version 1.0.0
- Command line arguments are parsed using argparse rather
  than by evaluating sys.argv --> new syntax for optional 
  arguments
- Format string of datetimes in output data and reports is
  changed to a purely number-based format 
  DD-MM-YYYY HH:MM:SS.
- In the availability test, when inventory is updated from
  service and reference networks are missing, we now add
  all networks from the cached inventory that are not in the
  new one. This means however, no longer existing or required
  networks will be added as well.