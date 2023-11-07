# This is a default configuration value file, 
# You can hardcode the following variables

# -------- Telescope ------------------------------
telescope               =   'GMRT'
refant                  =   'C00'
spw                     =   ''
minsnr                  =   5.0
# GOOD_SPECTRAL_WINDOW    =   '0:'

# -------- Sources --------------------------------
science                 =   'B0329+54'
phase_cal               =   '4C39.5'
delay_bandpass_cal      =   '4C39.5'
flux_cal                =   '4C39.5'

# -------- Folders & Files -------------------------
vis                     =   'example.ms'
setisim_output          =   'setisim/'                  # all the files and folders followed are located inside this folder
cal_tables              =   'cal_tables/'
output_images           =   'output/'
bandpass_plots          =   'bandpass/'
gain_plots              =   'gain/'
listfile                =   'listobs.txt'
flagfile                =   'flag.txt'
# -------- Flagging --------------------------------
quackinterval           =   10.0
quackmode               =   'beg'
tfcrop                  =   False
rflag                   =   False
clipminmax              =   [0,50]

config = {key: value for key, value in locals().items() if not key.startswith('__')}