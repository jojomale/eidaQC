
# Usage

1. as API
2. as command line tool:
    ```
    eida <method> <args> <configfile>
    ```

## Command line options
### Method
- `avail`: run availability test
- `inv`:   run inventory test
- `rep`:   create html and pdf report
- `templ`: create templates of config file 
            and html-style file

### args:
- `avail`: -
- `inv`: <level>
    request level for inventory. Any of
    'network', 'station' or 'channel'
- `rep`: -
- `templ`: -

### configfile:
- methods 'avail', 'inv', 'rep': mandatory,
        path to config file
- method 'templ': optional; file name for default
    file. If not given file name will be 
    "default_config.ini" in current dir.

