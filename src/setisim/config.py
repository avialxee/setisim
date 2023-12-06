# This is a default configuration value file, 
# You can hardcode the following variables

# -------- Telescope ------------------------------
telescope               =   'GMRT'
refant                  =   'C00'
spw                     =   ''
minsnr                  =   3.0
scanlist                =   []
# GOOD_SPECTRAL_WINDOW    =   '0:'

# -------- Sources --------------------------------
science                 =   'B0329+54'
phase_cal               =   '4C39.5'
delay_bandpass_cal      =   '4C39.5'
flux_cal                =   '4C39.5'

# -------- Folders & Files -------------------------
vis                     =   'example.ms'
outdir                  =   'setisim/'                  # all the files and folders followed are located inside this folder
caltables               =   'cal_tables/'
outputimages            =   'output/'
bandpassplots           =   'bandpass/'
gainplots               =   'gain/'
listfile                =   'listobs.txt'
flagfile                =   'flag.txt'
plotfolder              =   'plots/'
imagingdumps            =   'imaging_dumps/'

# -------- Flagging --------------------------------
quackinterval           =   10.0
quackmode               =   'beg'
tfcrop                  =   True
rflag                   =   False
clip                    =   False
clipminmax              =   [0,50]
flagcmd                 =   'FLAG_CMD.txt'
flagsummaryfile         =   'flagsummary.txt'
config = {key: value for key, value in locals().items() if not key.startswith('__')}