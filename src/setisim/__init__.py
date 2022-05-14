import os
import argparse




parser = argparse.ArgumentParser('setisim',description="""SETI synthesis imaging pipeline
""", formatter_class=argparse.RawDescriptionHelpFormatter)
parser.add_argument('-F', '--fitsfilename', type=str, help='input FITS filename')
parser.add_argument('-t', '--timerange', type=str, help='input timerange for ex: 5:04:12.8~15:04:27.8')
parser.add_argument('-ti', '--timeinstant', type=str, help='input time interval for ex: 509')
parser.add_argument('-f', '--frequency', type=float, help='input rest frequency for ex: 599.934021MHz')
parser.add_argument('-p', '--pipe', type=str, nargs='+', default=[''], help='pipeline #')
parser.add_argument('-pp', '--pipeline', type=int, help='pipeline #')
parser.add_argument('-convert', '--fitstovis', type=bool, help='convert fits to visfile')
parser.add_argument('-v', '--visibilityfilename', type=str, help='output visibility measurement set(.MS) filename')
parser.add_argument('-flg', '--flag', type=int, help="""flagging pipeline
1 - init flag
2 - tfcrop independent on each source
3 - bandpass calibrate + rflag""")
args=parser.parse_args()
from casatools import logsink
setisimlog=logsink('setisim.log')
setisimlog.setlogfile='setisim.log'
setisimlog.setglobal(True)


from collections import defaultdict
from casatasks import tclean, split, listobs, plotants, imstat, clearcal, visstat, flagdata, flagmanager
from casatasks import uvcontsub, flagdata, gencal, plotweather, setjy, gaincal, bandpass, applycal, fluxscale, importgmrt
from casaviewer import imview
from casaplotms import plotms
from pathlib import Path
from astropy.wcs import WCS
from astropy.time import Time, TimeDelta 
import matplotlib.pyplot as plt
import numpy as np
import io
import base64
from os import curdir, path, makedirs, remove, getcwd
import glob
from shutil import rmtree
from matplotlib import rcParams, rc
import os
from casatools import ms, msmetadata

# casalog.filter('DEBUG1')
msmd = msmetadata()

from casatools import image as IA
from astropy.wcs import WCS
import matplotlib.pyplot as plt
import numpy as np
import matplotlib.colors as colors
from mpl_toolkits.axes_grid1.anchored_artists import AnchoredSizeBar


def __clear_tmp(wd,cimagename):
    filelist = glob.glob(path.join(wd, cimagename+'*'))
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


def genpng(cimg, chno=0, out='output.jpg', norm_max=None, **kwargs):
    ia = IA()
    ia.open(cimg)
    pix = ia.getchunk()[:,:,0,chno]
    csys = ia.coordsys()
    ia.close()
    
    rad_to_deg =  180/np.pi
    w = WCS(naxis=2)
    w.wcs.crpix = csys.referencepixel()['numeric'][0:2]
    w.wcs.cdelt = csys.increment()['numeric'][0:2]*rad_to_deg
    w.wcs.crval = csys.referencevalue()['numeric'][0:2]*rad_to_deg
    w.wcs.ctype = ['RA---SIN', 'DEC--SIN']
    fig = plt.figure(figsize=(20, 10))
    ax = plt.subplot(1, 1, 1, projection=w)
#     p1 = int(pix.shape[0]*0.25)
#     p2 = int(pix.shape[0]*0.75)

#     im = ax.imshow(pix[p1:p2,p1:p2].transpose(), origin='lower',  cmap=plt.cm.viridis)
    if norm_max:
        try:
            norm_max=float(norm_max)
            im = ax.imshow(pix.transpose(), origin='lower',  
                           cmap=plt.cm.gist_heat, interpolation="lanczos",
                           norm=colors.CenteredNorm(norm_max/2.0)
            )
        except:
            im = ax.imshow(pix.transpose(), origin='lower',  
                           cmap=plt.cm.gist_heat, interpolation="none",
                           norm=colors.CenteredNorm(0.0))
        
    else:
        im = ax.imshow(pix.transpose(), origin='lower',  
                       cmap=plt.cm.gist_heat, interpolation="none",
                    #    norm=colors.CenteredNorm(0.0)
                       )
        
    plt.colorbar(im, ax=ax)
    ax.set_xlabel('Right Ascension')
    ax.set_ylabel('Declination')
    ax.set_title(str(out))
#     ax.add_size_bar(1/3600./f_hst[0].header["cdelt2"],
#                      r"$1^{\prime\prime}$", loc=3,
#                      borderpad=0.2)
    scalebar = AnchoredSizeBar(ax.transData,
                           5, r"$5^{\prime\prime}$", 'lower right', 
                           pad=0.1,
                           color='white',
                           frameon=False,
                           size_vertical=1, borderpad=0.5, sep=5,
#                            fontproperties=fontprops
                   )
    ax.add_artist(scalebar)
    kind = kwargs['kind'] or 'jpg'
    save_fig(plt, fig, kind, output=out+f'{chno}.jpg')
    


def bandpass_fc(csource, suffix='_init',ref_ant='C00', plotfolder='bp_plots/',fspw = '0:101~1900', 
                outvis='', **kwargs):
    cwd = getcwd()

    params={'reset':False,
            'quackinterval':10.0,
            'quackmode':'beg', 'bad_antenna':'','onvis':None,
                   }
#     params = defaultdict(lambda: -1, def_params)
    params.update(kwargs)
    if params['reset']:
        flagdata(vis=csource,mode='unflag', field='', spw='', antenna='', timerange='')
        clearcal(vis=csource)

    #### initialize ###########################
    s=fetch_sources(csource)
    csource_stem = Path(csource).stem

    ########## bandpass flagging ##############
    flagdata(vis=csource, mode='clip', clipzeros=True, flagbackup=False, action='apply') # clip zero amplitude
    flagdata(vis=csource, mode='shadow', tolerance=0.0, flagbackup=False, action='apply') # shadowing
    
    print(f' tfcrop on scan : {s["bpcals"]}')
    flagdata(vis=csource, mode='tfcrop', spw='0', scan=s["bpcals"], datacolumn='data', action='apply', 
             flagbackup=True)
    print(f' tfcrop on scan : {s["pmcals"]}')
    flagdata(vis=csource, mode='tfcrop', spw='0', scan=s["pmcals"], datacolumn='data', action='apply', 
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
    bandpass(vis=csource, caltable=bptab['BP_init'],
            field=s['bpcalf'], 
            solint=' inf ', combine='scan', refant=ref_ant, 
            minblperant=3, minsnr=10.0, gaintable=bptab['Ph_init'],
    #          selectdata=True, scan=bpcals,
            interp='nearest', solnorm=False)

    if params['onvis']:
        applycal(vis=params['onvis'], field='', calwt=False, gaintable=bptab['BP_init'])
        print(f'splitting ms....{csource_flagged}')
        split(params['onvis'],csource_flagged)
    else:    
        applycal(vis=csource, gaintable=bptab['BP_init'], calwt=False, scan=s['bpcals'])
        applycal(vis=csource, gaintable=bptab['BP_init'], calwt=False, scan=s['pmcals'])
        applycal(vis=csource, gaintable=bptab['BP_init'], calwt=False, scan=s['targets'])
    
        print(f'splitting ms....{csource_flagged}')
        split(csource,csource_flagged)


    
def rflag_pp(csource, scan, datacolumn='corrected'):
    csource_stem = Path(csource).stem
    outvis = csource_stem + 'rf.MS'
    flagdata(vis=csource, mode='rflag', spw='0', datacolumn=datacolumn, scan=scan,
            freqdevscale=2.5, timedevscale=3.5, extendflags=True, action='apply',
    #          display='both', 
            timeavg=True , flagbackup=True
            )
    flagdata(csource, mode='extend', growfreq=80.0, growtime=60.0, action='apply', extendpols=True)
    try :
        print('...splitting corrected column')
        split(vis=csource, outputvis=outvis, datacolumn='corrected', keepflags=False)
    except:
        print('...splitting data column')
        split(vis=csource, outputvis=outvis, datacolumn='data', keepflags=False)


def dical0(csource, suffix='_init', ref_ant='C00', gspw='0:201~1800', field='0',):
    #### initialize ###########################
    s=fetch_sources(csource)
    csource_stem = Path(csource).stem

    gtab={}
    gtab['delay']=csource_stem+'.K'+suffix
    gtab['bph']=csource_stem+'.P.G'+suffix
    gtab['bp']=csource_stem+'.B'+suffix
    gtab['intph']=csource_stem+'.IP.G'+suffix
    gtab['scnph']=csource_stem+'.SP.G'+suffix
    gtab['amp']=csource_stem+'.A.G'+suffix
    
    os.system(f'rm -rf {gtab["delay"]}')
    gaincal(vis=csource, caltable=gtab['delay'], 
            field=field, 
            selectdata=True, scan=s['pmcals'], 
            solint='inf', refant=ref_ant, gaintype='K')

    os.system(f'rm -rf {gtab["bph"]}')
    gaincal(vis=csource, caltable=gtab['bph'], 
            field=field, 
            spw=gspw, refant=ref_ant, 
            calmode='p', solint='int', 
            minsnr=3.0, gaintype='G', 
            gaintable=[gtab['delay']])

    os.system(f'rm -rf {gtab["bp"]}')
    bandpass(vis=csource, 
             caltable=gtab["bp"], 
             spw ='0',
             field=field,
             solint='inf', 
             refant=ref_ant, 
             solnorm = True,bandtype='B', gaintable=[gtab['bph'], gtab['delay']],
        minsnr=3.0, fillgaps=8, parang = True, 
             interp=['nearest,nearestflag','nearest,nearestflag'])

    # to fix Amp vs time
    os.system(f'rm -rf {gtab["intph"]}')
    gaincal(vis=csource,
            caltable=gtab["intph"], 
            field=field, 
            spw='0', 
            refant=ref_ant, 
            calmode='p', 
            solint='int', 
            minsnr=3.0, 
            gaintable=[gtab['bph'], gtab['delay']]
           )

    # no enough for interpolating the phase solutions in time
    os.system(f'rm -rf {gtab["scnph"]}')
    gaincal(vis=csource, 
            caltable=gtab['scnph'], 
            field=field, 
            spw='0', 
            refant=ref_ant, 
            calmode='p', 
            solint='inf', 
            combine='', 
            minsnr=3.0, 
            gaintable=[gtab['bph'], gtab['delay']]
           )

    # scaling amplitude gains skipping fluxscale as our flux-calibrator is also our 
    # bandpass and gain calibrator, the absolute flux scale will already be ok
    os.system(f'rm -rf {gtab["amp"]}')
    gaincal(vis=csource, 
            caltable=gtab['amp'], 
            field=field, 
            spw='0', selectdata=True, scan=s['pmcals'], 
            solint='inf', combine='', refant=ref_ant,
            calmode='ap', minsnr=3.0, 
            gaintable=[gtab['bph'], gtab['delay'], gtab['intph']])
    applycal(
        vis=csource, 
        field=s['bpcalf'], 
        gaintable=[gtab['delay'],gtab['bp'],gtab['scnph'],gtab['amp']], 
        gainfield=[s['bpcalf'],s['bpcalf'],s['bpcalf'],s['bpcalf']], 
        parang=True, calwt=False, applymode='calflagstrict', flagbackup=True)

    applycal(
        vis=csource, 
        field=s['targetf'], 
        gaintable=[gtab['delay'],gtab['bp'],gtab['scnph'],gtab['amp']], 
        gainfield=[s['bpcalf'],s['bpcalf'],s['bpcalf'],s['bpcalf']],
        calwt=False, applymode='calflagstrict', flagbackup=True)
    return {'tables':gtab}

def dical(csource, suffix='_di', ref_ant='C00', gspw='0:201~1800', **kwargs):
    #### initialize ###########################
    params={'ph':False, 'bp' : False, 'ampvtime':False,
    'solint':'inf','field':'0', }
    params.update(kwargs)
    csource_stem=Path(csource).stem
    s=fetch_sources(csource)
    gtab={}
    gtab['delay']=csource_stem+'.K'+suffix
    gtab['bph']=csource_stem+'.P.G'+suffix
    gtab['bp']=csource_stem+'.B'+suffix
    gtab['intph']=csource_stem+'.IP.G'+suffix
    gtab['scnph']=csource_stem+'.SP.G'+suffix
    gtab['amp']=csource_stem+'.A.G'+suffix
    
    if params['ph']:
        os.system(f'rm -rf {gtab["intph"]}')
        gaincal(vis=csource, 
            caltable=gtab['intph'], 
            field=params['field'], spw='0', refant=ref_ant, calmode='p', solint=params['solint'], 
            combine='', 
            minsnr=3.0)
        applycal(vis=csource, field=params['field'], gaintable=[gtab['intph']], interp='linear')
        outvis=Path(csource).stem+suffix+'.MS'
        print(f'phase calibration of field:{params["field"]} on {csource_stem}')
        print(f'splitting: {outvis}, calibrated field="0"')
        os.system(f'rm -rf {outvis}')
        split(vis=csource, outputvis=outvis, datacolumn='corrected', 
          field=params['field'], keepflags=False)
        
    if params['bp']:
        os.system(f'rm -rf {gtab["delay"]}')
        gaincal(vis=csource, caltable=gtab['delay'], 
                field=params['field'], 
                selectdata=True, scan=s['pmcals'], 
                solint='inf', refant=ref_ant, gaintype='K')

        os.system(f'rm -rf {gtab["bph"]}')
        gaincal(vis=csource, caltable=gtab['bph'], 
                field=params['field'], 
                spw=gspw, refant=ref_ant, 
                calmode='p', solint='int', 
                minsnr=3.0, gaintype='G', 
                gaintable=[gtab['delay']])

        os.system(f'rm -rf {gtab["bp"]}')
        bandpass(vis=csource, 
                caltable=gtab["bp"], 
                spw ='0',
                field=params['field'],
                solint='inf', 
                refant=ref_ant, 
                solnorm = True,bandtype='B', gaintable=[gtab['bph'], gtab['delay']],
            minsnr=3.0, fillgaps=8, parang = True, 
                interp=['nearest,nearestflag','nearest,nearestflag'])
    if params['ampvtime']:
        # to fix Amp vs time
        os.system(f'rm -rf {gtab["intph"]}')
        gaincal(vis=csource,
                caltable=gtab["intph"], 
                field=field, 
                spw='0', 
                refant=ref_ant, 
                calmode='p', 
                solint='int', 
                minsnr=3.0, 
                gaintable=[gtab['bph'], gtab['delay']]
            )

        # no enough for interpolating the phase solutions in time
        os.system(f'rm -rf {gtab["scnph"]}')
        gaincal(vis=csource, 
                caltable=gtab['scnph'], 
                field=field, 
                spw='0', 
                refant=ref_ant, 
                calmode='p', 
                solint='inf', 
                combine='', 
                minsnr=3.0, 
                gaintable=[gtab['bph'], gtab['delay']]
            )

        # scaling amplitude gains skipping fluxscale as our flux-calibrator is also our 
        # bandpass and gain calibrator, the absolute flux scale will already be ok
        os.system(f'rm -rf {gtab["amp"]}')
        gaincal(vis=csource, 
                caltable=gtab['amp'], 
                field=field, 
                spw='0', selectdata=True, scan=s['pmcals'], 
                solint='inf', combine='', refant=ref_ant,
                calmode='ap', minsnr=3.0, 
                gaintable=[gtab['bph'], gtab['delay'], gtab['intph']])
        applycal(
            vis=csource, 
            field=s['bpcalf'], 
            gaintable=[gtab['delay'],gtab['bp'],gtab['scnph'],gtab['amp']], 
            gainfield=[s['bpcalf'],s['bpcalf'],s['bpcalf'],s['bpcalf']], 
            parang=True, calwt=False, applymode='calflagstrict', flagbackup=True)

        applycal(
            vis=csource, 
            field=s['targetf'], 
            gaintable=[gtab['delay'],gtab['bp'],gtab['scnph'],gtab['amp']], 
            gainfield=[s['bpcalf'],s['bpcalf'],s['bpcalf'],s['bpcalf']],
            calwt=False, applymode='calflagstrict', flagbackup=True)
    return {'tables':gtab}

def init_flag(csource, **kwargs):
    
    params={'reset':False, 
            'quackinterval':10.0, 
            'quackmode':'beg', 'badant':'', 'badchan':'','clip':[0,50],'refant':'C00',
                   }
    params.update(kwargs)
    if params['reset']:
        flagdata(vis=csource,mode='unflag', field='', spw='', antenna='', timerange='')
        clearcal(vis=csource)

    s=fetch_sources(csource)
    csource_stem = Path(csource).stem

    flagdata(vis=csource, mode='clip', clipzeros=True, clipminmax=params['clip'], flagbackup=False, action='apply') # clip zero amplitude
    flagdata(vis=csource, mode='shadow', tolerance=0.0, flagbackup=False, action='apply') # shadowing
    flagdata(vis=csource, mode='quack', quackinterval=params['quackinterval'], quackmode=params['quackmode'], 
             flagbackup=False, action='apply')
    if params['badant']: flagdata(vis=csource, antenna=params['badant'],action='apply')
#     flagdata(vis=csource, mode='tfcrop', flagbackup=True, action='apply', extendpols=True, extendflags=True)
    flagdata(vis=csource, mode='extend', growfreq=80.0, growtime=60.0, action='apply', extendpols=True, extendflags=True)

def selfcal_model(calibrated_target, goodchans='0:500~600', ref_ant='C00'):
    ctarget_stem = str(Path(calibrated_target).stem)

    sctarget={}
    sctarget['sc1']=ctarget_stem+'.model1.MS'
    sctarget['sc2']=ctarget_stem+'.model2.MS'
    sctarget['sc3']=ctarget_stem+'.model3.MS'

    sgtab={}
    sgtab['sc1']='sc1.gcal'
    sgtab['sc2']='sc2.gcal'
    sgtab['sc3']='sc3.gcal'
    os.system(f"rm -rf {sctarget['sc1']}* {sctarget['sc2']}* {sctarget['sc3']}* {sgtab['sc1']}* {sgtab['sc2']}* {sgtab['sc3']}* {ctarget_stem}.model.cimage")

    tclean(vis=calibrated_target, 
           datacolumn='data', 
           imagename=ctarget_stem+'.model.cimage', 
           spw=goodchans, 
           specmode='mfs', 
           niter=100, 
           threshold='1.5Jy', 
           imsize=[256,256], cell='1arcsec', 
           weighting='briggs', robust=0.2, 
           savemodel='modelcolumn')
    gaincal(vis=calibrated_target, 
            caltable=sgtab['sc1'], 
            field='0', spw='0', refant=ref_ant, calmode='p', solint='30s', combine='', 
            minsnr=3.0)
    applycal(vis=calibrated_target, field='0', gaintable=[sgtab['sc1']], interp='linear')
    split(vis=calibrated_target, outputvis=sctarget['sc1'], datacolumn='corrected', 
          field='0', keepflags=False)

    tclean(vis=sctarget['sc1'], datacolumn='data', 
           imagename=sctarget['sc1']+'.cimage', 
           spw=goodchans, 
           specmode='mfs', 
           niter=500, 
           threshold='500mJy', 
           imsize=[256,256],cell='1arcsec', 
           weighting='briggs', robust=0.2, 
           savemodel='modelcolumn')
    gaincal(vis=sctarget['sc1'], caltable=sgtab['sc2'], 
            field='0', spw='0', refant=ref_ant, calmode='p', solint='10s', combine='', 
            minsnr=3.0)
    applycal(vis=sctarget['sc1'], field='0', gaintable=[sgtab['sc2']], interp='linear')
    split(vis=sctarget['sc1'], outputvis=sctarget['sc2'], datacolumn='corrected', 
          field='0', keepflags=False)

    tclean(vis=sctarget['sc2'], datacolumn='data', 
           imagename=sctarget['sc2']+'.cimage', spw=goodchans, 
           specmode='mfs', 
           niter=1000, threshold='100mJy', 
           imsize=[256,256], cell='1arcsec', weighting='briggs', robust=0.2, 
           savemodel='modelcolumn')
    gaincal(vis=sctarget['sc2'], caltable=sgtab['sc3'], 
            field='0', spw='0', refant=ref_ant, calmode='ap', solint='int', combine='', 
            minsnr=3.0)
    applycal(vis=sctarget['sc2'], field='0', gaintable=[sgtab['sc3']], interp='linear')
    
    os.system(f'rm -rf {sctarget["sc3"]}.*')
    split(vis=sctarget['sc2'], outputvis=sctarget['sc3'], datacolumn='corrected', 
          field='0', keepflags=False)

    tclean(vis=sctarget['sc3'], datacolumn='data', 
           imagename=sctarget['sc3']+'.cimage', spw=goodchans, 
           specmode='mfs', 
           niter=1000, threshold='100mJy', 
           imsize=[256,256], cell='1arcsec', weighting='briggs', robust=0.2, 
           savemodel='modelcolumn')
    return {'model_imagename':sctarget['sc3']+'.cimage', 'model_vis':sctarget['sc3']}


def tclean_spectral_image(vis, imagename, f=None, suffix='', norm_max=None):
    os.system(f'rm -rf {imagename}.*')
    if f:
        rest_freq = str(f)+'MHz'
        f=float(f)
    tclean(vis=vis, datacolumn='data', 
           imagename=imagename, spw=f'0:{rest_freq}',
           specmode='cube', outframe='bary', veltype='radio', restfreq=rest_freq, 
           niter=10000000, threshold='0.05Jy',
           imsize=[256,256], cell='1arcsec', 
           pbcor=True, weighting='briggs', robust=0.2, 
           perchanweightdensity=True, savemodel='none',
           interpolation='nearest')
    msmd.open(vis)
    nchan = msmd.nchan(0)
    chanwidths = float(msmd.chanwidths(0, 'MHz')[0])
    freqstart = float(msmd.chanfreqs(0, 'MHz')[0])
    msmd.done()
    n = (f - freqstart)/chanwidths
    if not n == float(int(n)): 
        plotchans = [int(n), int(n+1)]
    else:
        plotchans = [int(n)]
    for i in range(len(plotchans)):
        genpng(imagename+'.image',i,out=f"{imagename}_{plotchans[i]}.bary.cube", norm_max=norm_max, kind='jpg')
    #   imview(raster={'file':f"{imagename}"+'.image', 'colormap': 'Hot Metal 1'}, 
#        zoom={'channel': 0, },
#        axes={'z':'Frequency',},
#         out=f"{imagename}"+suffix+'.bary.cube.1'+'.png',       
#       )
#     imview(raster={'file':f"{imagename}"+'.image', 'colormap': 'Hot Metal 1'}, 
#            zoom={'channel': 1, },
#            axes={'z':'Frequency',},
#             out=f"{imagename}"+suffix+'.bary.cube.2'+'.png',
#           )

def tclean_continuum_image(science_vis_cont, imagename, suffix='', norm_max=None):
    os.system(f'rm -rf {imagename} {imagename}.*')
    tclean(vis=science_vis_cont, datacolumn='data', 
       imagename=imagename, spw='0', 
       specmode='mfs', 
       niter=1000, threshold='50mJy', 
       imsize=[256,256], cell='1arcsec', weighting='briggs', robust=0.2, 
#        savemodel='modelcolumn'
      )
    if norm_max is None:
        norm_max=imstat(imagename+'.image')['max'][0]
    genpng(imagename+'.image',0,out=f"{imagename}"+suffix, norm_max=norm_max, kind='jpg')
    return norm_max
#     imview(raster={'file':f"{imagename}"+'.image', 'colormap': 'Hot Metal 1'}, 
#             out=f"{imagename}"+suffix+'.cont'+'.png',

#           )



def fast_spectral_image(calvis, cvis, timerange='',f=None, suffix=''):
    os.system(f'rm -rf {cvis}*')
    rest_freq=None
    if f:
        rest_freq = str(f)+'MHz'
        f=float(f)
    # msmd.open(calvis)
    # msmd.chanwidths()
    fitspw=f'0:{rest_freq}'
    print(f"split({calvis}, {cvis}, timerange={timerange}, datacolumn='data')")
    split(calvis, cvis, timerange=timerange, datacolumn='data', spw='0:590~610MHz')
    if rest_freq is not None:
        uvcontsub(cvis, field='0',
            # fitspw=fitspw, #'0:0.566~0.575GHz',
            fitspw='0:595~599MHz',
            excludechans=True,
            fitorder=1,
            want_cont=False,
            )        
        science_vis=cvis+'.contsub'
        # science_vis_cont=cvis+'.cont'
        # norm_max=tclean_continuum_image(science_vis_cont, science_vis_cont+'.cimage', suffix=suffix+'.cont')
        tclean_spectral_image(science_vis, science_vis+'.cimage',f=f, suffix=suffix+'.cube')
    else:
        tclean_continuum_image(cvis, cvis+'.cimage', suffix=suffix)
    

def cli():
    fitsfile=args.fitsfilename or '/datax/scratch/AMITY_INDIA/avi/GMRT_d/tst2505/TEST2505_B0329_100MHZ_GWB_2.FITS'
    visfile=args.visibilityfilename or 'uncal1_0329.MS'
    f = args.frequency or None
    timerange = args.timerange or ''
    timeinstant = args.timeinstant or None
    flg = args.flag  or 0
    fitstovis = args.fitstovis or False
    pp = args.pipeline
    p = args.pipe

    s = fetch_sources(visfile)
    if fitsfile and fitstovis:
        os.system(f'rm -rf {visfile}')
        importgmrt(fitsfile=fitsfile, vis=visfile)
        print('importgmrt task finished.')
    
    if pp == 222:
        split(visfile, 'calibrated_target.MS', datacolumn='data', field='1' )#timerange='15:03:55~15:12:24')
    if pp == 111:
        # print(visstat(visfile))
        metadata = listobs(visfile,)# selectdata=True, scan=s['targets'], verbose=True, listfile='meta.txt', overwrite=True)
        # print(metadata['field_'+s['targetf']])
        from astropy import units as u
        from astropy.coordinates import SkyCoord
        ra = metadata['field_'+s['targetf']]['direction']['m0']['value']*u.radian
        dec = metadata['field_'+s['targetf']]['direction']['m1']['value']*u.radian
        c = SkyCoord(ra=ra, dec=dec, frame='fk5').to_string('hmsdms')
        name = metadata['field_'+s['targetf']]['name']
        metareturn = {'position' : c, 'name':name}
        print(metareturn)
        # print(metadata['timeref'])
        # print(metadata)
    
    if timeinstant:
            metadata = listobs(visfile, selectdata=True, scan=s['targets'])
            MJD=metadata['scan_'+s['targets']]['0']['BeginTime']
            tMJD = Time(MJD, format='mjd', scale=str.lower(metadata['timeref']))
            timeresolution = np.round(metadata['scan_'+s['targets']]['0']['IntegrationTime'],2) or 5.37
            ti = TimeDelta(timeinstant, format='sec', scale=str.lower(metadata['timeref']))
            tr = TimeDelta((timeresolution/2), format='sec', scale=str.lower(metadata['timeref'])) # half of time resolution
            t1,t2=(tMJD+ti-tr).to_value('datetime'), (tMJD+ti+tr).to_value('datetime')
            timerange=f"{t1.year}/{t1.month}/{t1.day}/{t1.time()}~{t2.year}/{t2.month}/{t2.day}/{t2.time()}"
            print(f"Scan:{metadata['scan_'+s['targets']]['0']['FieldName']} \t InTime:{metadata['scan_'+s['targets']]['0']['IntegrationTime']}\n {timerange}")

    if timerange or f:
        if f:
            model=selfcal_model(visfile)
            print(model)
            fast_spectral_image(model['model_vis'], Path(visfile).stem+'_cvis', str(timerange), f=f)
        elif timerange:
            if not timeinstant:
                td = timerange.split('~')
                try:
                    thms = np.vstack((td[0].split(':'), td[1].split(':')))
                    tdiff = thms[1].astype(float)-thms[0].astype(float)
                    tsec = int(tdiff[2] +(tdiff[1]*60)+(tdiff[0]*3600))
                except:
                    thms = Time(td)
                    tdiff = thms[1] - thms[0]
                    tsec = tdiff.sec
            else:
                tsec = timeinstant
            model=selfcal_model(visfile)
            print(model)
            fast_spectral_image(model['model_vis'], Path(visfile).stem+f'_{int(tsec)}.MS', str(timerange))

    if flg == 1:
        kwargs={}
        kwargs['badant']='C03,C08,C09,C10,C11,C14,C06'
        init_flag(visfile, **kwargs)
    
    if pp == 1:
        outvis = Path(visfile).stem + '_bp.MS'
        bandpass_fc(visfile, outvis=outvis)
        print(f'finished flagging calibrators')

    if pp == 11 or p[0]=='bp':
        onvis = p[1] if len(p)>1 else visfile
        outvis = Path(onvis).stem + '_bp.MS'
        # metadata=listobs(onvis, verbose=True)
        # msmd.open(onvis)
        # nchan = msmd.nchan(0)
        # msmd.done()
        # spw, avgchannel, uvrange, antenna =f'0:{int(nchan*0.02)}~{int(nchan*0.98)}', str(nchan),'2000~14000'
        # print(f"{spw}, {avgchannel}, {uvrange}")
        kwargs={'onvis':onvis if len(p)>1 else None}
        bandpass_fc(visfile, outvis=outvis, **kwargs)
        print(f'finished flagging calibrators')
    if pp == 2:
        flagmanager(vis=visfile,mode='save',versionname='pp2')
        csource_stem = Path(visfile).stem
        calibrated_csource=csource_stem+'cal1'+'.MS'

        ########## bandpass calibrator calibration ##############
        setjy(vis=visfile, field=s['bpcalf'], 
            scan=s['bpcals'], 
            scalebychan=True, standard='Perley-Butler 2017', 
            listmodels=False, usescratch=True)
        tab_init = dical0(visfile, '_init')
        # tab_recal= dical(csource, '_recal')
        split(visfile,calibrated_csource)
        print(f'completed pipeline 2..... {calibrated_csource}')
    
    if pp == 3:
        model=selfcal_model(visfile)
        print(model)
    
    if pp == 4:
        t_step = 22
        k1 = 5
        k2 = k1+t_step
    
        # timerange=f'15:04:{k1:02d}.8~15:04:{k2:02d}.8'
        if not timerange: timerange=''
        if f is None: rest_freq=599.934
        print(visfile, visfile+'_cvis', str(timerange), rest_freq , f'{k2}')
        fast_spectral_image(visfile, Path(visfile).stem+'_cvis', str(timerange), rest_freq , suffix=f'{k2}')

    if pp == 5:
        rflag_pp(visfile, '2', 'data')

    if pp == 555:
        metadata=listobs(visfile, verbose=True)
        fieldl = {k.replace('field_', ''):{'name':v['name']} for k,v in metadata.items() if 'field_' in k}
        scanl = {k.replace('scan_', ''):v['0']['FieldName'] for k,v in metadata.items() if 'scan_' in k}
        for fk,fv in fieldl.items():
            fieldl[str(fk)]['scans']=[k.replace('scan_', '') for k,v in metadata.items() if ('scan_' in k) and (v['0']['FieldId']==int(fk))]
        metadata.update({'fieldl':fieldl, 'scanl':scanl})
        print(metadata)


    if pp == 66:
        print(visstat(visfile))
        metadata = listobs(visfile)
        print(metadata)

    if pp == 6:
        for scan in ['1', '2', '3']:
            print(f'visfile: {visfile} scan : {scan}')
            print(visstat(visfile, selectdata=True, scan=scan))

    if pp == 7:
        split(visfile,Path(visfile).stem + '_target.MS', datacolumn='data')
    
    if p[0] == 'split':
        print(f'splitting...{p}')
        split(visfile,Path(visfile).stem + '_target.MS',field=p[1], datacolumn='data')
    if p[0] == 'splitc':
        split(visfile, p[1])
    if p[0] == 'phase':
        params, kwargs=['ph','field', 'solint'], {}
        for i in range((len(p))):
            kwargs[params[i]]=p[(i)] if i!=0 else True
            
        print(f'kwargs:{kwargs}')
        dical(visfile, **kwargs)

    if pp == 10:
        imagename = visfile
        out = Path(imagename).stem
        stat = imstat(imagename)
        print(stat)
        print(stat['max'][0])
        genpng(imagename,5,out=f"{out}", kind='jpg', norm_max=stat['max'][0])
        genpng(imagename,6,out=f"{out}", kind='jpg', norm_max=stat['max'][0])
        # from pyvirtualdisplay import Display
        # display = Display(visible=0,size=(1024,768))
        # display.start()
        # try:
        #     imview(raster={'file':f"{imagename}.image", 'colormap': 'Hot Metal 1'}, 
        #     out={'file':f"output/{imagename}.jpg", 'format':'jpg'},
        #     axes={'z':'1'}
        #     )
        # finally:
        #     display.stop()
        

    if pp == 9:
        from pyvirtualdisplay import Display
        display = Display(visible=0,size=(1024,768))
        display.start()
        print('plotms start....')
        plotfolder='plots/'
        if not path.exists(plotfolder):
            try:
                oumask = os.umask(0)
                makedirs(plotfolder)
            except:
                os.umask(oumask)
                makedirs(plotfolder, 777)
        stem=Path(visfile).stem
        scans= ['2']
        for scan in scans:
            yaxis,xaxis='phase','amp' 
            plotms(vis=visfile, spw='0', scan=scan,
            xaxis=xaxis, ydatacolumn='data',
            yaxis=yaxis,
            antenna='DA42', coloraxis='corr',
            showgui=False, plotfile=plotfolder+f'{yaxis}_{xaxis}_{scan}_{stem}_data.jpg',
            overwrite=True, avgbaseline=True, symbolsize=2, averagedata=True,avgtime='600',
            clearplots=True
            )
            yaxis,xaxis='amp','freq'
            plotms(vis=visfile, spw='0', scan=scan,
            xaxis=xaxis, ydatacolumn='data',
            yaxis=yaxis,
            antenna='DA42', coloraxis='corr',
            showgui=False, plotfile=plotfolder+f'{yaxis}_{xaxis}_{scan}_{stem}_data.jpg',
            overwrite=True, avgbaseline=True, symbolsize=2, averagedata=True,avgtime='600',
            clearplots=True
            )
            yaxis,xaxis='amp','time'
            plotms(vis=visfile, spw='0', scan=scan,
            xaxis=xaxis, ydatacolumn='data',
            yaxis=yaxis,
            antenna='DA42', coloraxis='corr',
            showgui=False, plotfile=plotfolder+f'{yaxis}_{xaxis}_{scan}_{stem}_data.jpg',
            overwrite=True, avgbaseline=True, symbolsize=2, averagedata=True,avgchannel='2048',
            #avgtime='600',
            clearplots=True
            )
        print('..stopping')
        # plotms(vis=csource, xaxis='freq', yaxis='amp', avgtime='8', field='0', antenna=params['refant'], coloraxis='baseline', showgui=False, plotfile='freq_amp_flagged.jpg')
        display.stop()

    if pp==999 or p[0]=='plots':
        """
        TODO : 
        1. Better target and calibrator identification
        2. 
        """
        from pyvirtualdisplay import Display
        display = Display(visible=0,size=(1024,768))
        display.start()

        plotfolder=f'plots/{Path(visfile).stem}/'
        if not path.exists(plotfolder):
            try:
                oumask = os.umask(0)
                makedirs(plotfolder)
            except:
                os.umask(oumask)
                makedirs(plotfolder, 777)
        
        vis = visfile
        metadata=listobs(vis, verbose=True)
        msmd.open(vis)
        nchan = msmd.nchan(0)
        msmd.done()

        fieldl = {k.replace('field_', ''):{'name':v['name']} for k,v in metadata.items() if 'field_' in k}
        scanl = {k.replace('scan_', ''):v['0']['FieldName'] for k,v in metadata.items() if 'scan_' in k}
        for fk,fv in fieldl.items():
            fieldl[str(fk)]['scans']=[k.replace('scan_', '') for k,v in metadata.items() if ('scan_' in k) and (v['0']['FieldId']==int(fk))]
        metadata.update({'fieldl':fieldl, 'scanl':scanl})
        spw, avgchannel, uvrange, antenna =f'0:{int(nchan*0.4)}~{int(nchan*0.6)}', str(nchan),'2000~8000','C00'
        print(f"{spw}, {avgchannel}, {uvrange}, {antenna}")
        # selectedfield=metadata['fieldl']['4']
        try:
            for scan in scanl.keys():
                scan=str(scan)
                print(scan)
                xaxis, yaxis= 'freq', 'amp'
                plotms(vis=vis, scan=scan,antenna=antenna, spw=spw,
                xaxis=xaxis, yaxis=yaxis, coloraxis='corr', title=f'{yaxis} vs {xaxis} - {scan}',
                    showgui=False, correlation='RR,LL',
                    averagedata=True, avgtime='1e9', avgbaseline=True,
                uvrange=uvrange,
                plotfile=plotfolder+f"{yaxis}_v_{xaxis}.{scanl[str(scan)]}.{scan}.png", overwrite=True)
                xaxis, yaxis = 'freq', 'phase'
                plotms(vis=vis, scan=scan, antenna=antenna, spw=spw,
                xaxis=xaxis, yaxis=yaxis, coloraxis='corr', title=f'{yaxis} vs {xaxis} - {scan}',
                    showgui=False, averagedata=True, avgtime='1e9', avgbaseline=True,
                uvrange=uvrange,
                plotfile=plotfolder+f"{yaxis}_v_{xaxis}.{scanl[str(scan)]}.{scan}.png", overwrite=True)
                xaxis, yaxis = 'amp', 'phase'
                plotms(vis=vis, scan=scan, antenna=antenna, spw=spw,
                xaxis=xaxis, yaxis=yaxis, coloraxis='corr', title=f'{yaxis} vs {xaxis} - {scan}',
                    showgui=False, averagedata=True, avgtime='1e9', avgbaseline=True,
                uvrange=uvrange,
                plotfile=plotfolder+f"{yaxis}_v_{xaxis}.{scanl[str(scan)]}.{scan}.png", overwrite=True)
                xaxis, yaxis = 'time', 'phase'
                plotms(vis=vis, scan=scan, antenna=antenna, spw=spw,
                xaxis=xaxis, yaxis=yaxis, coloraxis='corr', title=f'{yaxis} vs {xaxis} - {scan}',
                    showgui=False, averagedata=True, avgchannel=avgchannel, avgbaseline=True,
                uvrange=uvrange,
                plotfile=plotfolder+f"{yaxis}_v_{xaxis}.{scanl[str(scan)]}.{scan}.png", overwrite=True)
                xaxis, yaxis = 'time', 'amp'
                plotms(vis=vis, scan=scan, antenna=antenna, spw=spw,
                xaxis=xaxis, yaxis=yaxis, coloraxis='corr', title=f'{yaxis} vs {xaxis} - {scan}',
                    showgui=False, averagedata=True, avgchannel=avgchannel, avgbaseline=True,
                uvrange=uvrange,
                plotfile=plotfolder+f"{yaxis}_v_{xaxis}.{scanl[str(scan)]}.{scan}.png", overwrite=True)
                xaxis, yaxis = 'uvdist', 'amp'
                plotms(vis=vis, scan=scan, antenna=antenna, spw=spw,
                xaxis=xaxis, yaxis=yaxis, coloraxis='baseline', title=f'{yaxis} vs {xaxis} - {scan}',
                    showgui=False, averagedata=True, avgtime='1e9', avgchannel=avgchannel,
                uvrange=uvrange,
                plotfile=plotfolder+f"{yaxis}_v_{xaxis}.{scanl[str(scan)]}.{scan}.png", overwrite=True)
                xaxis, yaxis = 'uvdist', 'phase'
                plotms(vis=vis, scan=scan, antenna=antenna, spw=spw,
                xaxis=xaxis, yaxis=yaxis, coloraxis='baseline', title=f'{yaxis} vs {xaxis} - {scan}',
                    showgui=False, averagedata=True, avgtime='1e9', avgchannel=avgchannel,
                uvrange=uvrange,
                plotfile=plotfolder+f"{yaxis}_v_{xaxis}.{scanl[str(scan)]}.{scan}.png", overwrite=True)
        finally:
            display.stop()


    if pp==8:
        clearcal(vis=visfile)
        flagdata(vis=visfile,mode='unflag', field='', spw='', antenna='', timerange='')

if __name__=='__main__':
    cli()