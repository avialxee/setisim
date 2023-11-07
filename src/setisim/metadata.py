from casatools import ms, msmetadata, table
from setisim import read_inputfile
from setisim.util import create_config

"""
TODO:
build methods to fetch scans from vis
"""


def fetch_sources(vis):
    """
    fetch calibrator and target sources from the measurement set and return dictionary
    """
    pmcalf = '0'
    pmcals = '1'

    bpcalf = '0'
    bpcals = '3'

    fdcalf = '0'
    fdcals = '1'

    targets = '2'
    targetf = '1'

    return {'pmcalf':pmcalf, 'pmcals':pmcals, 
            'bpcalf':bpcalf, 'bpcals':bpcals,
           'fdcalf':fdcalf, 'fdcals':fdcals,
           'targetf':targetf, 'targets':targets
           }

class ConfigStream:

    def __init__(self, folder='', inputfile='config.inp'):
        self.folder                 =   folder
        self.inputfile              =   inputfile
        
        self.imeta                  =   {}
        self.ifiles                 =   []
        self.wd                     =   '' 

    @classmethod
    def attr_fromdict(cls, dictconfig):
        cls.config = dictconfig
        _dict = cls.config
        att = AttrDict()
        att.update(_dict)
        return att

    def read(self):
        self.imeta, self.ifiles, self.wd    =   read_inputfile(folder='', inputfile=self.inputfile)
        self.imeta                          =   self.attr_fromdict(self.imeta)
        for key in self.imeta:
                setattr(self, key, self.imeta[key])
        
        # # TELESCOPE ----------------------------------------------------------
        # self.telescope              =   self.imeta['telescope']
        # self.refant                 =   self.imeta['refant']

        # # SOURCES ------------------------------------------------------------
        # self.phase_cal              =   self.imeta['phase_cal'].split(',')              # type: ignore
        # self.science                =   self.imeta['science'].split(',')                # type: ignore
        # self.delay_bandpass_cal     =   self.imeta['delay_bandpass_cal'].split(',')           # type: ignore
        # self.flux_cal               =   self.imeta['flux_cal'].split(',')               # type: ignore

        # # FOLDERS & FILES ----------------------------------------------------
        # self.cal_tables             =   self.imeta['cal_tables'].split(',')             # type: ignore
        # self.output_images          =   self.imeta['output_images'].split(',')          # type: ignore
        # self.listfile               =   self.imeta['listfile']

class AttrDict(dict):
    def __init__(self, *args, **kwargs):
        super(AttrDict, self).__init__(*args, **kwargs)
        self.__dict__ = self
