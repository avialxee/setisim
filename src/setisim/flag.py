import os
from pathlib import Path
from setisim import split, plotd, init_flag, flagsummary, flagdata, gaincal, applycal
from setisim.calib import solint_p

def flagger(vis, **kwargs):
    visd={
        'f0':Path(vis).stem+'f0.MS',
        'f1':Path(vis).stem+'f1.MS',
        'f2':Path(vis).stem+'f2.MS',
        'f2c0':Path(vis).stem+'f2c0.MS',
        'f2c0c':Path(vis).stem+'f2c0.corrected.MS',
        'f3':Path(vis).stem+'f3.MS',
    }
    params={}
    params={'plots':False, 'flagsummary':False}
    params.update(kwargs)
    os.system(f"rm -rf {'* '.join(visd.values())}")

    m ="""# quacking, shadowing, clipping"""
    print(m)
    if params['plots']: plotd(vis)
    split(vis,visd['f0'], datacolumn='data')
    for scan in ['1','2','3']:
        init_flag(visd['f0'], quackmode='endb', scan=scan)
        init_flag(visd['f0'], quackmode='beg', scan=scan)
    if params['flagsummary']:flagsummary(visd['f0'])
    if params['plots']:plotd(visd['f0'])

    m ="""# tfcrop independently on each calibrators and target"""
    print(m)
    split(visd['f0'],visd['f1'], datacolumn='data')
    for scan in ['1','2','3']:
        flagdata(vis=visd['f1'], mode='tfcrop', spw='0', datacolumn='data', action='apply', scan=scan,
                    flagbackup=True)
        init_flag(visd['f1'], extend=True)
    if params['flagsummary']:flagsummary(visd['f1'])
    if params['plots']:plotd(visd['f1'])

    m="""# deriving phase solution to flag badant"""
    print(m)
    split(visd['f2'],visd['f2c0'], datacolumn='data')
    sol_res=solint_p(visd['f2c0'])
    tab,med=sol_res['tab'],sol_res['med']
    os.system(f'rm -rf {tab["p_96"]}')
    gaincal(visd['f2c0'], caltable=tab["p_96"], 
        solint='96s',refant='C00',calmode='p',gaintype='T', minsnr=med)
    applycal(visd['f2c0'], gaintable=tab['p_96'])
    split(visd['f2c0'], visd['f2c0c'])
    if params['plots']:plotd(visd['f2c0c'])
    
    m="""# using flaggable antennas to flag each scan for badant"""
    print(m)
    badant=fs['flaggable'].keys()

    split(visd['f2c0c'],visd['f3'], datacolumn='data')
    for scan in ['1','2','3']:
        init_flag(visd['f3'], badant=','.join(badant), extend=True, scan=scan)
    if params['flagsummary']:flagsummary(visd['f3'])
    if params['plots']:plotd(visd['f3'])
    print(f'flagged data:{visd["f3"]}')