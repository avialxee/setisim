import numpy as np

class FlagData:
    """
    TODO : 
    [ ]     :   tfcrop and rflag should be applied to supplied scans
    [ ]     :   inpfile to run only one instance of flagdata.
    """
    def __init__(self, config, flagbackup=False, action='apply', name=''):
        self.vis            =   config.vis
        self.config         =   config
        self.refant         =   config.refant
        self.inpfile        =   config.flagfile
        self.flagbackup     =   flagbackup
        self.action         =   action
        self.name           =   name
        self.flagcmd        =   config.flagcmd
        self.flagsummaryfile=   config.flagsummaryfile

        self.quacking       =   False
        self.quackinterval  =   10.0
        self.quackmode      =   'beg'

        self.shadows        =   False

        self.badant         =   ''
        self.clip           =   config.clip

        self.tfcrop         =   False
        self.rflag          =   False

        self.cmd            =   []


    def flag(self, flagdata):
        if self.quacking    :   self.cmd.append(f"mode='quack' quackinterval={self.quackinterval} quackmode='{self.quackmode}'")
        if self.badant      :   self.cmd.append(f"mode='manual' antenna='{self.badant}'")
        if self.shadows     :   self.cmd.append(f"mode='shadow' tolerance=0.0")
        if self.clip        :   self.cmd.append(f"mode='clip' clipzeros=True{f' clipminmax={self.config.clipminmax}' if self.config.clipminmax else ''}")
        if self.tfcrop      :   self.cmd.append(f"mode='tfcrop'")
        
        flagdata(self.vis, mode='list', inpfile=self.cmd, flagbackup=self.flagbackup, action=self.action, timecutoff=6.0, freqcutoff=6.0, freqfit='line')
        if self.inpfile: flagdata(self.vis, mode='list', inpfile=self.inpfile, flagbackup=self.flagbackup, action=self.action, savepars=True, overwrite=True, outfile=self.flagcmd)    
        
        if self.inpfile     :   
            with open(self.inpfile, 'r') as inp: 
                inptxt      =   inp.read()
                self.cmd.append(list(filter(bool, inptxt.splitlines())))
            
    def flagsummary(self, flagdata, **kwargs):
        
        flagsu              =   flagdata(vis=self.vis,mode='summary', name=self.name, fieldcnt=True, basecnt=True, **kwargs, )
        # flagsu            =   meta['flagsummary']        # TODO associate flagsummary with metadata object
        msg_f               =   ''
        with open(self.flagsummaryfile, 'w') as fs:
            for field_name,field_v in flagsu.items():
                if isinstance(field_v, dict):
                    percf=(field_v['flagged']/field_v['total'])*100
                    msg_f+=f"\n{field_name.ljust(10, ' ')}:\t{np.round(percf,2)}%\n"
                    for ant,ant_v in flagsu[field_name]['antenna'].items():
                        if isinstance(ant_v, dict):
                            perca=(ant_v['flagged']/ant_v['total'])*100
                            msg_f+=f"\t\t{np.round(perca,1)}%\t{ant}\n"
            print(msg_f,file=fs)
        

    def reset(self, flagdata, clearcal):
        flagdata(vis=self.vis, mode='unflag', field='', spw='', antenna='', timerange='')
        clearcal(vis=self.vis)
