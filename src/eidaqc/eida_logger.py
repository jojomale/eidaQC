
import logging
import logging.handlers

def create_logger():
    """
    Manage logging behavior

    Warning
    ---------
    Filenames (and paths probably too) must not contain "." otherwise
    the automatic deletion of backup files does not work

    Notes
    -----------
    - See https://docs.python.org/3/howto/logging.html#logging-basic-tutorial
    - https://docs.python.org/3/howto/logging-cookbook.html#using-logging-in-multiple-modules
    - TimedRotatingFileHandler splits the path and filename base at "." and then
        uses regular expressions
     
    """
    # print("eida_logger NAME", __name__)
    # print("eida_logger PCKG", __package__)
    #print("MODULE", __name__.__module__)

    # Try to get the package name, may not work for python <3.9 versions
    try: 
        if __package__ is None and __name__ != "__main__":
            print("Using name for logger from __name__", __name__)
            loggername = __name__.split('.')[0]
        elif __package__ == "":
            print("Setting loggername to eidaqc")
            loggername = "eidaqc"
        else:
            print("Using name for logger from __package__", __package__)
            loggername = __package__
    except UnboundLocalError:
        print("Error, using ", __name__.split('.')[0])
        loggername = __name__.split('.')[0]
    
    # print("LOGGERNAME", loggername)
     # create main logger
    logger = logging.getLogger(loggername)
    logger.setLevel(logging.DEBUG)

    # Set handler for console if no handler is present
    if not logger.hasHandlers():
        ch = logging.StreamHandler()
        ch.setLevel(logging.DEBUG)  # set level
        cformatter = logging.Formatter('%(asctime)s - %(name)s - %(levelname)s - %(message)s',
                                    datefmt='%y-%m-%d %H:%M:%S')
        ch.setFormatter(cformatter)
        logger.addHandler(ch)
    return logger #, logger_ea, logger_ar, logger_dpc, logger_rm


def configure_handlers(logger, loglevel_console, loglevel_file, eia_tmp_path, 
                        log_timeunit, log_backupcount, log_interval):
    
    # Remove any existing handlers
    for hdl in logger.handlers:
        logger.removeHandler(hdl)

    # Create handlers
    ## console handler
    ch = logging.StreamHandler()
    ch.setLevel(loglevel_console)  # set level

    ## file handler
    fh = logging.handlers.TimedRotatingFileHandler(
            eia_tmp_path + 'eida_availability_log', 
            when=log_timeunit, backupCount=log_backupcount, interval=log_interval)
    fh.setLevel(loglevel_file)
    
    ## create formatter
    cformatter = logging.Formatter('%(asctime)s - %(name)s - %(levelname)s - %(message)s',
                                    datefmt='%y-%m-%d %H:%M:%S')
    hformatter = logging.Formatter('%(asctime)s - %(name)s - %(levelname)s - %(message)s')

    ### add formatter to ch
    ch.setFormatter(cformatter)
    fh.setFormatter(hformatter)

    # add handlers to main logger, if it doesn't has some already.
    # This happens if different modules are used by a script because
    # each one calls create_logger once.
    # We don't need to add the handlers again, messages are propagated
    # up to main logger. Otherwise messages are duplicated.
    #if not logger.hasHandlers():
    logger.addHandler(ch)
    logger.addHandler(fh)

    # Create loggers for each class
    ## We don't need to add the handlers again, messages are propagated
    ## up to main logger
    
    # logger_ea = logging.getLogger(__name__+'.EidaAvailability')
    # logger_ea.setLevel(logging.DEBUG)

    # logger_ar = logging.getLogger(__name__+'.AvailabilityReport')
    # logger_ar.setLevel(logging.DEBUG)

    # logger_dpc = logging.getLogger(__name__+'.DoubleProcessCheck')
    # logger_dpc.setLevel(logging.DEBUG)

    # logger_rm = logging.getLogger(__name__+'.RetryManager')
    # logger_rm.setLevel(logging.DEBUG)
    #logger_ea.addHandler(ch)
    #logger_ea.propagate = False
    #logger_ea.addHandler(fh) 
    logger.info("Find log file at %s" % eia_tmp_path + 
                'EidaAvailability.log')