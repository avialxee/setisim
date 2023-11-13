from collections import defaultdict
import ast, glob, shutil, warnings, os, sys
import argparse, subprocess
from pathlib import Path
from importlib.metadata import version
from datetime import datetime
from pprint import pprint
from textwrap import dedent
pipedir = str(Path.home())+'/.setisim/'

c={"x":"\033[0m","g":"\033[32m", "r":"\033[31m", "b":"\033[34","c":"\033[36m","w":"\033[0m"}

def read_inputfile(folder,inputfile='config.inp'):
    """
    Read the input file and return a dictionary with the parameters.
    """
    from setisim.config import config
    params = config
    input_folder= ''
    files=glob.glob(f'{folder}/*{inputfile}',recursive=True)
    if not files: files=glob.glob(f'{folder}/*/*{inputfile}',recursive=False)
    if not files: files=glob.glob(f'{folder}/*/*/*{inputfile}',recursive=False)
    
    if files:
        input_folder = str(Path(files[-1]).parent) + '/'
        for filepath in files:
            if '.inp' in filepath:
                with open(filepath,'r') as f:
                    pr=f.read().splitlines()
                    for p in pr:
                        if '#' in p:
                            continue
                        elif '=' in p:
                            k,v=p.split('=')
                            try:
                                v=int(v)
                            except:
                                try:
                                    v=float(v)
                                except:
                                    v=str(v).strip()
                                    if any(s in v for s in ['~',',']):
                                        v=v.split(',')
                                        av=[]
                                        for a in v:
                                            if '~' in a:
                                                av=a.split('~')
                                                av=list(range(int(av[0]), int(av[1])+1))
                                            else:
                                                av+=[int(a)]
                                        v=av
                                        
                                    if ',' in v:
                                        v=v.split(',')
                                        v=[int(a) for a in v if a]
                                    
                                    elif 'True' in v: v=v.lower()=='true'
                                    elif 'False' in v:v=v.lower()=='true'
                            params[k.strip()]=v                             # type: ignore
    return params, files, input_folder


def create_config(params, out='config.inp'):
    with open(out, 'w') as o:
        for k,v in params.items():
            
            if isinstance(v,list) : 
                v=map(str, v)
                o.write(f'{k}={",".join(v)}\n')
            elif isinstance(v, range):
                o.write(f'{k}={v.start}~{v.stop}\n')
            else:
                o.write(f'{k}={v}\n')
    return out

def get_functionnames(tree=None, modulfile=None, match='', classes=True):
    """
    get list of function def names from a module tree,
    also checks function definitions insiide class definitions
    """
    if modulfile is not None: 
        with open(modulfile) as f:
            tree=ast.parse(f.read())                
    functiondefs=[]
    for elem in tree.body:                                                  # type: ignore
        if classes:
            if isinstance(elem, ast.ClassDef):
                for child in elem.body:
                    if isinstance(child, ast.FunctionDef):
                        child.parent = elem
                        if match in child.name:functiondefs.append(child.name)
        elif isinstance(elem,ast.FunctionDef): 
            if match in elem.name:functiondefs.append(elem.name)
    return functiondefs

# -------------------------  Inspired from rPicard by @Michael Janssen (https://bitbucket.org/M_Janssen/picard)
def pipeline_step(telescope='GMRT', dict=False):
    steps,_help={},''
    from setisim.lib import Lib
    from setisim.metadata import ConfigStream
    cs=ConfigStream(folder=input_folder, inputfile=files)
    cs.read()
    l=Lib(cs,'')
    l.solve=False
    l.run_auxilliary()
    # print(l.steps)
    if dict: 
        return l.steps
    else:        
        for i,k in enumerate(l.steps):_help += f"""{i}:{k}\n""" #:\t{','.join(v)}\n"""
        return dedent(_help)

def first_run():
    """
    """
    print("Please enter your monolithic casa directory (eg /path/to/casa-CASA-xxx-xxx-py3.xxx/bin/):")
    
    casadir=input()
    try:
        subprocess.run([f"{casadir}/casa",'-v'],shell=False, stdout=subprocess.DEVNULL)
    except FileNotFoundError:
        print(f"{c['r']}Failed!{c['x']} The path you entered is not a valid casa directory")
        print(f"Proceed with automatic search? (y/n):")
        auto=input()
        if str(auto).lower() in ["y", "yes"]:
            casadir=Path(str(shutil.which("casa"))).parent
            print(f"{c['g']}Success!{c['x']} Found this casa directory:{c['g']} {casadir}{c['x']}")
        if not Path(casadir / 'mpicasa').exists():
            print("Failed! mpicasa was not found")
        else:
            casadir = Path(casadir)
    subprocess.run([f"{casadir}/casa",'-v'],shell=False, stdout=subprocess.DEVNULL)
    subprocess.run([f"{casadir}/mpicasa",'-h'],shell=False, stdout=subprocess.DEVNULL)
    casa_path=f"{pipedir}/casa_path.txt"
    with open(casa_path, 'w') as o:
        o.write(f"{casadir}/")
    print(f"Written casa_path : {casa_path}")


def run_aux(config, steps, casalogf, pipedir):
    """
    TODO:run commands directly from params/config and steps
    """
    from setisim.lib import Lib
    from setisim.metadata import ConfigStream
    cs=ConfigStream(folder=input_folder, inputfile=files)
    cs.build_path = True
    cs.read()
    
    l=Lib(cs,'')
    print(f"executing following steps:")
    l.run_auxilliary(steps)
    print(l.steps)
    l.solve=True
    l.run_auxilliary(steps)
    

def run_pipe(n_cores, casadir, setisimpath, passed_cmd_args):
    """
    runs commands with mpicasa when needed
    """
    thisdate = datetime.now().strftime('%m%d_%H%M%S')
    casalogf = f'casa.log_{thisdate}'
    errlogf  = f'err.log_{thisdate}'
    casadir = open(os.path.join(pipedir, 'casa_path.txt')).read().strip()
    cmd=[]
    
    if n_cores==2:
        print("Not running MPI for -n=2")
        cmd = [str(setisimpath), '--pipe', '--casalogf', casalogf] + passed_cmd_args
    elif n_cores>2:
        cmd = [f'{casadir}/mpicasa', '--oversubscribe', '-n', str(n_cores), f'{casadir}/casa', '--agg', '--nogui', '--logfile', casalogf, '-c', str(setisimpath), '--pipe', '--casalogf', casalogf] + passed_cmd_args
    
    else:
        print(params)
        exit(0)


    if cmd and setisimpath:
        subprocess.run(cmd, stderr=open(errlogf,"+a"))
        proc = subprocess.Popen(['tail', '-n', '100', errlogf], stdout=subprocess.PIPE)
        lines = proc.stdout.read()
        print(lines.decode('utf-8'))
        if Path(casalogf).exists():
            proc = subprocess.Popen(['tail', '-n', '100', casalogf], stdout=subprocess.PIPE)
            lines = proc.stdout.read()
            print(lines.decode('utf-8'))
    

#   ----------------------------------------------------------------

parser = argparse.ArgumentParser('setisim',description=f"""pipeline for {c['c']}SETI{c['x']} {c['c']}S{c['x']}ynthesis {c['c']}Im{c['x']}aging
""", formatter_class=argparse.RawTextHelpFormatter,add_help=False)

input_params=parser.add_argument_group('input parameters',)
input_params.add_argument('-f', '--fitsfile',   type=str,   help='FITS file path')
input_params.add_argument('-t', '--timerange',  type=str,   help='input timerange for ex: 5:04:12.8~15:04:27.8')
input_params.add_argument('-sec','--seconds',  type=str,   help='input time interval for ex: 509')
input_params.add_argument('-F', '--frequency',  type=float, help='input rest frequency in MHz for ex: 599.934')
input_params.add_argument('-m',  '--ms-file',  type=str,   help='measurement set(.MS) path')
input_params.add_argument('-n', '--n-cores', type=int,   help='specify number of cores to use MPI', default=1)
input_params.add_argument('-rc','--read-config',  type=str,   help='configuration file for pipeline run', default=Path.cwd(), metavar='CONFIG_FILE')

parser.add_argument('--pipe',help='pipeline mode',action='store_true')
parser.add_argument('--casalogf',help='This file is used for storing logs from CASA task run')

operations=parser.add_argument_group('operations',)
operations.add_argument('--fitstovis',  action='store_true',  help='convert fits to visfile, requires -vis and -fits', )
operations.add_argument('--calibrate',  action='store_true',  help='calibrate the visibility file', )
operations.add_argument('--cc',         action='store_true',  help='create configuration file from default values',)
operations.add_argument('--bind',       action='store_true',  help='bind setisim with your casa path',)

args=parser.parse_known_args()[0]
parser.add_argument('-h',action='help', help="shows this help menu")
parser.add_argument('-v','--version',help='shows information on the installed version',action='store_true')

search_folder=args.read_config

params,files, input_folder=read_inputfile(str(search_folder)+'/','config.inp')
telescope=params['telescope']
pipestep=parser.add_argument_group('pipeline_step',description=f"""select calibration options for {telescope}, e.g setisim -p 0~3""",)

pipestep.add_argument('-p', '--pipe-step',   help=pipeline_step(params['telescope']), metavar='{1,2,3...}') # type: ignore


def _allvitals_check(args):
    casadir, setisimpath, status, msg=None,None,False,''
    if not Path(pipedir).exists():Path(pipedir).mkdir(parents=True,exist_ok=True)
    if not args.bind:                                                                                   # check casapath for the pipeline run
        casa_path=os.path.join(pipedir, 'casa_path.txt')
        if Path(casa_path).exists(): 
            casadir,status = open(casa_path).read().strip(),True
        else: 
            msg+=f"{c['r']}File doesn't exist!{c['x']} ({casa_path})\n use '{__name__} --bind' again! \n"
            status=False
        setisimpath = shutil.which(__name__)
        if not setisimpath: 
            warnings.warn(f'setisim is not in your PATH!', RuntimeWarning, stacklevel=2)
            setisimpath=__path__[0]
            print(f"Working with the script: {setisimpath}")
            status=True
    return casadir, setisimpath, status, msg

def _args_sanitycheck(args):
    """
    TODO: write sanity check for all arguments
    """
    msg=f"{c['r']}Failed sanity check!{c['x']}"
    if args.timerange:
        pass

def cli():
    args=parser.parse_args()
    
    timerange       =   args.timerange
    n_cores         =   args.n_cores
    fitsfile        =   args.fitsfile

    if args.ms_file: params['vis']=args.ms_file

    if args.version:
        print(version('setisim'))
    
    elif args.cc:
        print(create_config(params))
    
    elif args.bind:
        first_run()
    
    elif not args.pipe :
        casadir,setisimpath,status,msg=_allvitals_check(args)
        if status:
            strargs = []
            for k,v in vars(args).items():
                if v:
                    if str(v).lower()=='true':strargs.append(f'--{k}')
                    else: 
                        strargs.append(f"--{k.replace('_','-')}")
                        strargs.append(f'{v}')
            passed_cmd_args = strargs
            run_pipe(n_cores,casadir,setisimpath, passed_cmd_args)
        else: print(msg)
    
    elif args.pipe:
        steps=None
        if args.fitstovis:
            from casatasks import importgmrt
            if Path(fitsfile).exists():
                os.system(f'rm -rf {params["vis"]}')
                importgmrt(fitsfile=fitsfile, vis=params['vis'])
        
        
        elif args.pipe_step: 
            
            steps = args.pipe_step.split(',')
            for i,step in enumerate(steps):
                if '~' in str(step):
                    a,b=step.split('~')
                    steps.pop(i)
                    steps.extend(list(range(int(a),int(b))))
            steps.sort()
            
        casalogf=args.casalogf
        run_aux(params, steps, casalogf, pipedir)