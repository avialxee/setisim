# from casatasks import tclean, split, listobs, plotants, imstat, clearcal, visstat, flagdata, flagmanager, \
#                         uvcontsub, flagdata, gencal, plotweather, setjy, gaincal, bandpass, applycal, fluxscale, importgmrt

from setisim.calibration import CalTasks
from setisim.flagging import FlagData
import inspect

class  Lib:
    def __init__(self, config, msmeta, **kwargs):
        self.config         =   config
        self.msmeta         =   msmeta
        self.steps          =   {}
        self.solve          =   False
                
    def dical(self,  scan='', timerange='', solint='int', flagbackup=False, name='i'):
        """
        BUG take care of gc.scan else it fails when scan based calibration is used.

        """
        
        gaintable=self.delay_and_bandpass( self.config, scan, timerange, solint, flagbackup)
        gc=self.gain_calibration( self.config, field=self.config.flux_cal, scan=scan, timerange=timerange, solint=solint, flagbackup=flagbackup, gaintable=gaintable)
        
        if self.solve:gc.solve(caltable=gc.caltable)
        else: self._sanitized_stepslist([gc.cal_sequence()[0]])
        gc.field            =   self.config.phase_cal
        
        if self.solve:gc.solve(caltable=gc.caltable)
        else:self._sanitized_stepslist([gc.cal_sequence()[0]])
        gc.gain             =   False
        gc.fscale           =   True
        
        if self.solve:gc.solve(caltable=gc.caltable, reference=self.config.flux_cal, transfer=self.config.phase_cal)
        else:self._sanitized_stepslist([gc.cal_sequence()[0]])
        
        if self.solve:
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
        if self.solve:listobs(self.config.vis, listfile=self.config.listfile, overwrite=True, verbose=True)
        else: self._sanitized_stepslist([('listobs','gen_listobs')])

    def selfcal(self):
        pass

    def diagnostics(self,  ):
        if not self.solve: self._sanitized_stepslist([('diagnostic_plot','')])
        pass
        
    def init_flag(self,  flagbackup=False, name='i'):   
        """
        """
        F                   =   FlagData( self.config.flagfile, self.config.refant, flagbackup=flagbackup, action='apply', name=name)
        F.quacking          =   True
        F.quackinterval     =   self.config.quackinterval or 10.0
        F.quackmode         =   self.config.quackmode or 'beg'

        F.shadows           =   True
        F.clip              =   self.config.clipminmax or [0,50]

        F.inpfile           =   self.config.flagfile
        from casatasks import flagdata
        if self.solve:F.flag(flagdata)
        else: self._sanitized_stepslist([(F.flag,'flagdata')])
        

    def delay_and_bandpass(self,  config, scan, timerange, solint, flagbackup):
        """
        TODO : change list sequence(cal_sequence) [0]to execute sequences(T.apply)
        """
        T                   =   CalTasks(
                                        vis            =   config.vis,
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
                                        targets        =   config.science,
                                        bandpass_cal   =   config.delay_bandpass_cal,
                                        flux_cal       =   config.flux_cal
                                        )
        T.delay             =   True
        T.gain              =   True
        T.bandpass          =   True
        self._sanitized_stepslist(T.cal_sequence()[0])
        return T.gaintable

    def gain_calibration(self,  config, field, scan, timerange, solint, flagbackup, gaintable):
        T                   =   CalTasks(
                                        vis            =   config.vis,
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
                                        targets        =   config.science,
                                        bandpass_cal   =   config.delay_bandpass_cal,
                                        flux_cal       =   config.flux_cal
                                        )
        T.gain              =   True
        T.gaintable         =   gaintable
        
        return T
    
    def run_auxilliary(self, choosensteps=[]):
        
        aux_steps=[                                                     # TODO : Keep all steps here for uniformity as there are two steps inside dical
            
            self.gen_listobs,
            self.init_flag,
            self.dical,
            self.diagnostics
        ]
        if not choosensteps: choosensteps=list(range(len(aux_steps)))
        for i in choosensteps:
            aux_steps[int(i)]()

    def _sanitized_stepslist(self, listtuple, intent='calibration'):
        t=''
        try:
            step=str(inspect.currentframe().f_back.f_code.co_name)      # TODO : test this for pypi installation compatibility or runtime issues
        except:
            step=intent
        if not step in self.steps.keys(): self.steps[step]=[]
        for tup in listtuple:
            if isinstance(tup, list):
                for t in tup:
                    t=t[0].__name__
            else:
                if not isinstance(tup,str):
                    if isinstance(tup,tuple):
                        if isinstance(tup[0],str):t=tup[0]
                        else:t=tup[0].__name__
                    else:
                        t=tup.__name__
                else: t=tup
            self.steps[step].append(t)