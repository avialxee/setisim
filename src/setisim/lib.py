# from casatasks import tclean, split, listobs, plotants, imstat, clearcal, visstat, flagdata, flagmanager, \
#                         uvcontsub, flagdata, gencal, plotweather, setjy, gaincal, bandpass, applycal, fluxscale, importgmrt

from setisim.calibration import CalTasks
from setisim.flagging import FlagData

class  Lib:
    def __init__(self, config, msmeta, **kwargs):
        self.config         =   config
        self.msmeta         =   msmeta
                
    def dical(self,  scan, timerange, solint, flagbackup, config, name='i'):
        """
        TODO:
        take care of gc.scan
        """
        
        gaintable=self.delay_and_bandpass( config, scan, timerange, solint, flagbackup)

        gc=self.gain_calibration( config, field=config.flux_cal, scan=scan, timerange=timerange, solint=solint, flagbackup=flagbackup, gaintable=gaintable)
        gc.solve(caltable=gc.caltable)
        gc.field            =   config.phase_cal
        gc.solve(caltable=gc.caltable)
        gc.gain             =   False
        gc.fscale           =   True
        gc.solve(caltable=gc.caltable, reference=config.flux_cal, transfer=config.phase_cal)
        
        gc.gaintable.extend(gc.fluxtable)
        gc.field            =   config.flux_cal
        gc.apply(['','',config.flux_cal],['','', 'nearest'])
        gc.field            =   config.phase_cal
        gc.apply(['','',config.phase_cal],['','', 'nearest'])
        gc.field            =   config.science
        gc.apply(['','',config.science],['','', 'nearest'])

        return gc.tablepaths
    
    def cal_listobs(self):
        from casatasks import listobs
        listobs(self.vis, listfile=self.config.listfile, overwrite=True, verbose=True)

    def selfcal(self):
        pass

    def diagnostics(self,  ):
        pass
        
    def init_flag(self,  config, flagbackup, name='i'):   
        """
        """
        F                   =   FlagData( config.flagfile, config.refant, flagbackup, action='apply', name=name)
        F.quacking          =   True
        F.quackinterval     =   config.quackinterval or 10.0
        F.quackmode         =   config.quackmode or 'beg'

        F.shadows           =   True
        F.clip              =   config.clipminmax or [0,50]

        F.inpfile           =   config.flagfile
        from casatasks import flagdata
        F.flag(flagdata)
        

    def delay_and_bandpass(self,  config, scan, timerange, solint, flagbackup):
        """
        TODO : change list sequence to execute sequences
        """
        T                   =   CalTasks(self.vis,
                                        refant         =   config.refant, 
                                        field          =   config.delay_bandpass_cal,
                                        scan           =   scan,
                                        spw            =   config.spw,
                                        minsnr         =   config.minsnr,
                                        timerange      =   timerange, 
                                        wd             =   config.wd,
                                        solint         =   solint,
                                        flagbackup     =   flagbackup,
                                        phase_cal      =   config.phase_cal, 
                                        targets        =   config.targets,
                                        bandpass_cal   =   config.bandpass_cal,
                                        flux_cal       =   config.flux_cal
                                        )
        T.delay             =   True
        T.gain              =   True
        T.bandpass          =   True
        T.cal_sequence()
        return T.gaintable

    def gain_calibration(self,  config, field, scan, timerange, solint, flagbackup, gaintable):
        T                   =   CalTasks(self.vis,
                                        refant         =   config.refant, 
                                        field          =   field,
                                        scan           =   scan,
                                        spw            =   config.spw,
                                        minsnr         =   config.minsnr,
                                        timerange      =   timerange, 
                                        wd             =   config.wd,
                                        solint         =   solint,
                                        flagbackup     =   flagbackup,
                                        phase_cal      =   config.phase_cal, 
                                        targets        =   config.targets,
                                        bandpass_cal   =   config.bandpass_cal,
                                        flux_cal       =   config.flux_cal
                                        )
        T.gain              =   True
        T.gaintable         =   gaintable
        
        return T
    