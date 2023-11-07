import os
from pathlib import Path
from setisim.util import plt, WCS, np, colors, AnchoredSizeBar, save_fig        # type: ignore

from casatasks import tclean, imstat
from casatools import image as IA

def genpng(img, chno=0, out='output.jpg', norm_max=None, **kwargs):
    """
    TODO :
    remove unnecessary hardcoded parts of the code
    """
    ia = IA()
    ia.open(img)
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
                           cmap=plt.cm.gist_heat, interpolation="none",
                           norm=colors.CenteredNorm(0.0,norm_max))
        except:
            im = ax.imshow(pix.transpose(), origin='lower',  
                           cmap=plt.cm.gist_heat, interpolation="none",
                           norm=colors.CenteredNorm(0.0))
        
    else:
        im = ax.imshow(pix.transpose(), origin='lower',  
                       cmap=plt.cm.gist_heat, interpolation="none",
                       norm=colors.CenteredNorm(0.0))
        
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
    save_fig(plt, fig, kind, output=out+'.jpg')

def tclean_spectral_image(vis, imagename, rest_freq, suffix='', norm_max=None):
    os.system(f'rm -rf {imagename}.*')
    tclean(
        vis                     =   vis, 
        datacolumn              =   'data', 
        imagename               =   imagename, 
        spw                     =   f'0:{rest_freq}',
        specmode                =   'cube', 
        outframe                =   'bary', 
        veltype                 =   'optical', 
        restfreq                =   rest_freq, 
        niter                   =   10000, 
        threshold               =   '0.05Jy',          # type: ignore
        imsize                  =   [256,256], 
        cell                    =   '1arcsec', 
        pbcor                   =   True, 
        weighting               =   'briggs', 
        robust                  =   0.2, 
        perchanweightdensity    =   True, 
        savemodel               =   'none',
        interpolation           =   'nearest'
        )
    
    genpng(imagename+'.image',0,out=f"{imagename}"+suffix+'.bary.cube.1', norm_max=norm_max, kind='jpg')
    genpng(imagename+'.image',1,out=f"{imagename}"+suffix+'.bary.cube.1', norm_max=norm_max, kind='jpg')

def tclean_continuum_image(science_vis_cont, imagename, suffix='', norm_max=None):
    os.system(f'rm -rf {imagename} {imagename}.*')
    tclean(
        vis                     =   science_vis_cont, 
        datacolumn              =   'data', 
        imagename               =   imagename, 
        spw                     =   '0', 
        specmode                =   'mfs', 
        niter                   =   1000, 
        threshold               =   '50mJy',            # type: ignore
        imsize                  =   [256,256], 
        cell                    =   '1arcsec', 
        weighting               =   'briggs', 
        robust                  =   0.2, 
    #        savemodel='modelcolumn'
      )
    if norm_max is None:
        norm_max=imstat(imagename+'.image')['max'][0]
    genpng(imagename+'.image',0,out=f"{imagename}"+suffix+'.cont', norm_max=norm_max, kind='jpg')
    return norm_max

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