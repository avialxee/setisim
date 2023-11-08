# from casatasks import tclean, split, listobs, plotants, imstat, clearcal, visstat, flagdata, flagmanager, \
#                         uvcontsub, flagdata, gencal, plotweather, setjy, gaincal, bandpass, applycal, fluxscale, importgmrt

from setisim.calibration import CalTasks
from setisim.flagging import FlagData
import inspect

class  Lib:
    def __init__(self, config, msmeta, **kwargs):
        self.config         =   config
        self.msmeta         =   msmeta
        self.steps          =   []
        self.solve          =   False
                
    def dical(self,  scan='', timerange='', solint='int', flagbackup=False, name='i'):
        """        
        [ ] need pipeline metadata to be updated for chooosen pipeline_steps as we need previous values
        """
        # 
        gaintable=self.delay_and_bandpass( self.config, scan, timerange, solint, flagbackup)           # BUG take care of gc.scan else it fails when scan based calibration is used. Can do inside configstream
        gc=self.gain_calibration( self.config, field=self.config.flux_cal, scan=scan, timerange=timerange, solint=solint, flagbackup=flagbackup, gaintable=gaintable)
        gc.solve(caltable=gc.caltable)
        from setisim.imaging import pl_bandpass
        from casatasks import plotbandpass
        pl_bandpass(plotbandpass, self.config, self.config.refant, caltable=gc.caltable)
        
        gc.field            =   self.config.phase_cal
        gc.solve(caltable=gc.caltable)

        gc.gain             =   False
        gc.fscale           =   True
        gc.solve(caltable=gc.caltable, reference=self.config.flux_cal, transfer=self.config.phase_cal)
        
        
        gc.gaintable.append(gc.fluxtable)
        gc.field        =   self.config.flux_cal
        gc.apply(['','',self.config.flux_cal],['','', 'nearest'])
        gc.field        =   self.config.phase_cal
        gc.apply(['','',self.config.phase_cal],['','', 'nearest'])
        gc.field        =   self.config.science
        gc.apply(['','',self.config.science],['','', 'nearest'])
        return gc.tablepaths
        
    
    def gen_listobs(self):
        from casatasks import listobs
        listobs(self.config.vis, listfile=self.config.listfile, overwrite=True, verbose=True)
        
    def selfcal(self):
        pass

    def diagnostics(self, xaxis='', yaxis=''):
        from casaplotms import plotms
        from setisim.imaging import plotd
        # requires config.nchan, config.plotfolder
        if not 'nchan' in self.msmeta: nchan=2
        else: nchan         =   self.msmeta.nchan
        plotd(plotms=plotms,config=self.config, xaxis=xaxis, yaxis=yaxis, nchan=nchan)
        
    def init_flag(self,  flagbackup=False, name='i'):   
        """
        """
        F                   =   FlagData( self.config, flagbackup=flagbackup, action='apply', name=name)
        F.quacking          =   True
        F.quackinterval     =   self.config.quackinterval or 10.0
        F.quackmode         =   self.config.quackmode or 'beg'
        F.shadows           =   True
        F.clip              =   self.config.clipminmax or [0,50]
        F.inpfile           =   self.config.flagfile        
        
        from casatasks import flagdata
        F.flag(flagdata)
        

    def delay_and_bandpass(self,  scan, timerange, solint, flagbackup):
        """
        TODO : change list sequence(cal_sequence) [0]to execute sequences(T.apply)
        """
        T                   =   CalTasks(
                                        vis            =   self.config.vis,
                                        refant         =   self.config.refant, 
                                        field          =   self.config.delay_bandpass_cal,
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
                                        flux_cal       =   self.config.flux_cal
                                        )
        T.delay             =   True
        T.gain              =   True
        T.bandpass          =   True
        return T.gaintable

    def gain_calibration(self, field, scan, timerange, solint, flagbackup, gaintable):
        T                   =   CalTasks(
                                        vis            =   self.config.vis,
                                        refant         =   self.config.refant, 
                                        field          =   field,
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
                                        flux_cal       =   self.config.flux_cal
                                        )
        T.gain              =   True
        T.gaintable         =   gaintable
        
        return T
    
    def run_auxilliary(self, choosensteps=[]):
        
        aux_steps=[                                                                         # TODO : Keep all steps here for uniformity as there are two steps inside dical
            
            'self.gen_listobs',
            'self.init_flag',
            'self.dical',
            'self.diagnostics'
        ]
        if not choosensteps: choosensteps=list(range(len(aux_steps)))
        
        if self.solve:
            for i in choosensteps:
                eval(aux_steps[int(i)])()
        else:
            for i in choosensteps: self.steps.append(aux_steps[int(i)].replace('self.', '')) # HACK: remove replace self to something more intuitive