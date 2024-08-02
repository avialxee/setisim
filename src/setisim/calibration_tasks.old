import os
from pathlib import Path
import numpy as np
from os import path, makedirs
import matplotlib.pyplot as plt
from scipy import stats
from setisim.calibration


def solint_p(vis,**kwargs):
    params={'read':False}
    params.update(kwargs)
    tablefolder=f'tables/{Path(vis).stem}/'
    if not path.exists(tablefolder):
            makedirs(tablefolder)
    tab={}
    tab={
        'p_3':tablefolder+'solint_3.tb',
        'p_6':tablefolder+'solint_6.tb',
        'p_12':tablefolder+'solint_12.tb',
        'p_24':tablefolder+'solint_24.tb',
        'p_48':tablefolder+'solint_48.tb',
        'p_96':tablefolder+'solint_96.tb',
    }
    if not params['read']:
        os.system(f"rm -rf {' '.join(tab.values())}")
        gaincal(vis=vis,caltable=tab['p_3'],
            solint='int',refant='C00',calmode='p',gaintype='T', minsnr=0)
        gaincal(vis=vis,caltable=tab['p_6'],
            solint='6s',refant='C00',calmode='p',gaintype='T', minsnr=0)
        gaincal(vis=vis,caltable=tab['p_12'],
            solint='12s',refant='C00',calmode='p',gaintype='T', minsnr=0)
        gaincal(vis=vis,caltable=tab['p_24'],
            solint='24s',refant='C00',calmode='p',gaintype='T', minsnr=0)
        gaincal(vis=vis,caltable=tab['p_48'],
            solint='48s',refant='C00',calmode='p',gaintype='T', minsnr=0)
        gaincal(vis=vis,caltable=tab['p_96'],
            solint='96s',refant='C00',calmode='p',gaintype='T', minsnr=0)

    
    tb=table()
    tb.open( f"{tab['p_6']}" )
    snr_6s = tb.getcol( 'SNR' ).ravel()
    tb.close()

    tb.open( f"{tab['p_12']}" )
    snr_12s = tb.getcol( 'SNR' ).ravel()
    tb.close()

    tb.open( f"{tab['p_24']}" )
    snr_24s = tb.getcol( 'SNR' ).ravel()
    tb.close()

    tb.open( f"{tab['p_48']}" )
    snr_48s = tb.getcol( 'SNR' ).ravel()
    tb.close()

    tb.open( f"{tab['p_96']}" )
    snr_96s = tb.getcol( 'SNR' ).ravel()
    tb.close()
    
    plt.hist( snr_6s, bins=50, density=True, histtype='step', label='6 seconds' )
    plt.hist( snr_12s, bins=50, density=True, histtype='step', label='12 seconds' )
    plt.hist( snr_24s, bins=50, density=True, histtype='step', label='24 seconds' )
    plt.hist( snr_48s, bins=50, density=True, histtype='step', label='48 seconds' )
    plt.hist( snr_96s, bins=50, density=True, histtype='step', label='96 seconds' )
    plt.legend( loc='upper right' )
    plt.xlabel( 'SNR' )
    
    med=int(np.median( snr_6s ) ) # TODO: change snr_6s to time resolution
    print( f"P(<={med}) = {stats.percentileofscore( snr_6s, med )}, 6s")
    print( f"P(<={med}) = {stats.percentileofscore( snr_12s, med )}, 12s")
    print( f"P(<={med}) = {stats.percentileofscore( snr_24s, med )}, 24s")
    print( f"P(<={med}) = {stats.percentileofscore( snr_48s, med )}, 48s")
    print( f"P(<={med}) = {stats.percentileofscore( snr_96s, med )}, 96s")
    return {'tab':tab, 'med':med}



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
    #          display='both', 
            timeavg=True , flagbackup=True
            )
    flagdata(csource, mode='extend', growfreq=80.0, growtime=60.0, action='apply', extendpols=True)
    print(f'splitting ms....{csource_flagged}')
    split(csource,csource_flagged)
    
    


def dical(csource, suffix='_init', ref_ant='C00', gspw='0:201~1800', field='0',):
    
    
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
            spw='0', selectdata=False, solint='inf', combine='', refant=ref_ant,
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

def all_cal(csource, suffix='_init',ref_ant='C00', plotfolder='simplots/',fspw = '0:101~1900', 
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
    calibrated_csource=outvis or csource_stem+suffix+'.MS'

    ########## bandpass calibrator calibration ##############
    setjy(vis=csource, field=s['bpcalf'], 
          scan=s['bpcals'], 
          scalebychan=True, standard='Perley-Butler 2017', 
          listmodels=False, usescratch=True)
    tab_init = dical(csource, '_init')
    # tab_recal= dical(csource, '_recal')
    split(csource,calibrated_csource)
    

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
            field='0', spw='0', refant=ref_ant, calmode='p', solint='60s', combine='', 
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
            field='0', spw='0', refant=ref_ant, calmode='p', solint='30s', combine='', 
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
            field='0', spw='0', refant=ref_ant, calmode='ap', solint='30s', combine='', 
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




def fast_spectral_image(calvis, cvis, timerange,rest_freq , suffix):
    os.system(f'rm -rf {cvis}')
    split(calvis, cvis, timerange=timerange, datacolumn='data')
    uvcontsub(cvis, field='0',
          fitspw=f'0:{rest_freq}', excludechans=True,
          fitorder=1,
          want_cont=True,
         )
    science_vis=cvis+'.contsub'
    science_vis_cont=cvis+'.cont'
    norm_max=tclean_continuum_image(science_vis_cont, science_vis_cont+'.cimage', suffix=suffix+'.cont')
    tclean_spectral_image(science_vis, science_vis+'.cimage', rest_freq, suffix=suffix+'.cube', norm_max=norm_max)




def selfcal_all(calibrated_csource, ):
    s=s=fetch_sources(calibrated_csource)
    ctarget_stem = Path(calibrated_csource).stem
    calibrated_target=ctarget_stem+f'_field{s["targetf"]}.MS'
    rest_freq = '599.934021MHz'

    split(calibrated_csource, calibrated_target, datacolumn='data', field=s['targetf'])
    model_dict=selfcal_model(calibrated_target)
    t_duration = 12 # total time duration (seconds)
    t_step = 12 # t_step seconds for imaging as time step in between the total duration
    sctarget={}
    sctarget['sc3'],sctarget['sc3_t']= model_dict['model_vis'], model_dict['model_vis']+'_spectral_image'
    
    for i in range(5,t_duration,t_step): # 
        k1 =i
        k2 =k1+t_step
        sctarget['sc3_tk']=sctarget['sc3_t']+f'{k1}_{k2}.MS'
        timerange=f'15:04:{k1:02d}.8~15:04:{k2:02d}.8'
        print(timerange)    
        print(sctarget['sc3_tk'])
        try:
            fast_spectral_image(sctarget['sc3'], sctarget['sc3_tk'], str(timerange), rest_freq , suffix=f'{k2}')
        except Exception as e:
            print(f'{e}')
            pass
    tclean_continuum_image(model_dict['model_vis'], 'whole_continuum', '_contonly')