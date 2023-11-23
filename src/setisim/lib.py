# from casatasks import tclean, split, listobs, plotants, imstat, clearcal, visstat, flagdata, flagmanager, \
#                         uvcontsub, flagdata, gencal, plotweather, setjy, gaincal, bandpass, applycal, fluxscale, importgmrt

from setisim.calibration import CalTasks
from setisim.flagging import FlagData
import os
from setisim import Path

class  Lib:
    def __init__(self, config, msmeta, **kwargs):
        self.config         =   config
        self.msmeta         =   msmeta
        self.steps          =   []
        self.solve          =   False
                
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
        find optimal value so that we get enough detections 
        from each scan for the snr of percentile population recommended.
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
        cal_vis=f"{self.config.science}_calibrated.ms"
        from casatasks import mstransform
        mstransform(vis=self.config.vis, field=self.config.science, spw=self.config.spw, datacolumn='corrected', outputvis=cal_vis)
        self.config.vis=cal_vis

    def continuum_subtraction(self):
        """
        TODO: use setisim.imaging.fast_spectral_imaging
        """
        pass

    def selfcal_setmodel(self):
        """
        TODO: Remove the continuum for background using uvcontsub.
        and then select timerange or spw for imaging.
        """
        from setisim.imaging import tclean_model
        imagename                               =   f"{Path(self.config.vis).stem}_model"
        print(imagename, self.config.vis)
        tclean_model(self.config.vis, imagename=imagename)

    def selfcal_iter(self):
        """
        """
        from setisim.imaging import tclean_selfcal_iter
        from casatasks import mstransform, imstat
        solints             =   ['8min', '7min', '4min', '3min', '1min']
        for solint in solints:
            pc              =   self.phase_calibration(field='0', 
                                    solint=solint, scan='', timerange='', flagbackup=False, gaintable=[],
                                    )
            
            itername=pc.name=   f'pselfcal_{solint}'
            visname=f"{Path(self.config.vis)}_{itername}.ms"
            pc.apply(interp =   ['linear'], applymode='calflag')
            mstransform(vis=self.config.vis, field='0', spw='0', datacolumn='corrected', outputvis=visname)
            tclean_selfcal_iter(visname, imagename=itername)
            print(imstat(visname))

        solints             =   ['2min', '2min']
        for solint in solints:
            gc              =   self.gain_calibration( 
                                    field='0', 
                                    solint=solint, scan='', timerange='', flagbackup=False, gaintable=[],
                                    )
            gc.solve(interp =   ['nearest,nearestflag'], solnorm=False, parang=True, minsnr=2.0)
            itername=gc.name=   f'gselfcal_{solint}'
            visname=f"{Path(self.config.vis)}_{itername}.ms"
            gc.apply(interp =   ['linear'], applymode='calflag')
            mstransform(vis=self.config.vis, field='0', spw='0', datacolumn='corrected', outputvis=visname)
            tclean_selfcal_iter(visname, imagename=itername)
            print(imstat(visname))
            

    def run_auxilliary(self, choosensteps=[]):
        """
        TODO: pipeline should stop after calibration and imaging code requires --timerange/ --frequency else one can use manual steps.
        """
        aux_steps=[                                                                         # TODO: Keep all steps here for uniformity as there are two steps inside dical
            
            'self.gen_listobs',
            'self.flag_init',
            'self.flag_autotfcrop',
            'self.flag_fromfile',
            'self.cal_setmodel',
            'self.cal_direction_independent',
            'self.diagnostics',
            'self.gen_flagsummary',
            'self.split_field',
            'self.selfcal_setmodel'
            
        ]
        if not choosensteps: choosensteps=list(range(len(aux_steps)))
        
        if self.solve:
            for i in choosensteps:
                eval(aux_steps[int(i)])()
        else:
            for i in choosensteps: self.steps.append(aux_steps[int(i)].replace('self.', '')) # HACK: remove replace self to something more intuitive