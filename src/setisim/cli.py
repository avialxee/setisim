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
from setisim import *

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

    if pp==88:
        imagename=Path(visfile).stem+'.sc0'
        tclean(
            visfile,
            imagename=imagename,
            datacolumn='corrected',
            imsize=250, cell='0.4arcsec', 
            pblimit=-0.1,
            gridder='standard',
            deconvolver='mtmfs', 
            interactive=False, 
            weighting='briggs', robust=0.2, savemodel='none',
            niter=1000, threshold='20.5Jy',
        )
if __name__=='__main__':
    cli()