# setisim
a python based package for Synthesis Imaging using CASA for SETI. Spectral Imaging for uGMRT data

# Installation

```bash
pip install setisim
```

# Development

```bash
pip install -e .[dev]
```

# Usage: 
>[Under Progress]

```bash
usage: setisim [-f FITSFILE] [-t TIMERANGE] [-sec SECONDS] [-F FREQUENCY] [-m MS_FILE] [-n N_CORES] [-rc CONFIG_FILE] [--pipe]
               [--casalogf CASALOGF] [--fitstovis] [--calibrate] [--cc] [--bind] [-h] [-v] [-p {1,2,3...}]

pipeline for SETI Synthesis Imaging

optional arguments:
  --pipe                pipeline mode
  --casalogf CASALOGF   This file is used for storing logs from CASA task run
  -h                    shows this help menu
  -v, --version         shows information on the installed version

input parameters:
  -f FITSFILE, --fitsfile FITSFILE
                        FITS file path
  -t TIMERANGE, --timerange TIMERANGE
                        input timerange for ex: 5:04:12.8~15:04:27.8
  -sec SECONDS, --seconds SECONDS
                        input time interval for ex: 509
  -F FREQUENCY, --frequency FREQUENCY
                        input rest frequency in MHz for ex: 599.934
  -m MS_FILE, --ms-file MS_FILE
                        measurement set(.MS) path
  -n N_CORES, --n-cores N_CORES
                        specify number of cores to use MPI
  -rc CONFIG_FILE, --read-config CONFIG_FILE
                        configuration file for pipeline run

operations:
  --fitstovis           convert fits to visfile, requires -vis and -fits
  --calibrate           calibrate the visibility file
  --cc                  create configuration file from default values
  --bind                bind setisim with your casa path

pipeline_step:
  select calibration options for GMRT, e.g setisim -p 1~3

  -p {1,2,3...}, --pipe-step {1,2,3...}
                        1:init_flag      Initial Flag
                        2:dical  Direction Independent Calibration
```