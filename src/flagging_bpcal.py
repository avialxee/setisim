from collections import defaultdict
from casatasks import tclean, split, listobs, plotants, imstat, clearcal, visstat, casalog, flagdata
from casatasks import uvcontsub, flagdata, gencal, plotweather, setjy, gaincal, bandpass, applycal, fluxscale, importgmrt
from casaviewer import imview
from casaplotms import plotms
from pathlib import Path
from casatools import image as IA
from astropy.wcs import WCS
import matplotlib.pyplot as plt
import numpy as np
import io
import base64
from os import path, makedirs, remove, getcwd
import glob
from shutil import rmtree
from matplotlib import rcParams, rc
import os
from casatools import ms, msmetadata

casalog.filter('DEBUG1')
msmd = msmetadata()
# from capturelib import *

def __clear_tmp(wd,cimagename):
    filelist = glob.glob(path.join(wd, cimagename+'.*'))
    for f in filelist:
        try:
            rmtree(f)
        except OSError:
            remove(f)
def save_fig(plt, fig, kind='base64', output='output.jpg'):
    if kind == 'base64':
        buf = io.BytesIO()
        fig.savefig(buf, format='png', bbox_inches='tight',
                    transparent=True, pad_inches=0)
        buf.seek(0)
        string = base64.b64encode(buf.read())
        plt.close()
        return string
    elif kind == 'plot':
        plt.show()
        return 'plotted'
    else :
        if not path.exists('output'):
            makedirs('output')
        newPath = 'output/'+output
        opt = newPath
        if path.exists(newPath):
            numb = 1
            while path.exists(newPath):
                newPath = "{0}_{2}{1}".format(
                    *path.splitext(opt) + (numb,))
                try :
                    if path.exists(newPath):
                        numb += 1 
                except:
                    pass               
        fig.savefig(newPath, format=kind, bbox_inches='tight',
                    pad_inches=0)
        print("saved {}".format(newPath))
        plt.close()
        return newPath
def fetch_sources(vis):
    """
    fetch calibrator and target sources from the measurement set and return dictionary
    """
    pmcalf = '0'
    pmcals = '1'

    bpcalf = '0'
    bpcals = '3'

    fdcalf = '0'
    fdcals = '1'

    targets = '2'
    targetf = '1'

    return {'pmcalf':pmcalf, 'pmcals':pmcals, 
            'bpcalf':bpcalf, 'bpcals':bpcals,
           'fdcalf':fdcalf, 'fdcals':fdcals,
           'targetf':targetf, 'targets':targets
           }

def bandpass_fc(csource, suffix='_init',ref_ant='C00', plotfolder='bp_plots/',fspw = '0:101~1900', 
                outvis='', **kwargs):
    cwd = getcwd()
    if not path.exists(plotfolder):
        try:
            oumask = os.umask(0)
            makedirs(plotfolder)
        finally:
            os.umask(oumask)
#             makedirs(plotfolder, 777)
            
    params={'reset':False, 
            'quackinterval':10.0, 
            'quackmode':'beg', 'bad_antenna':'',
                   }
#     params = defaultdict(lambda: -1, def_params)
    params.update(kwargs)
    if kwargs:
        for k in kwargs:
            if k in params.keys():
                params[k]=kwargs[k]
    if params['reset']:
        flagdata(vis=csource,mode='unflag', field='', spw='', antenna='', timerange='')
        clearcal(vis=csource)

    #### initialize ###########################
    s=fetch_sources(csource)
    
    csource_stem = Path(csource).stem

    ########## bandpass flagging ##############
    
#     plotms(vis=csource, scan=s['bpcals'], antenna=ref_ant, xaxis='freq', iteraxis='scan', yaxis='amp',
#        ydatacolumn='data', plotfile=plotfolder+'amp_v_freq_before_begin.png', title='Before Flagging',
#        coloraxis='baseline',showgui=False)
    flagdata(vis=csource, mode='clip', clipzeros=True, flagbackup=False, action='apply') # clip zero amplitude
    flagdata(vis=csource, mode='shadow', tolerance=0.0, flagbackup=False, action='apply') # shadowing
    flagdata(vis=csource, mode='quack', quackinterval=params['quackinterval'], quackmode=params['quackmode'], 
             flagbackup=False, action='apply')
    flagdata(vis=csource, mode='tfcrop', spw='0', scan='3', datacolumn='data', action='apply', 
             flagbackup=True)
    if params['bad_antenna']:
        flagdata(vis=csource, antenna=params['bad_antenna'],action='apply')

    ###### initial bandpass ##########
    csource_flagged = outvis or csource_stem+f'_scan{s["bpcals"]}_flagged.MS'
    bptab={}
    bptab['Ph_init'], bptab['BP_init']='bp_ph.initPh', 'bp_BP.initBP'
    
    os.system(f'rm -rf {bptab["Ph_init"]} {bptab["BP_init"]}')
    gaincal(vis=csource, caltable=bptab['Ph_init'], 
            selectdata=True, scan=s['bpcals'],
            solint=' int ', spw=fspw, refant=ref_ant, minblperant=3, 
            minsnr=3.0, calmode='p')
#     plotms(vis=bptab['Ph_init'], xaxis='time', yaxis='phase', plotfile=plotfolder+'ph_time_ph_init.png', 
#            showgui=False, iteraxis='spw', antenna=ref_ant, coloraxis='Antenna1')
    bandpass(vis=csource, caltable=bptab['BP_init'],
            field=s['bpcalf'], 
            solint=' inf ', combine='scan', refant=ref_ant, 
            minblperant=3, minsnr=10.0, gaintable=bptab['Ph_init'],
    #          selectdata=True, scan=bpcals,
            interp='nearest', solnorm=False)
#     plotms(vis=bptab["BP_init"],xaxis='freq', yaxis='amp',ydatacolumn='corrected', antenna=ref_ant, 
#         showgui=False, plotfile=plotfolder+f'freq_amp_bp_init_{ref_ant}.png',
#             coloraxis='corr',gridrows=2)
    applycal(vis=csource, gaintable=bptab['BP_init'], calwt=False)
    
    flagdata(vis=csource, mode='rflag', spw='0', datacolumn='corrected', scan=s['bpcals'],
            freqdevscale=2.5, timedevscale=3.5, extendflags=True, action='apply', 
            timeavg=True , flagbackup=True
            )
    flagdata(csource, mode='extend', growfreq=80.0, growtime=60.0, action='apply', extendpols=True)
    print(f'splitting ms....{csource_flagged}')
    split(csource,csource_flagged)

# csource='/home/avi/CASA/imaging/data/TEST2505_B0329_100MHZ_GWB_2.MS'
# kwargs={'bad_antenna':'C03,C08,C09,C10,C11,C14,C06',
#        'quackmode':'beg', 'quackinterval':5.0, 'reset':False}
# bandpass_fc(csource, outvis='test.MS', **kwargs)