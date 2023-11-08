

class FlagData:
    """
    TODO : 
    [ ]     :   tfcrop and rflag should be applied to supplied scans
    [ ]     :   inpfile to run only one instance of flagdata.
    """
    def __init__(self, config, flagbackup=False, action='apply', name=''):
        self.vis            =   config.vis
        self.refant         =   config.refant
        self.inpfile        =   config.flagfile
        self.flagbackup     =   flagbackup
        self.action         =   action
        self.name           =   name
        
        self.quacking       =   False
        self.quackinterval  =   10.0
        self.quackmode      =   'beg'

        self.shadows        =   True

        self.badant         =   ''
        self.clip           =   []

        self.tfcrop         =   False
        self.rflag          =   False

        self.cmd            =   []


    def flag(self, flagdata):
        if self.quacking    :   self.cmd.append(f"mode='quack' quackinterval={self.quackinterval} quackmode='{self.quackmode}'")
        if self.badant      :   self.cmd.append(f"mode='manual' antenna='{self.badant}'")
        if self.shadows     :   self.cmd.append(f"mode='shadow' tolerance=0.0")
        if self.clip        :   
                                # self.cmd.append(f"mode='clip' clipminmax={self.clip}")
                                self.cmd.append(f"mode='clip' clipzeros=True")
        # if self.tfcrop      :   self.cmd.append(f"")
        
        flagdata(self.vis, mode='list', inpfile=self.cmd, flagbackup=self.flagbackup, action=self.action)
        if self.inpfile: flagdata(self.vis, mode='list', inpfile=self.inpfile, flagbackup=self.flagbackup, action=self.action)    
        
        # if self.inpfile     :   
        #     with open(self.inpfile, 'r') as inp: 
        #         inptxt      =   inp.read()
        #         self.cmd.append(list(filter(bool, inptxt.splitlines())))
            
    def reset(self, flagdata, clearcal):
        flagdata(vis=self.vis, mode='unflag', field='', spw='', antenna='', timerange='')
        clearcal(vis=self.vis)
