#!/bin/bash/

# Call as:
# $ run_eida_avail <prg>
# <prg> can be `avail`, `inv` or `rep`

# Path to config file
configfile=~/Work/config_eidatests.ini
invlevel="channel"
echo "running eida test with "$configfile

# Activate conda environment with eidaqc
source ~/miniconda3/etc/profile.d/conda.sh
conda activate eidaQC

# Run CLI
if [ $1 == "avail" ]; then
eida avail $configfile
elif [ $1 == "inv" ]; then
eida inv $invlevel $configfile
elif [ $1 == "rep" ]; then
eida rep $configfile
else
echo "Unknown argument" $1
fi

# Deactivate conda again
conda deactivate