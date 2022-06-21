import os
from pathlib import Path
from setisim import split, plotd, init_flag, flagsummary, flagdata, gaincal, applycal, listobs
from setisim.calib import solint_p

def flagger(vis, **kwargs):
    """
    Does automated flagging of bad channel and bad antenna;

    Returns
    -------
    Flagged visiblity file.

    TODO: 
    1. For badant flagging employing solution from gaincal in 'p' mode
    should have maximum solution interval?
    """
    visd={
        'f0':Path(vis).stem+'f0.MS',
        'f1':Path(vis).stem+'f1.MS',
        'f1c0':Path(vis).stem+'f1c0.MS',
        'f1c0c':Path(vis).stem+'f1c0.corrected.MS',
        'f2':Path(vis).stem+'f2.MS',
    }
    params={}
    params={'plots':False, 'flagsummary':False}
    params.update(kwargs)
    os.system(f"rm -rf {'* '.join(visd.values())}")

    metadata=listobs(vis, verbose=True)
    scanl = {k.replace('scan_', ''):v['0']['FieldName'] for k,v in metadata.items() if 'scan_' in k}
    scanlist = scanl.keys()

    m ="""# quacking, shadowing, clipping"""
    print(m)
    if params['plots']: plotd(vis)
    split(vis,visd['f0'], datacolumn='data')
    for scan in scanlist:
        init_flag(visd['f0'], quackmode='endb', scan=scan)
        init_flag(visd['f0'], quackmode='beg', scan=scan)
    if params['flagsummary']:flagsummary(visd['f0'])
    if params['plots']:plotd(visd['f0'])

    m ="""# tfcrop independently on each calibrators and target"""
    print(m)
    split(visd['f0'],visd['f1'], datacolumn='data')
    for scan in scanlist:
        flagdata(vis=visd['f1'], mode='tfcrop', spw='0', datacolumn='data', action='apply', scan=scan,
                    flagbackup=True)
        init_flag(visd['f1'], extend=True)
    if params['flagsummary']:flagsummary(visd['f1'])
    if params['plots']:plotd(visd['f1'])

    m="""# deriving phase solution to flag badant"""
    print(m)
    split(visd['f1'],visd['f1c0'], datacolumn='data')
    sol_res=solint_p(visd['f1c0'])
    tab,med=sol_res['tab'],sol_res['med']
    os.system(f'rm -rf {tab["p_96"]}')
    gaincal(visd['f1c0'], caltable=tab["p_96"], 
        solint='96s',refant='C00',calmode='p',gaintype='T', minsnr=med)
    
    m="""# applying phase solution to flag badant"""
    print(m)
    applycal(visd['f1c0'], gaintable=tab['p_96'])
    split(visd['f1c0'], visd['f1c0c'])
    if params['plots']:plotd(visd['f1c0c'])
    fs = flagsummary(visd['f1c0c'])

    m="""# using flaggable antennas to flag each scan for badant"""
    badant=','.join(fs['flaggable'].keys())
    print(f'{m}:{badant}')
    
    split(visd['f1c0c'],visd['f2'], datacolumn='data')
    for scan in scanlist:
        init_flag(visd['f2'], badant=badant, extend=True, scan=scan)
    if params['flagsummary']:flagsummary(visd['f2'])
    if params['plots']:plotd(visd['f2'])
    print(f'flagged data:{visd["f2"]}')
    return visd['f2']