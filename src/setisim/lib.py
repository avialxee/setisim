# from casatasks import tclean, split, listobs, plotants, imstat, clearcal, visstat, flagdata, flagmanager, \
#                         uvcontsub, flagdata, gencal, plotweather, setjy, gaincal, bandpass, applycal, fluxscale, importgmrt

from setisim.calibration import CalTasks
from setisim.flagging import FlagData
import os
from setisim import Path, c
from setisim.util import tolist, build_path
from astropy.time import Time, TimeDelta
import time

                # elif Path(self.vis).stem + '_calibrated'
class  Lib:
    def __init__(self, config, msmeta, **kwargs):
        self.config         =   config
        self.msmeta         =   msmeta
        self.steps          =   []
        self.solve          =   False

        self.timerange      =   ''
                
    def cal_direction_independent(self,  scan='', timerange='', solint='int', flagbackup=False, name='i'):
        """        
        TODO: need pipeline metadata to be updated for chooosen pipeline_steps as we need previous values
        """
        # 
        os.system(f"rm -rf {self.config.caltables}/*")
        
        # Initial gain calibration
        gaintable=self.delay_and_bandpass( scan, timerange, solint, flagbackup)           # BUG take care of gc.scan else it fails when scan based calibration is used. Can do inside configstream
        gc=self.gain_calibration( field=self.config.flux_cal, scan=scan, timerange=timerange, solint=solint, flagbackup=flagbackup, gaintable=gaintable)
        gc.solve(gaintable=gaintable, interp = ['nearest,nearestflag', 'nearest,nearestflag' ])

        # from setisim.imaging import pl_bandpass
        # from casatasks import plotbandpass
        # pl_bandpass(plotbandpass, self.config, self.config.refant, caltable=gc.caltable)
        
        
        # final gain calibration # TODO: change solint to a better number
        gc.field            =   self.config.flux_cal
        gc.name             =   'ii'
        gc.solve(append=False, gaintable=gaintable,interp=['nearest,nearestflag', 'nearest,nearestflag' ], minsnr=2.0, name='ii')
        
        gc.field            =   self.config.phase_cal
        gc.name             =   'ii'
        gc.solve(caltable=gc.caltable, gaintable=gaintable, append=True,interp=['nearest,nearestflag', 'nearest,nearestflag' ], minsnr=2.0,name='ii')


        gc.gain             =   False
        gc.fscale           =   True
        gc.solve(caltable=gc.caltable, reference=self.config.flux_cal, transfer=self.config.phase_cal, append=True)
        
        
        gc.gaintable.append(gc.fluxtable)
        gc.field        =   self.config.flux_cal
        gc.apply(['','',self.config.flux_cal],['','', 'nearest'])
        gc.field        =   self.config.phase_cal
        gc.apply(['','',self.config.phase_cal],['','', 'nearest'])
        gc.field        =   self.config.science
        gc.apply(['','',self.config.science],['','', 'nearest'])
        return gc.tablepaths

    

    def find_solint(self):
        """
        TODO: look for solint from list of values, 
        find optimal value so that we get enough detections at nominal SNR.
        select from each scan for the snr of percentile population recommended.
        """
        pass
    
    def gen_listobs(self):
        from casatasks import listobs
        listobs(self.config.vis, listfile=self.config.listfile, overwrite=True, verbose=True)

    def diagnostics(self, xaxis='', yaxis=''):
        from casaplotms import plotms
        from setisim.imaging import plotd
        # requires config.nchan, config.plotfolder
        if not 'nchan' in self.msmeta: nchan=2
        else: nchan         =   self.msmeta.nchan
        plotd(plotms=plotms,config=self.config, xaxis=xaxis, yaxis=yaxis, nchan=nchan)
        
    def flag_init(self,  flagbackup=False, name='i'):   
        """
        """
        F                   =   FlagData( self.config, flagbackup=flagbackup, action='apply', name=name)
        F.quacking          =   True
        F.quackinterval     =   self.config.quackinterval or 10.0
        F.quackmode         =   self.config.quackmode or 'beg'
        F.shadows           =   True
        F.clip              =   self.config.clipminmax or [0,50]
        
        
        from casatasks import flagdata
        F.flag(flagdata)

    def flag_autotfcrop(self, flagbackup=False, name='tfcrop'):
        """
        """
        F                   =   FlagData( self.config, flagbackup=flagbackup, action='apply', name=name)
        F.tfcrop            =   True
        F.clip              =   False
        F.shadows           =   False
        F.quacking          =   False
        from casatasks import flagdata
        F.flag(flagdata)

    def flag_fromfile(self, flagbackup=False, name='tfcrop'):
        """
        """
        F                   =   FlagData( self.config, flagbackup=flagbackup, action='apply', name=name)
        F.tfcrop            =   False
        F.clip              =   False
        F.shadows           =   False
        F.quacking          =   False
        
        F.inpfile           =   self.config.flagfile
        from casatasks import flagdata
        F.flag(flagdata)
        
    def gen_flagsummary(self, **kwargs):
        F                   =   FlagData( self.config, flagbackup=False, action='apply')
        F.inpfile           =   self.config.flagfile     
        from casatasks import flagdata
        F.flagsummary(flagdata)

    def delay_and_bandpass(self,  scan, timerange, solint, flagbackup):
        """
        
        """
        T                   =   CalTasks(
                                        vis            =   self.config.vis,
                                        refant         =   self.config.refant, 
                                        field          =   self.config.delay_bandpass_cal,
                                        caltables      =   self.config.caltables,
                                        scan           =   scan,
                                        spw            =   self.config.spw,
                                        minsnr         =   self.config.minsnr,
                                        timerange      =   timerange, 
                                        wd             =   self.config.wd,
                                        solint         =   solint,
                                        flagbackup     =   flagbackup,
                                        phase_cal      =   self.config.phase_cal, 
                                        targets        =   self.config.science,
                                        bandpass_cal   =   self.config.delay_bandpass_cal,
                                        flux_cal       =   self.config.flux_cal,
                                        name           =   'DK.init',
                                        )
        T.delay             =   True
        T.gain              =   True
        T.bandpass          =   True
        T.solve()
        return T.gaintable

    def gain_calibration(self, field, scan, timerange, solint, flagbackup, gaintable):
        T                   =   CalTasks(
                                        vis            =   self.config.vis,
                                        refant         =   self.config.refant, 
                                        field          =   field,
                                        scan           =   scan,
                                        caltables      =   self.config.caltables,
                                        spw            =   self.config.spw,
                                        minsnr         =   self.config.minsnr,
                                        timerange      =   timerange, 
                                        wd             =   self.config.wd,
                                        solint         =   solint,
                                        flagbackup     =   flagbackup,
                                        phase_cal      =   self.config.phase_cal, 
                                        targets        =   self.config.science,
                                        bandpass_cal   =   self.config.delay_bandpass_cal,
                                        flux_cal       =   self.config.flux_cal
                                        )
        T.gain              =   True
        T.gaintable         =   gaintable
        
        return T

    def cal_setmodel(self, flux='', scan='', timerange='', solint='int', flagbackup=False):
        T                   =   CalTasks(
                                vis            =   self.config.vis,
                                refant         =   self.config.refant, 
                                field          =   flux or self.config.flux_cal,
                                scan           =   scan,
                                caltables      =   self.config.caltables,
                                spw            =   self.config.spw,
                                minsnr         =   self.config.minsnr,
                                timerange      =   timerange, 
                                wd             =   self.config.wd,
                                solint         =   solint,
                                flagbackup     =   flagbackup,
                                phase_cal      =   self.config.phase_cal, 
                                targets        =   self.config.science,
                                bandpass_cal   =   self.config.delay_bandpass_cal,
                                flux_cal       =   self.config.flux_cal
                                )
        T.set_model         =   True
        T.solve()
        # return 
    
    def phase_calibration(self, field, scan, timerange, solint, flagbackup, gaintable):
        T                   =   CalTasks(
                                        vis            =   self.config.vis,
                                        refant         =   self.config.refant, 
                                        field          =   field,
                                        scan           =   scan,
                                        caltables      =   self.config.caltables,
                                        spw            =   self.config.spw,
                                        minsnr         =   self.config.minsnr,
                                        timerange      =   timerange, 
                                        wd             =   self.config.wd,
                                        solint         =   solint,
                                        flagbackup     =   flagbackup,
                                        phase_cal      =   self.config.phase_cal, 
                                        targets        =   self.config.science,
                                        bandpass_cal   =   self.config.delay_bandpass_cal,
                                        flux_cal       =   self.config.flux_cal
                                        )
        T.phase             =   True
        return T

    def split_field(self):
        cal_vis                                         =   f"{self.config.science}_calibrated.ms"
        datacolumn                                      =   'corrected'
        from casatasks import mstransform

        if self.config.seconds or self.config.timerange :
            i =  IMAGING(self.config.vis, self.config)
            self.config.science                         =   i.fieldname
            self.timerange                              =   i.timerange_from_instant(self.config.seconds) if self.config.seconds else self.config.timerange
            print(f"Timerange selected for splitting data: {self.timerange}")
            cal_vis                                     =   f"{i.fieldname}_time_split.ms"
            datacolumn                                  =   'data'
        
        cal_vis                                         =   build_path(cal_vis)
        mstransform(vis=self.config.vis, field=self.config.science, spw=self.config.spw, datacolumn=datacolumn, timerange=self.timerange, outputvis=cal_vis)
        
        self.config.vis=cal_vis

    def continuum_subtraction(self):
        """
        TODO: use setisim.imaging.fast_spectral_imaging
        """
        pass

    # def timerange_subtraction(self, mstransform):
    #     """
    #     TODO: create visibility file with the specified timerange.
    #     """
    #     mstransform(vis=self.config.vis, field=self.config.science, timerange=self.timerange)

    

    def selfcal_setmodel(self):
        """
        TODO: Remove the continuum for background using uvcontsub.
        and then select timerange or spw for imaging.
        """
        from setisim.imaging import tclean_model
        imagename                               =   f"{Path(self.config.vis).stem}_model"
        print(imagename, self.config.vis)
        tclean_model(self.config.vis, imagename=f"{self.config.imagingdumps}/{imagename}")

    def selfcal_iter(self):
        """
        TODO: test running this, if it is complete
        TESTED - G Jones solutions not found for all kind of solints.
        """
        from setisim.imaging import tclean_selfcal_iter, genpng
        from casatasks import mstransform, imstat
        from casatools import msmetadata
        md=msmetadata()
        md.open(self.config.vis)
        effexptime=md.effexposuretime()['value']
        
        md.close()
        print(effexptime, "is effective exposure time")
        
        if effexptime <= 120:
            solints=['int', 'int', 'int']
            print(f"Effective exposure time <= 2 minute.. So we only solve for solint='int'")
        elif effexptime >= 960:
            solints             =   ['8min', '7min', '4min', '3min', '1min']
        else :
            len_in_min          =   effexptime//60
            if len_in_min>2:
            
                solint          =   list(range(1,int(len_in_min//2)))
                solints         =   [str(sol)+'min' for sol in solint]
            else:
                solints         =   ['2min', '1min', '30s', '10s']
            solints.append('int')
        print("solints=",str(solints))
        for i,solint in enumerate(solints):
            pc              =   self.phase_calibration(field='0', 
                                    solint=solint, scan='', timerange='', flagbackup=False, gaintable=[],
                                    )
            
            itername=pc.name=   f'{Path(self.config.vis).stem}_pselfcal_{i}_{solint}'
            pc.solve(interp =   ['nearest,nearestflag'], solnorm= False, minsnr=2.0, solint=solint)
            pc.apply(interp =   ['linear'], gainfield=[''], applymode='calflag')

            visname=f"{itername}.ms"
            mstransform(vis=self.config.vis, field='0', spw='0', datacolumn='corrected', outputvis=visname)
            tclean_selfcal_iter(visname, imagename=f"{self.config.imagingdumps}/{itername}")
            
            print(imstat(f"{self.config.imagingdumps}/{itername}.image.tt0"))
        genpng(f"{self.config.imagingdumps}/{itername}.image.tt0",0,out=f"{Path(self.config.vis).stem}_{itername}", norm_max=None, kind='jpg', outfolder=self.config.outputimages)
        if effexptime <= 180:
            solints=['int', 'int']
            print(f"Effective exposure time <= 3 minute.. So we only solve for solint='int'")
        else:
            solints=['2min', '2min']
        for i,solint in enumerate(solints):
            gc              =   self.gain_calibration( 
                                    field='0', 
                                    solint=solint, scan='', timerange='', flagbackup=False, gaintable=[],
                                    )
            itername=gc.name=   f'{Path(self.config.vis).stem}_gselfcal_{i}_{solint}'
            gc.solve(interp =   ['nearest,nearestflag'], solnorm=False, parang=True, minsnr=2.0, solint=solint)
            gc.apply(interp =   ['linear'], gainfield=[''], applymode='calflag')
                        
            visname=f"{itername}.ms"
            mstransform(vis=self.config.vis, field='0', spw='0', datacolumn='corrected', outputvis=visname)
            tclean_selfcal_iter(visname, imagename=f"{self.config.imagingdumps}/{itername}")
            print(f"{self.config.imagingdumps}/{itername}.image.tt0")
        genpng(f"{self.config.imagingdumps}/{itername}.image.tt0",0,out=f"{Path(self.config.vis).stem}_{itername}", norm_max=None, kind='jpg', outfolder=self.config.outputimages)


    def run(self, choosensteps=[]):
        """
        TODO: pipeline should stop after calibration and imaging code requires --timerange/ --frequency else one can use manual steps.
        """
        lib_steps=[                                                                         # TODO: Keep all steps here for uniformity as there are two steps inside dical
            
            'self.gen_listobs',
            'self.flag_init',
            'self.flag_autotfcrop',
            'self.flag_fromfile',
            'self.cal_setmodel',
            'self.cal_direction_independent',
            'self.diagnostics',
            'self.gen_flagsummary',
            'self.split_field',
            'self.selfcal_setmodel',
            'self.selfcal_iter'
            
        ]
        if not choosensteps: choosensteps=list(range(len(lib_steps)))
        
        if self.solve:
            for i in choosensteps:
                print(f"executing {lib_steps[int(i)].replace('self.', '')}")
                eval(lib_steps[int(i)])()
        else:
            for i in choosensteps: self.steps.append(lib_steps[int(i)].replace('self.', '')) # HACK: remove replace self to something more intuitive



class IMAGING:
    from setisim.metadata import msmetadata
    md=msmetadata()
    def __init__(self, vis, config, meta=None):
        self.vis                                =   vis
        self.config                             =   config
        self.meta                               =   meta
        
        self.fieldname                          =   None
        self.fieldid                            =   0

        self._vitals_check()

    def _vitals_check(self):
        """
        Since we can only image one source per call.
        check from metadata and config file if the science target name is present and update field id
        else assume science field id=0
        """        
        if self.vis and Path(self.vis).exists():
            if self.config:
                if 'science' in self.config.__dict__:
                    print("Science is there..doing the needful")
                    self.fieldname              =   self.config.science
                    
                    self.md.open(self.vis)
                    try:
                        self.fieldid            =   self.md.fieldsforname(self.fieldname)
                    except:
                        self.fieldid            =   0
                        self.fieldname          =   tolist(self.md.namesforfields(self.fieldid))[0]

                    self.btime                  =   self.md.timesforfield(self.fieldid)[0]
                    s                           =   self.md.scansfortimes(self.btime)[0]
                    self.inttime                =   self.md.exposuretime(scan=s)['value']
                    self.metams                 =   self.md.summary()                       # TODO: make this inside metadata class
                    
                    self.md.close()
                    self.fieldid                =   tolist(self.fieldid)[0]
                
                if 'timerange' in self.config.__dict__:
                    t                           =   self.config.timerange.split('~')
                    try:
                        t0                      =   time.strptime(t[0], '%H:%M:%S.%f')
                        t1                      =   time.strptime(t[1], '%H:%M:%S.%f')
                    except Exception as e:
                        print(f"{c['r']}Failed! Is {self.config.timerange} a valid timerange? {c['x']}\n {e}")
                        exit(0)


        else:
            print(f"{c['r']}Failed! Is {self.vis} a valid path? {c['x']}")
            exit(0)

        

    def timerange_from_instant(self,ti):
        """
        This function takes time instant and creates a timerange that can be supplied to CASA task mstransform.

        Example:

        ```
        ti  =   '9~24'
        ti  =   '9'
        ```

        BUG: Fails for time between two different dates.
        """
        ti                                      =   str(ti).split('~')
        t_d0                                    =   TimeDelta(ti[0], format='sec')
        btime                                   =   Time(self.btime/24/60/60, format='mjd')
        print(btime.to_value('isot'))
        inttime                                 =   TimeDelta(self.inttime, format='sec')
        t0                                      =   btime + t_d0 - inttime#/2
        t1                                      =   btime + t_d0 + inttime#/2
        if len(ti)==2: 
                t_d1                            =   TimeDelta(ti[1], format='sec')
                t1                              =   btime + t_d1 + inttime#/2
        timerange                               =   f"{t0.strftime('%H:%M:%S.%f')}~{t1.strftime('%H:%M:%S.%f')}"

        return timerange