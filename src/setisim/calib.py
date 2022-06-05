from setisim import gaincal, table
import os
from pathlib import Path
import numpy as np
from os import path, makedirs
import matplotlib.pyplot as plt

def solint_p(vis,**kwargs):
    params={'read':False}
    params.update(kwargs)
    tablefolder=f'tables/{Path(vis).stem}/'
    if not path.exists(tablefolder):
            makedirs(tablefolder)
    tab={}
    tab={
        'p_3':tablefolder+'solint_3.tb',
        'p_6':tablefolder+'solint_6.tb',
        'p_12':tablefolder+'solint_12.tb',
        'p_24':tablefolder+'solint_24.tb',
        'p_48':tablefolder+'solint_48.tb',
        'p_96':tablefolder+'solint_96.tb',
    }
    if not params['read']:
        os.system(f"rm -rf {tab['p_3']}* {tab['p_6']}* {tab['p_12']}* {tab['p_24']}* {tab['p_48']}* {tab['p_96']}*")
        gaincal(vis=vis,caltable=tab['p_3'],
            solint='int',refant='C00',calmode='p',gaintype='T', minsnr=0)
        gaincal(vis=vis,caltable=tab['p_6'],
            solint='6s',refant='C00',calmode='p',gaintype='T', minsnr=0)
        gaincal(vis=vis,caltable=tab['p_12'],
            solint='12s',refant='C00',calmode='p',gaintype='T', minsnr=0)
        gaincal(vis=vis,caltable=tab['p_24'],
            solint='24s',refant='C00',calmode='p',gaintype='T', minsnr=0)
        gaincal(vis=vis,caltable=tab['p_48'],
            solint='48s',refant='C00',calmode='p',gaintype='T', minsnr=0)
        gaincal(vis=vis,caltable=tab['p_96'],
            solint='96s',refant='C00',calmode='p',gaintype='T', minsnr=0)

    
    tb=table()
    tb.open( f"{tab['p_6']}" )
    snr_6s = tb.getcol( 'SNR' ).ravel()
    tb.close()

    tb.open( f"{tab['p_12']}" )
    snr_12s = tb.getcol( 'SNR' ).ravel()
    tb.close()

    tb.open( f"{tab['p_24']}" )
    snr_24s = tb.getcol( 'SNR' ).ravel()
    tb.close()

    tb.open( f"{tab['p_48']}" )
    snr_48s = tb.getcol( 'SNR' ).ravel()
    tb.close()

    tb.open( f"{tab['p_96']}" )
    snr_96s = tb.getcol( 'SNR' ).ravel()
    tb.close()
    
    plt.hist( snr_6s, bins=50, density=True, histtype='step', label='6 seconds' )
    plt.hist( snr_12s, bins=50, density=True, histtype='step', label='12 seconds' )
    plt.hist( snr_24s, bins=50, density=True, histtype='step', label='24 seconds' )
    plt.hist( snr_48s, bins=50, density=True, histtype='step', label='48 seconds' )
    plt.hist( snr_96s, bins=50, density=True, histtype='step', label='96 seconds' )
    plt.legend( loc='upper right' )
    plt.xlabel( 'SNR' )
    
    
    from scipy import stats
    med=int(np.median( snr_6s ) ) # TODO: change snr_6s to time resolution
    print( f"P(<={med}) = {stats.percentileofscore( snr_6s, med )}, 6s")
    print( f"P(<={med}) = {stats.percentileofscore( snr_12s, med )}, 12s")
    print( f"P(<={med}) = {stats.percentileofscore( snr_24s, med )}, 24s")
    print( f"P(<={med}) = {stats.percentileofscore( snr_48s, med )}, 48s")
    print( f"P(<={med}) = {stats.percentileofscore( snr_96s, med )}, 96s")
    return tab
