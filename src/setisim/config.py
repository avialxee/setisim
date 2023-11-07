# This is a default configuration value file, 
# You can hardcode the following variables

# -------- Telescope ------------------------------
telescope               =   'GMRT'
refant                  =   'C00'
# GOOD_SPECTRAL_WINDOW    =   '0:'

# -------- Sources --------------------------------
science                 =   'B0329+54'
phase_cal               =   '4C39.5'
delay_bandpass_cal      =   '4C39.5'
flux_cal                =   '4C39.5'

# -------- Folders & Files -------------------------
setisim_output          =   'setisim/'                  # all the files and folders followed are located inside this folder
cal_tables              =   'cal_tables/'
output_images           =   'output/'
bandpass_plots          =   'bandpass/'
gain_plots              =   'gain/'
listfile                =   'listobs.txt'

# -------- Flagging --------------------------------
quack_interval          =   10.0
quack_mode              =   'beg'
tfcrop                  =   False
rflag                   =   False


config = {key: value for key, value in locals().items() if not key.startswith('__')}