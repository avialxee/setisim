
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
from casatools import ms, msmetadata, table
from pyvirtualdisplay import Display
    

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
            'scan':'', 'extend':False
                   }
    params.update(kwargs)
    if params['reset']:
        flagdata(vis=csource,mode='unflag', field='', spw='', antenna='', timerange='')
        clearcal(vis=csource)

    s=fetch_sources(csource)
    csource_stem = Path(csource).stem

    flagdata(vis=csource, mode='clip', clipzeros=True, scan=params['scan'],clipminmax=params['clip'], flagbackup=False, action='apply') # clip zero amplitude
    flagdata(vis=csource, mode='shadow', tolerance=0.0, scan=params['scan'],flagbackup=False, action='apply') # shadowing
    if params['quackmode']:flagdata(vis=csource, mode='quack', scan=params['scan'],quackinterval=params['quackinterval'], quackmode=params['quackmode'], 
             flagbackup=False, action='apply')
    if params['badant']: flagdata(vis=csource, antenna=str(params['badant']),action='apply')
#     flagdata(vis=csource, mode='tfcrop', flagbackup=True, action='apply', extendpols=True, extendflags=True)
    if params['extend']:flagdata(vis=csource, mode='extend', growfreq=80.0, growtime=60.0, action='apply', extendpols=True, extendflags=True)

def flagsummary(vis):
    fsummary = flagdata(vis, mode='summary')
    sof=fsummary.keys()
    fgen=['name','type', 'total', 'flagged']
    totflag=np.round((fsummary['flagged']/fsummary['total'])*100,2)
    print(f"{fsummary['name']}\n-----\nTotal flagged:{totflag}%")
    flaggable={}
    for s in sof:

        if s in fgen:
            pass
        else:
            print(f'\n{s}:\n')
            for k in fsummary[s]:
                v=fsummary[s][k]
                perc = np.round((fsummary[s][k]['flagged']/fsummary[s][k]['total'])*100,2)

                if perc>totflag and s=='antenna':
                    flaggable[k]=perc

                print(f"{k}:{perc}%")
    antmax = max(flaggable, key=flaggable.get)
    ant3sigma=np.round(float(totflag)+((float(flaggable[str(antmax)])-float(totflag))/3),2)
    print(f'antenna 3 sigma : {ant3sigma}')
    for ant,perc in flaggable.items():
        if perc>ant3sigma:
            print(f'flaggable antenna:{ant}')
    # print(f'flaggable antenna:{antmax}\n {flaggable}')
    return {'flaggable':flaggable}

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
           imagename=imagename, spw=f'0:596~597.5MHz',#{rest_freq}',
           specmode='cube', outframe='bary', veltype='radio', restfreq=rest_freq, 
           niter=10000000, threshold='0.05Jy',
           imsize=[256,256], cell='1arcsec', 
        #    pbcor=True, 
           weighting='briggs', robust=0.0, 
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
    # msmd.open(calvis)
    # msmd.chanwidths()
    fitspw=f'0:{rest_freq}'
    print(f"split({calvis}, {cvis}, timerange={timerange}, datacolumn='data')")
    split(calvis, cvis, timerange=timerange, datacolumn='data', )#spw='0:590~610MHz')
    if rest_freq is not None:
        uvcontsub(cvis, field='0',
            # fitspw=fitspw, #'0:0.566~0.575GHz',
            fitspw='0:596~597.5MHz',
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
    
def plotd(visfile, **kwargs):
    display = Display(visible=0,size=(1024,768))
    display.start()

    plotfolder=f'plots/{Path(visfile).stem}/'
    if not path.exists(plotfolder):
        try:
            oumask = os.umask(0)
            makedirs(plotfolder)
        except:
            os.umask(oumask)
            makedirs(plotfolder, 775)
    print(f'plotting in folder: {plotfolder}')
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
    params={'spw':'',#f'0:{int(nchan*0.4)}~{int(nchan*0.6)}',
    'avgchannel' :str(nchan),
    'uvrange':'',
    'antenna':'C00', 'scan':'', 'corr':'',
    'xaxis':[''], 'yaxis':['']}
    params.update(kwargs)
    spw, avgchannel, uvrange, antenna = params['spw'], params['avgchannel'], params['uvrange'], params['antenna']
    print(f"{spw}, {avgchannel}, {uvrange}, {antenna}")
    # selectedfield=metadata['fieldl']['4']
    scanlist = params['scan'] or scanl.keys()
    comb={'amp':{'freq':{'averagedata':True,'avgtime':'1e9', 'avgbaseline':False, 'avgchannel':''},
             'time':{'averagedata':False,'avgtime':'', 'avgbaseline':False, 'avgchannel':''},
             'uvwave':{'averagedata':False,'avgtime':'', 'avgbaseline':False, 'avgchannel':''}
            }, 
      'phase':{'freq':{'averagedata':True,'avgtime':'1e9', 'avgbaseline':False, 'avgchannel':''},
               'time':{'averagedata':True,'avgtime':'', 'avgbaseline':True, 'avgchannel':nchan},
               'uvwave':{'averagedata':False,'avgtime':'', 'avgbaseline':False, 'avgchannel':nchan},
               'amp':{'averagedata':True,'avgtime':'1e9', 'avgbaseline':False, 'avgchannel':''}
              },
     }
    _pd={}
    for k,v in comb.items():
        for yi in params['yaxis']:
            if yi:
                if yi==k:            
                    for xi in params['xaxis']:
                        for vi in v:
                            if xi and (xi==vi):
                                try:
                                    _pd[k][vi]=comb[k][vi]
                                except:
                                    _pd[k]={vi:comb[k][vi]}
                                break
                            else:
                                try:
                                    _pd[k][vi]=comb[k][vi]
                                except:
                                    _pd[k]={vi:comb[k][vi]}

            else:
                for xi in params['xaxis']:
                    for vi in v:
                        if xi:
                            if xi==vi:
                                try:
                                    _pd[k][vi]=comb[k][vi]
                                except:
                                    _pd[k]={vi:comb[k][vi]}
                                break
                        else:
                            try:
                                _pd[k][vi]=comb[k][vi]
                            except:
                                _pd[k]={vi:comb[k][vi]}                       
    try:
        for scan in scanlist:
            scan=str(scan)
            print(scan)
            # print(_pd)
            for yaxis,xaxes in _pd.items():
                for xaxis,avgdata in xaxes.items():
                    print(f'{yaxis} vs {xaxis}')
                    plotms(vis=vis, scan=scan, antenna=antenna, spw=spw, correlation=params['corr'],
                        xaxis=xaxis, yaxis=yaxis, coloraxis='corr', title=f'{scanl[str(scan)]}:{yaxis} vs {xaxis} - {scan}',
                        showgui=False,
                        averagedata=avgdata['averagedata'], avgtime=avgdata['avgtime'], avgbaseline=avgdata['avgbaseline'],
                        avgchannel=str(avgdata['avgchannel']),
                        uvrange=uvrange,
                        plotfile=plotfolder+f"{yaxis}_v_{xaxis}.{scanl[str(scan)]}.{scan}.png", overwrite=True)
            
    finally:
        display.stop()