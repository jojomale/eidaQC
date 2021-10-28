def create_logger(logging_mode):
    """
    Manage logging behavior
    
    Notes
    -----------
    See https://docs.python.org/3/howto/logging.html#logging-basic-tutorial
    """
    

    if logging_mode.lower() == 'installation':
        ## Provide most detailed infos to stdout 
        # logger_name = 'install'
        log_level = logging.DEBUG
        # create console handler
    elif logging_mode.lower() == 'operation':
        ## Provide only warning level output to log-file
        # logger_name = 'operate'
        log_level = logging.INFO
        # Create file handler
        #ch = logging.FileHandler(eia_tmp_path + 'EidaAvailability.log')
        #print("Find log file at %s" % eia_tmp_path + 'EidaAvailability.log')
    else:
        raise RuntimeError("Logging mode unspecified. Choose" + 
                "'installation' or 'operation'.")

     # create logger
    logger = logging.getLogger('eida_availability')
    logger.setLevel(logging.DEBUG)

    # console handler
    console = logging.StreamHandler()
    # set level
    console.setLevel(log_level)

    # create formatter
    formatter = logging.Formatter('%(asctime)s - %(name)s - %(levelname)s - %(message)s')

    # add formatter to ch
    console.setFormatter(formatter)

    # add ch to logger
    logger.addHandler(console)

    return logger