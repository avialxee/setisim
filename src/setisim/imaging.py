import os
from pathlib import Path
import matplotlib

from matplotlib import pyplot as plt
from astropy.wcs import WCS
# from matplotlib.pyplot import plot as plt
import matplotlib.colors as colors
from mpl_toolkits.axes_grid1.anchored_artists import AnchoredSizeBar
from setisim.util import np, save_fig        # type: ignore
from pyvirtualdisplay import Display
from setisim.util import tolist
from casatasks import tclean, imstat
from casatools import image as IA
old_matplotlib      = False
if int(matplotlib.__version__.split('.')[1])<=3:
    old_matplotlib  = True
    print(f"Using older version of matplotlib...")
    from matplotlib.colors import Normalize

def genpng(img, chno=0, out='output.jpg', norm_max=None,outfolder='output', **kwargs):
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
    if old_matplotlib:
        norm=Normalize()
    elif norm_max:
        try:
            norm_max=float(norm_max)
            norm=colors.CenteredNorm(0.0,norm_max)
            
        except:
            norm=colors.CenteredNorm(0.0)         
        
    else:
        norm=colors.CenteredNorm(0.0)
    
    
    
    im = ax.imshow(pix.transpose(), origin='lower',  
                           cmap=plt.cm.gist_heat, interpolation="none",
                           norm=norm)
        
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
    save_fig(plt, fig, kind, output=out+'.jpg', outfolder=outfolder)

def tclean_spectral_image(vis, imagename, rest_freq, suffix='', norm_max=None, threshold='0.05Jy'):
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
        threshold               =   threshold,          
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

def plotd(plotms, config, z=1.5, xax=[], yax=[], model=False, **kwargs):
    """
    for quick views you can select small timerange and averaged channel etc.
    TODO setisim 0.3 Milestone : A new tool is developed for plotting data without the casaplotms tool in VASCO, 
    a dependency on VASCO can be helpful.
    """
    

    plotfolder              =   config.plotfolder
    if not Path(plotfolder).exists(): Path(plotfolder).mkdir(parents=True,exist_ok=True)
    print(f'plotting in folder: {plotfolder}')
    
    vis = config.vis
    params={
            'spw'           :   '',#f'0:{int(nchan*0.4)}~{int(nchan*0.6)}',
            'nchan'         :   '',
            'uvrange'       :   '',
            'antenna'       :   '',
            'scan'          :   '',
            'corr'          :   '',
            'w'             :   4096,
            'h'             :   2880,
            }
    
    params.update(kwargs)
    w=params['w']
    h=params['h']
    sources                 =   config.scanlist or config.fields
    
    display = Display(visible=0,size=(w,h))
    
    if z: w,h=int(w/z),int(h/z)

    display.start()


    if not params['nchan']: print("avgchannel might fail as nchan is missing")
    spw, uvrange, antenna = params['spw'], params['uvrange'], params['antenna']
    print(f"spw={spw}, nchan={params['nchan']}, uvrange={uvrange}, antenna={antenna}")
    
    plot_dictcomb={
        'amp':
                   {'freq'  :   {'averagedata':True,'avgtime':'1e9', 'avgbaseline':False, 'avgchannel':''},
                    'time'  :   {'averagedata':False,'avgtime':'', 'avgbaseline':False, 'avgchannel':''},
                    'uvwave':   {'averagedata':False,'avgtime':'', 'avgbaseline':False, 'avgchannel':''},
                    'uvidist':  {'averagedata':False,'avgtime':'', 'avgbaseline':False, 'avgchannel':''}
                    }, 
        'phase':
                    {'freq' :   {'averagedata':True,'avgtime':'1e9', 'avgbaseline':False, 'avgchannel':''},
                    'time'  :   {'averagedata':True,'avgtime':'', 'avgbaseline':True, 'avgchannel':params['nchan']},
                    'uvwave':   {'averagedata':False,'avgtime':'', 'avgbaseline':False, 'avgchannel':params['nchan']},
                    'amp'   :   {'averagedata':True,'avgtime':'1e9', 'avgbaseline':False, 'avgchannel':''}
              },
     }
                         
    try:
        msg = "Finished Successfully!"
        for source in sources:
            source                              =   source_name=str(source)
            field                               =   source if (config.fields and not config.scanlist) else ''
            scan                                =   source if config.scanlist else ''
            if len(yax): 
                for yaxes in yax: plot_dictcomb =   {k: plot_dictcomb[k] for k in plot_dictcomb if plot_dictcomb[k]==yaxes}
            if len(xax):
                for xaxes in xax: plot_dictcomb =   {k: plot_dictcomb[k] for k in plot_dictcomb if k==xaxes}
                
            for yaxis,xaxes in plot_dictcomb.items():
                for xaxis,avgdata in xaxes.items():
                    print(f'{yaxis} vs {xaxis} - {source_name}')
                    plotms(
                            vis                 =   vis, 
                            field               =   field, 
                            scan                =   scan,
                            antenna             =   antenna, spw=spw, correlation=params['corr'],
                            xaxis               =   xaxis, 
                            yaxis               =   yaxis,
                            coloraxis           =   'corr', 
                            title               =   f'{source_name}:{yaxis} vs {xaxis}',
                            showgui             =   False,
                            averagedata         =   avgdata['averagedata'], 
                            avgtime             =   avgdata['avgtime'],
                            avgbaseline         =   avgdata['avgbaseline'],
                            avgchannel          =   str(avgdata['avgchannel']),
                            uvrange             =   uvrange,
                            plotfile            =   str(plotfolder / f"{yaxis}_v_{xaxis}.{source_name}.png"),
                            width               =   int(w),
                            height              =   int(h),
                            overwrite           =   True,
                            clearplots          =   True,
                            highres             =   False, 
                            customsymbol        =   True, 
                            symbolshape         =   'square',
                            flaggedsymbolshape  =   'square',
                            xaxisfont           =   22,
                            yaxisfont           =   22,
                            titlefont           =   22,
                            ydatacolumns        =   'model' if model else ''
                        )

    except Exception as e:
        msg=str(e)
            
    finally:
        display.stop()
        print(f"STOPPED : {msg}")


def tclean_model(vis, imagename, imsize=900, cell='1.0arcsec', threshold='1.0mJy', parallel=False):
    """
    parameters selected from the NCRA CASA tutorial by Ruta Kale : http://www.ncra.tifr.res.in/~ruta/ras-tutorials/CASA-tutorial.html
    Running two iterations so that a Ctrl-C command wont corrupt the visibilities.
    """
    steps, savemodel, restoration, calcpsf, calcres, niter = [0,1], ['none', 'modelcolumn'], [True, False], [True, False], [True, False], [2000, 0]
    for i in steps:
        tclean(
                                vis             =   vis, 
                                imagename       =   imagename,
                                selectdata      =   True,
                                field           =   '0',
                                spw             =   '0',
                                imsize          =   imsize,
                                cell            =   cell, 
                                robust          =   0,
                                weighting       =   'briggs',
                                specmode        =   'mfs',
                                nterms          =   1,
                                niter           =   niter[i],
                                usemask         =   'auto-multithresh',
                                minbeamfrac     =   0.1,
                                smallscalebias  =   0.6,
                                threshold       =   threshold,
                                pblimit         =   -1,
                                deconvolver     =   'mtmfs',
                                gridder         =   'wproject',
                                wprojplanes     =   -1,
                                wbawp           =   False,
                                restoration     =   restoration[i],
                                savemodel       =   savemodel[i],
                                cyclefactor     =   0.5,
                                parallel        =   parallel,
                                calcpsf         =   calcpsf[i],
                                calcres         =   calcres[i],
                                interactive     =   False)
    
    print(f"Model Created successfully!  -\t\t{imagename}")    
    return imagename

def tclean_selfcal_iter(vis, imagename, imsize=900, cell='1.0arcsec', threshold='0.5mJy', parallel=False, niter=3000):
    return tclean(                     
                                vis             =   vis, 
                                imagename       =   imagename,
                                selectdata      =   True,
                                field           =   '0',
                                spw             =   '0',
                                imsize          =   imsize,
                                cell            =   cell, 
                                robust          =   0,
                                weighting       =   'briggs',
                                specmode        =   'mfs',
                                nterms          =   1,
                                niter           =   niter,
                                usemask         =   'auto-multithresh',
                                minbeamfrac     =   0.1,
                                smallscalebias  =   0.6,
                                threshold       =   threshold,
                                pblimit         =   -1,
                                deconvolver     =   'mtmfs',
                                gridder         =   'wproject',
                                wprojplanes     =   128,
                                wbawp           =   False,
                                restoration     =   True,
                                savemodel       =   'modelcolumn',
                                cyclefactor     =   0.3,
                                parallel        =   parallel,
                                interactive     =   False
            )
    
# def fast_spectral_image(vis, cvis, timerange, rest_freq , suffix):
#     os.system(f'rm -rf {cvis}')
#     split(calvis, cvis, timerange=timerange, datacolumn='data')
#     uvcontsub(cvis, field='0',
#           fitspw=f'0:{rest_freq}', excludechans=True,
#           fitorder=1,
#           want_cont=True,
#          )
#     science_vis=cvis+'.contsub'
#     science_vis_cont=cvis+'.cont'
#     norm_max=tclean_continuum_image(science_vis_cont, science_vis_cont+'.cimage', suffix=suffix+'.cont')
#     tclean_spectral_image(science_vis, science_vis+'.cimage', rest_freq, suffix=suffix+'.cube', norm_max=norm_max)


# def selfcal_all(calibrated_csource, rest_freq):
    
    
#     calibrated_target=ctarget_stem+f'_field{s["targetf"]}.MS'
#     rest_freq= '599.934021MHz'

#     split(calibrated_csource, calibrated_target, datacolumn='data', field=s['targetf'])
#     model_dict=selfcal_model(calibrated_target)
#     t_duration = 12 # total time duration (seconds)
#     t_step = 12 # t_step seconds for imaging as time step in between the total duration
#     sctarget={}
#     sctarget['sc3'],sctarget['sc3_t']= model_dict['model_vis'], model_dict['model_vis']+'_spectral_image'
    
#     for i in range(5,t_duration,t_step): # 
#         k1 =i
#         k2 =k1+t_step
#         sctarget['sc3_tk']=sctarget['sc3_t']+f'{k1}_{k2}.MS'
#         timerange=f'15:04:{k1:02d}.8~15:04:{k2:02d}.8'
#         print(timerange)    
#         print(sctarget['sc3_tk'])
#         try:
#             fast_spectral_image(sctarget['sc3'], sctarget['sc3_tk'], str(timerange), rest_freq , suffix=f'{k2}')
#         except Exception as e:
#             print(f'{e}')
#             pass
#     tclean_continuum_image(model_dict['model_vis'], 'whole_continuum', '_contonly')

