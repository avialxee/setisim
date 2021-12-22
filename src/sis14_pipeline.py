from casatasks import tclean, split, listobs
from pathlib import Path
from casatools import image as IA
from astropy.wcs import WCS
import matplotlib.pyplot as plt
import numpy as np
import io
import base64
from os import path, makedirs, remove, getcwd
import glob
from shutil import rmtree

def __clean_tmp(wd,cimagename):
    
    filelist = glob.glob(path.join(wd, cimagename+'.*'))
    for f in filelist:
        try:
            rmtree(f)
        except OSError:
            remove(f)

def save_fig(plt, fig, kind='base64', output='output.jpg'):
    
    if kind == 'base64':
        buf = io.BytesIO()
        fig.savefig(buf, format='png', bbox_inches='tight',
                    transparent=True, pad_inches=0)
        buf.seek(0)
        string = base64.b64encode(buf.read())
        plt.close()
        return string
    elif kind == 'plot':
        plt.show()
        return 'plotted'
    else :
        if not path.exists('output'):
            makedirs('output')
        newPath = 'output/'+output
        opt = newPath
        if path.exists(newPath):
            numb = 1
            while path.exists(newPath):
                newPath = "{0}_{2}{1}".format(
                    *path.splitext(opt) + (numb,))
                try :
                    if path.exists(newPath):
                        numb += 1 
                except:
                    pass               
        fig.savefig(newPath, format=kind, bbox_inches='tight',
                    pad_inches=0)
        print("saved {}".format(newPath))
        plt.close()
        return newPath


cwd = getcwd()
csource = str(Path.home()) + '/CASA/tests/test_d/sis14-working/sis14_twhya_selfcal.ms' # ms file as visibility input
csource_stem = str(Path(csource).stem) # filename for p1 creations

work_folder = str(Path.home()) + '/CASA/tmp/'+csource_stem+'/' # all creations inside this
if not path.exists(work_folder):
            makedirs(work_folder)
csource_smoothed = work_folder+csource_stem+'_p1.ms' # created by p1
cimagename=str(Path(csource_smoothed).stem) # created by p1 during tclean

niter=10000
field='5'
split_field='0'
threshold='15mJy'
width='8'

#listobs(csource, listfile=csource_stem+'.txt')
#with open(csource_stem+'.txt') as f:
#    print(f.read())

split(vis=csource, field=field, width=width, outputvis=csource_smoothed, datacolumn='data')

#listobs(csource_smoothed, listfile=cimagename+'.txt')
#with open(cimagename+'.txt') as f:
#    print(f.read())

tclean(vis=csource_smoothed,
       imagename=cimagename,
       field=split_field, # split had the field=5 become 0
       spw='',
       specmode='mfs',
       perchanweightdensity=True,
       gridder='standard',
       deconvolver='hogbom',
       imsize=[250,250],
       cell=['0.08arcsec'],
       mask='box [ [ 100pix , 100pix] , [150pix, 150pix ] ]',
       weighting='briggs',
       robust=0.5,
       threshold=threshold,
       niter=niter,
       interactive=False)

res_file = cimagename + '.residual'
model_file = cimagename + '.psf'

ia = IA()
ia.open(res_file)
pix = ia.getchunk()[:,:,0,0]
csys = ia.coordsys()
ia.close()

ia = IA()
ia.open(model_file)
pix_psf = ia.getchunk()[:,:,0,0]
csys = ia.coordsys()
ia.close()

rad_to_deg =  180/np.pi
w = WCS(naxis=2)
w.wcs.crpix = csys.referencepixel()['numeric'][0:2]
w.wcs.cdelt = csys.increment()['numeric'][0:2]*rad_to_deg
w.wcs.crval = csys.referencevalue()['numeric'][0:2]*rad_to_deg
w.wcs.ctype = ['RA---SIN', 'DEC--SIN']

fig = plt.figure(figsize=(20, 20))
ax1 = plt.subplot(1, 2, 1, projection=w)
p1 = int(pix.shape[0]*0.25)
p2 = int(pix.shape[0]*0.75)

im1 = ax1.imshow(pix.transpose(), origin='lower',  cmap=plt.cm.viridis)
plt.colorbar(im1, ax=ax1)
ax1.set_xlabel('Right Ascension')
ax1.set_ylabel('Declination')
ax1.set_title(f'{niter} iter of tclean\n {res_file}')
ax2 = plt.subplot(1, 2, 2, projection=w)
p1 = int(pix.shape[0]*0.25)
p2 = int(pix.shape[0]*0.75)

im2 = ax2.imshow(pix_psf[p1:p2,p1:p2].transpose(), origin='lower',  cmap=plt.cm.viridis)
plt.colorbar(im2, ax=ax2)
ax2.set_xlabel('Right Ascension')
ax2.set_ylabel('Declination')
ax2.set_title(f'{niter} iter of tclean\n {model_file}')
save_fig(plt, fig, kind='jpg')

__clean_tmp(work_folder, '*')
__clean_tmp(cwd, cimagename)
