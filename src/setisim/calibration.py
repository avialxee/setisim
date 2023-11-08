import numpy as np
from pathlib import Path

class Cal:
    """
    Handler for calibration tasks

    -   Initialize the class with desired default parameters
    -   Call each tasks separately eg for bandpass, phase etc.
    -   tablekey and kwagrs can be used to get desired parameters and store them in the self.tablepaths with the 'tablekey' key

    :tablekey:      - used to create dictionary of tablepath by take custom keys apart from default ones.
    :modetype:      - used internally to select modes and get the right name from MODES.

    """
    MODES= {
            'K'     :   'delay',                    # Delays
            'p'     :   'phase',                    # Represents any multiplicative polarization- and time-dependent complex gain effect downstream of the polarizers.
            'B'     :   'bandpass',                 # Bandpass
            'ap'    :   'gain',
            'fs'    :   'fluxscale',
            }
    foldername                  =   'cal_tables/'
    def __init__(self, vis='', refant='', field='', scan='', spw='', minsnr=4.0, timerange='', wd='', solint='int', name=''):
        self.vis                =   vis
        self.refant             =   refant
        self.scan               =   scan
        self.field              =   field
        self.spw                =   spw
        self.minsnr             =   minsnr
        self.timerange          =   timerange
        self.solint             =   solint
        self.name               =   name
        
        self.selectdata         =   False
        
        
        self.caltable           =   ''
        self.gaintable          =   ''

        self.wd                 =   Path(wd)
        self.tablename          =   '0'
        self.tablefolder        =   self.wd / self.foldername
        self.tablepaths         =   {}                          # This keeps the table paths that can be accessed as dictioaries
        self.modetype           =   ''                          # This is used internally and should not be supplied

        

    def __gentablepath(self, *tablekeys):
        for tablekey in tablekeys: self.tablepaths[tablekey]  = self.tablefolder / f"{self.tablename}.{self.name}.{self.field}.t"
        
    def model_setjy(self, setjy, **kwargs):
        """
        TODO : check usescratch is for fresh model
        """
        self.__dict__.update(kwargs)
        setjy(
            vis                 =   self.vis, 
            field               =   self.field, 
            scan                =   self.scan, 
            scalebychan         =   True,
            standard            =   'Perley-Butler 2017',
            listmodels          =   False, 
            usescratch          =   True,
            )

    def gc_delay(self, gaincal, tablekey='K', **kwargs):
        """
        Solves for simple antenna-based delays of spectra on baselines to only the refant.
        """
        self.solint             =   'inf'
        self.modetype           =   'K'
        self.tablename          =    self.MODES[self.modetype]
        self.__gentablepath(tablekey)
        self.caltable           =   self.tablepaths[tablekey]
        self.__dict__.update(kwargs)
        gaincal(
                    vis         =   self.vis, 
                    caltable    =   self.caltable, 
                    field       =   self.field,
                    selectdata  =   self.selectdata, 
                    scan        =   self.scan,
                    solint      =   self.solint, 
                    refant      =   self.refant,
                    gaintype    =   self.modetype,
                )
        self.__gentablepath(tablekey)
    
    def gc_phase(self, gaincal, tablekey='p', **kwargs):
        """
        Represents any multiplicative polarization- and time-dependent complex gain effect downstream of the polarizers.
        """
        self.solint             =   'int'
        self.modetype           =   'p'
        self.tablename          =    self.MODES[self.modetype]
        self.__gentablepath(tablekey)
        self.caltable           =   self.tablepaths[tablekey]
        self.__dict__.update(kwargs)
        gaincal(
                    vis         =   self.vis, 
                    caltable    =   self.caltable,
                    gaintable   =   self.gaintable,                      # requires caltable from delay
                    field       =   self.field,
                    spw         =   self.spw,
                    calmode     =   self.modetype,                      # phase only
                    selectdata  =   self.selectdata, 
                    scan        =   self.scan,
                    solint      =   self.solint, 
                    refant      =   self.refant,
                    gaintype    =   'G',
                    minsnr      =   self.minsnr,
        )
        

    def bp_cal(self, bandpass, plotbandpass, tablekey='B', **kwargs):
        self.solint             =   'inf'
        self.modetype           =   'B'
        self.tablename          =    self.MODES[self.modetype]
        self.__gentablepath(tablekey)
        self.caltable           =   self.tablepaths[tablekey]
        self.__dict__.update(kwargs)        
        bandpass(
                    vis         =   self.vis, 
                    caltable    =   self.caltable,
                    gaintable   =   self.gaintable,             # requires caltable from delay
                    field       =   self.field,
                    spw         =   self.spw,
                    solnorm     =   True,
                    bandtype    =   self.modetype,
                    selectdata  =   self.selectdata, 
                    scan        =   self.scan,
                    solint      =   self.solint,
                    refant      =   self.refant,
                    minsnr      =   self.minsnr,
                    fillgaps    =   8,
                    parang      =   True,
                    interp      =   ['nearest,nearestflag','nearest,nearestflag'],
        )
        params = {'figfile':'','antenna':'C00'}
        params.update(kwargs)
        plotbandpass(caltable=self.caltable, xaxis='freq', yaxis='amp', field=self.field,**params)

    def gc_gain(self, gaincal, tablekey='AP', **kwargs):
        self.modetype           =   'ap'
        self.solint             =   'inf'
        self.tablename          =    self.MODES[self.modetype]
        self.__gentablepath(tablekey)
        self.caltable           =   self.tablepaths[tablekey]
        self.__dict__.update(kwargs)
        gaincal(
            vis                 =   self.vis,
            caltable            =   self.caltable, 
            field               =   self.field, 
            spw                 =   '0', 
            selectdata          =   False, 
            solint              =   self.solint,
            combine             =   '', 
            refant              =   self.refant,
            calmode             =   self.modetype, 
            minsnr              =   self.minsnr, 
            gaintable           =   self.gaintable
        )

    def fl_scale(self, fluxscale, reference, transfer, caltable, tablekey='F', **kwargs):
        self.modetype           =   'fs'
        self.tablename          =    self.MODES[self.modetype]
        self.__gentablepath(tablekey)
        self.caltable           =   caltable
        self.fluxtable          =   self.tablepaths[tablekey]
        self.__dict__.update(kwargs)
        fluxscale(
            vis                 =   self.vis, 
            caltable            =   self.caltable,      # this will be same between the two fields for transfer from reference to target
            fluxtable           =   self.fluxtable,     # will be used for applycal first on reference and then on target
            reference           =   reference, 
            transfer            =   transfer, 
            incremental         =   False
            )


class CalTasks(Cal):
    """
    [ ] take user input before apply for attribute
    [ ] fix the cal_seq for fluxscale, gain etc
    [ ] Remove the table files of similar name

    """
    def __init__(self, vis, refant, field, scan, spw, minsnr, timerange, wd, solint, flagbackup, phase_cal, targets, bandpass_cal, flux_cal, name='init'):
        self.vis                =   vis
        self.refant             =   refant
        self.scan               =   scan
        self.field              =   field
        self.spw                =   spw
        self.minsnr             =   minsnr
        self.timerange          =   timerange
        self.wd                 =   wd
        self.solint             =   solint
        self.flagbackup         =   flagbackup or False
        self.name               =   name
                                                            # following should be supplied from the configstream, eg assumes a list
        self.phase_cal          =   phase_cal           
        self.targets            =   targets
        self.bandpass_cal       =   bandpass_cal
        self.flux_cal           =   flux_cal

        super().__init__(self.vis, self.refant, self.field, self.scan, self.spw, self.minsnr, self.timerange, self.wd, self.solint, self.name)
        self.set_model,self.delay,self.phase,self.bandpass,self.phase_t,self.phase_inf,self.fscale,self.gain=[False]*8
        
        self.gainfield_interp   =   []

    def cal_sequence(self):
        seq_switch=[self.set_model,self.delay,self.phase,self.bandpass,self.phase_t,self.phase_inf,self.fscale,self.gain]
        seq_ind=np.where(seq_switch)[0]
        
        cal_seq = [
            (self.cal_model_setjy,  ['setjy']), 
            (self.cal_delay,        ['gaincal']), 
            (self.cal_phase,        ['gaincal']), 
            (self.cal_bandpass,     ['bandpass', 'plotbandpass']),
            (self.cal_phase_t,      ['gaincal']), 
            (self.cal_phase_inf,    ['gaincal']),
            (self.cal_fluxscale,    ['fluxscale']), 
            (self.cal_gain,         ['gaincal'])
            ]
        seq=np.empty(len(cal_seq), dtype=object)
        seq[:]=cal_seq
        return seq[seq_ind].tolist()
        
    def solve(self, **kwargs):
        from casatasks import gaincal, bandpass, setjy, fluxscale, plotbandpass
        cal_seq = self.cal_sequence()
        solved_gains=[]
        for t, v in cal_seq:
            par_list=[eval(val) for val in v]
            t(eval(*par_list), **kwargs)
            solved_gains.append(self.gaintable)
        self.gaintable = list(dict.fromkeys(solved_gains))      # keeps ordered unique values in list for python>=3.7
        
    
    def apply(self, gainfield=[], interp=[],**kwargs):
        if not len(interp): interp = ['']*len(gainfield)
        if not len(self.gainfield_interp):
            self.gainfield_interp=list(zip(gainfield,interp))
        if not len(self.gainfield_interp)==len(self.gaintable): 
            raise ValueError(f'Check if all values for (gainfield,interpolation) are inserted w.r.t gaintable for "{self.name}"')
        gainfield,interp        =   list(zip(*self.gainfield_interp))

        from casatasks import applycal
        applycal(
                    vis         =   self.vis,
                    field       =   self.field,
                    gaintable   =   self.gaintable,   #[gtab['delay'],gtab['bp'],gtab['scnph'],gtab['amp']], 
                    gainfield   =   gainfield,        #[s['bpcalf'],s['bpcalf'],s['bpcalf'],s['bpcalf']], 
                    interp      =   interp,
                    parang      =   True, 
                    calwt       =   False, 
                    # applymode =   'calflagstrict', 
                    flagbackup  =   self.flagbackup,
                    **kwargs
                )

    def cal_model_setjy(self, setjy, **kwargs):
        self.model_setjy(setjy, **kwargs)

    def cal_delay(self, gaincal, **kwargs):
        self.gc_delay(gaincal, tablekey='K', **kwargs)
        
    def cal_phase(self, gaincal, tablekey='p', **kwargs):
        self.gaintable          =   self.list_table('K')
        self.gc_phase(gaincal, tablekey, **kwargs)
        
    def cal_bandpass(self, bandpass, plotbandpass, tablekey='B', **kwargs):
        self.gaintable          =   self.list_table('p','K')
        self.bp_cal(bandpass, plotbandpass, tablekey, **kwargs)
    
    

    def cal_phase_t(self, gaincal, tablekey='pt', **kwargs):
        self.gaintable          =   self.list_table('p','K')
        self.gc_phase(gaincal, tablekey, **kwargs)

    def cal_phase_inf(self, gaincal, tablekey='pinf', **kwargs):
        self.solint             =   'inf'
        self.gaintable          =   self.list_table('p','K')
        self.gc_phase(gaincal, tablekey, **kwargs)

    def cal_fluxscale(self, fluxscale, tablekey='F', **kwargs):
        """
        caltable    :   this will be same between the two fields for transfer from reference to target
        fluxtable   :   will be used for applycal first on reference and then on target
        """
        self.fl_scale(fluxscale, tablekey=tablekey, **kwargs)

    def cal_gain(self, gaincal, tablekey='AP', **kwargs):
        self.gaintable          =   self.list_table('K','B')
        self.gc_gain(gaincal, tablekey, **kwargs)
    
    def list_table(self, *tablekeys):
        """
        Prevents Error from inserting tables which are not present.
        """
        gaintable = [self.tablepaths[tablekey] for tablekey in tablekeys if tablekey in self.tablepaths.keys()]
        return gaintable