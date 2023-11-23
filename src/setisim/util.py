import glob, io, base64
from os import curdir, path, makedirs, remove, getcwd
from shutil import rmtree
from pprint import pprint
import numpy as np
from astropy.wcs import WCS
from matplotlib.pyplot import plot as plt
import matplotlib.colors as colors
from mpl_toolkits.axes_grid1.anchored_artists import AnchoredSizeBar

def __clear_tmp(wd,filename):
    filelist = glob.glob(path.join(wd, filename+'*'))
    for f in filelist:
        try:
            rmtree(f)
        except OSError:
            remove(f)

def exec(listtuple):
    for t in listtuple:
        print(f"{t[2]}\n")
        eval(t[0])(*t[1])

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

def find_clusters(array):
    """
    from array find if there are sub populations/clusters and give back the central values for each cluster

    TODO to find cluster use the max value and bin with a constant number suitable for dataset
    fit polynomial function to the data,
    create a bisector and see if we find more than two points
    """
    bins                        =   np.size(array)//20 or 1    # ensures that 20 datapoints are there
    max_clusters                =   2
    max_val                     =   np.max(array)

    pass
