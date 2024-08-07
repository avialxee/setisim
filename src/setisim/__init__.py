import ast, glob, shutil, warnings, os, sys
import argparse, subprocess
from pathlib import Path
import readline
# from collections import defaultdict
from datetime import datetime
pipedir = str(Path.home())+'/.setisim/'

python_version = sys.version_info[1]
if python_version >7:
    from importlib.metadata import version
elif python_version==7:
    from importlib_metadata import version
else:
    raise ValueError("Python version not supported")

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
                                                try:
                                                    av+=[int(a)]
                                                except:
                                                    av=v
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
    _help=''
    from setisim.lib import Lib
    l=Lib(None,'')
    l.solve=False
    l.run()
    if dict: 
        return l.steps
    else:        
        for i,k in enumerate(l.steps):_help += f"""{i}:{k}\n"""
        return _help

def first_run():
    """
    """
    readline.set_completer_delims('\t\n=')
    readline.parse_and_bind("tab: complete") 
    cp_txt,do       =   '','y'
    casa_path       =   f"{pipedir}/casa_path.txt"
    if Path(casa_path).exists():
        with open(casa_path, "r") as cp:
            cp_txt  =   cp.readlines()[0]

    if cp_txt: 
        casadir     =   cp_txt
        print(f"There is a CASA path already written: {cp_txt}")
        print(f"{c['c']} Are you sure you want to proceed overwriting?{c['x']}")
        do          =   input("(y/n)")
    if str(do).lower() in ["y", "yes"]:
        print("Please enter your monolithic casa directory (eg /path/to/casa-CASA-xxx-xxx-py3.xxx/bin/):")
               
        casadir=input()
        with open(casa_path, 'w') as o:
            o.write(f"{casadir}/")
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
    
    print(f"casa_path : {casa_path}")
    
    print(f'{c["c"]}In order to use MPI please give the path to setisim repository downloaded from github...{c["x"]}')
    print(f"\n{casadir}/pip3 install <input>")
    setisim_rep     =   input("(Enter to skip)")
    install_setisim  =   [f"{casadir}/pip3", "install", f"{setisim_rep}"]
    install_out     =   subprocess.run(install_setisim, capture_output=True).stdout
    
    print(install_out)

def exec_steps(params, steps, debug):
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
    l.run(steps)
    print(l.steps)
    l.solve=True
    if debug:
        cs.debug()
        print(f"\n\nThe Input {c['c']}Parameters{c['x']} are shown here:\n")
        print(params)
    else:
        l.run(steps)
    

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
        proc = subprocess.Popen(['tail', '-n', '5', errlogf], stdout=subprocess.PIPE)
        lines = proc.stdout.read()
        print(lines.decode('utf-8'))
        if Path(casalogf).exists():
            proc = subprocess.Popen(['tail', '-n', '5', casalogf], stdout=subprocess.PIPE)
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
input_params.add_argument('-m', '--ms-file',  type=str,   help='measurement set(.MS) path')
input_params.add_argument('-n', '--n-cores', type=int,   help='specify number of cores to use MPI', default=1)
input_params.add_argument('-rc','--read-config',  type=str,   help='configuration file for pipeline run', default=Path.cwd(), metavar='CONFIG_FILE')
input_params.add_argument('--iname', type=str,   help='imagename after tclean can be used with pipeline step for imaging.',)

parser.add_argument('--pipe',help='pipeline mode',action='store_true')
parser.add_argument('--casalogf',help='This file is used for storing logs from CASA task run')

operations=parser.add_argument_group('operations',)
operations.add_argument('--fitstoms',  action='store_true',  help='convert fits to measurement set file, requires --ms-file and --fitsfile', )
operations.add_argument('--calibrate',  action='store_true',  help='calibrate the visibility file', )
operations.add_argument('--cc',         action='store_true',  help='create configuration file from default values',)
operations.add_argument('--bind',       action='store_true',  help='bind setisim with your casa path',)
operations.add_argument('--debug',      action='store_true',  help='Show Parameters used for debugging',)

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
        t                           =   args.timerange.split('~')
        try:
            t0                      =   datetime.strptime(t[0], '%H:%M:%S.%f')
            t1                      =   datetime.strptime(t[1], '%H:%M:%S.%f')
        except Exception as e:
            print(f"{c['r']}Failed! Is {args.timerange} a valid timerange? {c['x']}\n {e}")
            exit(0)
    if args.frequency:
        if 'mhz' in args.frequency.lower():
            args.frequency.lower().replace('mhz', 'MHz')
            

def cli():
    args=parser.parse_args()
    _args_sanitycheck(args)
    timerange           =   args.timerange
    n_cores             =   args.n_cores
    fitsfile            =   args.fitsfile

    if args.ms_file     :   params['vis']       =   args.ms_file
    if args.timerange   :   params['timerange'] =   timerange
    if args.seconds     :   params['seconds']   =   args.seconds
    if args.frequency   :   params['frequency'] =   args.frequency
    if args.iname       :   params['iname']     =   args.iname
    if args.version:
        print(version('setisim'))
    
    elif args.cc:
        print(create_config(params))
    
    elif args.bind:
        first_run()
    
    elif not args.pipe :
        casadir,setisimpath,status,msg          =   _allvitals_check(args)
        if status:
            strargs     =   []
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
        if args.fitstoms:
            from casatasks import importgmrt, importuvfits
            if Path(fitsfile).exists():
                os.system(f'rm -rf {params["vis"]}')
                if 'telecope' in params:
                    if 'gmrt' in params['telescope'].lower(): importgmrt(fitsfile=fitsfile, vis=params['vis'])
                    else: importuvfits(fitsfile=fitsfile, vis=params['vis'])
        
        
        elif args.pipe_step: 
            
            steps       =   args.pipe_step.split(',')
            for i,step in enumerate(steps):
                if '~' in str(step):
                    a,b =   step.split('~')
                    steps.pop(i)
                    steps.extend(list(range(int(a),int(b)+1)))
            # steps.sort()
        # if args.seconds:

        elif args.seconds or args.timerange:
            """
            This is imaging step without any pipeline steps specified.
            """
            steps = [8,10,11]
        
        elif args.frequency:
            steps = [8,9,10,11]
        exec_steps(params, steps, args.debug)
        # ret, params["vis"]       =   exec_steps(params, steps, args.debug)
        # ret='0'
        # if ret: 
        #     if args.seconds or args.frequency or args.timerange:
        #         """
        #         Imaging step is called latter with -n 2
        #         """
        #         casadir,setisimpath,status,msg          =   _allvitals_check(args)
        #         passed_cmd_args                         =   ["--iname", ret, "-m", params["vis"], "-p", "12"]
                
        #         run_pipe(2,casadir,setisimpath, passed_cmd_args)
            
    
# from pyinstrument import Profiler
# with Profiler(interval=0.1) as profiler:     
# profiler.print()