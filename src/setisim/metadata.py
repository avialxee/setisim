from casatools import ms, msmetadata, table
from setisim import read_inputfile
from setisim import create_config

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
    """
    Is loaded first and used as lifeline of the code as long as the runtime lives
    majorly from the config file and updates during the runtime.
    """
    def __init__(self, folder='', inputfile='config.inp'):
        self.folder                 =   folder
        self.inputfile              =   inputfile
        
        self.imeta                  =   {}
        self.ifiles                 =   []
        self.wd                     =   '' 

    def attr_fromdict(self, dictconfig):
        self.config = dictconfig
        _dict = self.config
        att = AttrDict()
        att.update(_dict)
        return att

    def add(self, newconfig):
        if isinstance(newconfig, dict):
            for key in newconfig:
                    setattr(self, key, newconfig[key])

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

class MetaData(ConfigStream):
    """
    Is a super set, containinf ConfigStream and updates. Used by setisim.lib
    Also fetches metadata from the visibility file.
    Supposed to live longer than the runtime as a json based metadata file.
    """
    def __init__(self, *args, **kwargs):
          pass
     
    def dict_fromlistobs(self, listobs_dict):   # TODO listobs_dict = listobs(vis, listfile=False, verbose=True)
        fields                      =   {k.replace('field_', ''):{'name':v['name']} for k,v in listobs_dict.items() if 'field_' in k}
        # scans                       =   {k.replace('scan_', ''):v['0']['FieldName'] for k,v in listobs_dict.items() if 'scan_' in k}
        for fk in fields:
            fields[str(fk)]['scans']=[k.replace('scan_', '') for k,v in listobs_dict.items() if ('scan_' in k) and (v['0']['FieldId']==int(fk))]

    def dict_fromsmd(self, msmd):
        msmd.open(self.config.vis)
        nchan = msmd.nchan(0)
        msmd.done()
    
    def save_json(self):
        """
        a retrievable json 
        """
        pass