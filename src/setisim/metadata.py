from casatools import ms, msmetadata, table
from setisim import read_inputfile
from setisim import Path
import json

"""
TODO:
build methods to fetch scans from vis
"""


class ConfigStream:
    m="""
    ConfigStream is loaded first and used as lifeline of the code as long as the runtime lives
    majorly from the config file and updates during the runtime.
    ConfigStream.__dict__ has
        imeta comes from input file, 
        config coming from default value and 
        there and the key,value pairs which are used out of the imeta, config.
    """
    
    def __init__(self, folder='', inputfile='config.inp'):
        self.folder                 =   folder
        self.inputfile              =   inputfile
        
        self.imeta                  =   {}
        self.ifiles                 =   []
        self.wd                     =   '' 
        self.build_path             =   False
    
    def debug(self):
        from setisim import c
        print(self.m)
        print(f"The {c['c']}ConfigStream{c['x']} processed is below:\n")
        print(self.__dict__)

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

    def update_path_fromkeys(self, outdir='',**kwargs):
        def create_folder(*outs, files=False):
            Path(self.imeta[outdir]).mkdir(parents=True, exist_ok=True)
            for out in outs:
                self.imeta[out]             =   Path(self.imeta[outdir]) / self.imeta[out]
                
                if not files: self.imeta[out].mkdir(parents=True, exist_ok=True)
                else: self.imeta[out]         =   str(self.imeta[out])
            
        return create_folder

    def read(self):
        self.imeta, self.ifiles, self.wd    =   read_inputfile(folder='', inputfile=self.inputfile)
        if 'scanlist' in self.imeta:
             if not isinstance(self.imeta['scanlist'],list): self.imeta['scanlist'] = str(self.imeta['scanlist']).split(',')
        if 'fields' not in self.imeta:
            fields                          =   self.imeta['science'].split(',') + self.imeta['phase_cal'].split(',') + self.imeta['delay_bandpass_cal'].split(',') + self.imeta['flux_cal'].split(',')
            self.imeta['fields']            =   list(dict.fromkeys(fields))
        if self.build_path:
            FOLDERS                         =   ['outputimages', 'bandpassplots', 'gainplots','caltables', 'plotfolder', 'imagingdumps']
            FILES                           =   ['listfile', 'flagfile', 'flagsummaryfile', 'flagcmd']
            update_path                     =   self.update_path_fromkeys('outdir')
            update_path(*FOLDERS)
            update_path(*FILES, files=True)
        
        self.imeta                          =   self.attr_fromdict(self.imeta)
        for key in self.imeta:
                setattr(self, key, self.imeta[key])
        
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
          self.metafile             =   ''
          self.metad                =   self.__dict__ # TODO : test implementation
     
    def dict_fromlistobs(self, listobs_dict):   # TODO listobs_dict = listobs(vis, listfile=False, verbose=True)
        fields                      =   {k.replace('field_', ''):{'name':v['name']} for k,v in listobs_dict.items() if 'field_' in k}
        scans                       =   {k.replace('scan_', ''):{'t0':v['0']['BeginTime'],'t1':v['0']['EndTime']} for k,v in listobs_dict.items() if 'scan_' in k}
        for fk in fields:
            fields[str(fk)]['scans']=   [k.replace('scan_', '') for k,v in listobs_dict.items() if ('scan_' in k) and (v['0']['FieldId']==int(fk))]

    def dict_fromsmd(self, msmd):
        msmd.open(self.config.vis)
        nchan = msmd.nchan(0)
        msmd.done()

    def save_metafile(self):
        """
        creates a json based metafile with the runtime ConfigStream
        """
        with open(str(self.metafile), 'w') as mf: json.dump(self.metad, mf)