# setisim
A python based package for Synthesis Imaging using CASA for SETI. Spectral Imaging for uGMRT data

# Installation

After downloading the repository and unzip (or clone) to the desired folder.

```bash
cd setisim
pip install .
```

# Development

Please report any bug or issues on Github.

```bash
pip install -e .[dev]
```

# Usage: 


```bash
usage: setisim [-f FITSFILE] [-t TIMERANGE] [-sec SECONDS] [-F FREQUENCY] [-m MS_FILE] [-n N_CORES] [-rc CONFIG_FILE]
               [--iname INAME] [--pipe] [--casalogf CASALOGF] [--fitstovis] [--calibrate] [--cc] [--bind] [--debug] [-h] [-v]
               [-p {1,2,3...}]

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
  --iname INAME         imagename after tclean can be used with pipeline step for imaging.

operations:
  --fitstovis           convert fits to visfile, requires --ms-file and --fitsfile
  --calibrate           calibrate the visibility file
  --cc                  create configuration file from default values
  --bind                bind setisim with your casa path
  --debug               Show Parameters used for debugging

pipeline_step:
  select calibration options for GMRT, e.g setisim -p 0~3

  -p {1,2,3...}, --pipe-step {1,2,3...}
                        0:gen_listobs
                        1:flag_init
                        2:flag_autotfcrop
                        3:flag_fromfile
                        4:cal_setmodel
                        5:cal_direction_independent
                        6:diagnostics
                        7:gen_flagsummary
                        8:split_field
                        9:continuum_subtraction
                        10:selfcal_setmodel
                        11:selfcal_iter
                        12:genimg
```

# Examples

1) For imaging around 781.1MHz

```bash

setisim --frequency 781.1 -n 2 -m calibrated_data.ms

```

2) For imaging around timerange

```bash

setisim --timerange 12:14:00.00~12:14:60.00 -n 2 -m calibrated_data.ms

```

3) Imaging around timerange using timestamp 509s

```bash

setisim --seconds 509 -n 2 -m calibrated_data.ms
```

4) Create Configuration file for giving input values from default values

```bash
setisim --cc
```

5) Post imaging create image manually using pipeline step (i.e `-p 12`)

```bash
setisim -p 12 --iname calibrated_data_gscale_1_2min -n 2
```