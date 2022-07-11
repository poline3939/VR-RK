#!/usr/bin/env python
import numpy as np
import os
import subprocess
import argparse
import logging
import ConfigParser
import sys

work_dir = None
config_default = {'parameters|detd' : 200, 'parameters|lambda' : 2.5, \
                  'parameters|detsize' : 128, 'parameters|pixsize' : 0.3, \
                  'parameters|stoprad' : 0, 'parameters|polarization' : 'x', \
                  'make_data|num_data' : 100, 'make_data|fluence' : 1e14}

def help(module):
    global config_default
    if module=="generate_config_files":
        print("This function is used to configure simulation parameters")
        print("    -> Input: pdb_file (Path of your pdb file used in simulation [/..../xx.pdb])")
        print("     *option: workpath (Choose your work directory, ABSOLUTE PATH !, default is current dir)")
        print("     *option: name (give your project a name, default is None, program will choose a name for you)")
        print("     *option: params (A dict, {'section_1|param_1': value_1, ...})\n")
        print("[Notice] Give 'workdir' parameter a None value to use current directory")
        print("[Notice] If your 'params' is a empty dict, a default config file will be generated : ")
        print(config_default)
        print("\n---- Meanings of Parameters ----")
        print("'parameters|detd' : distance between sample and detector [unit : mm]")
        print("'parameters|lambda' : wave length of laser [unit : angstrom]")
        print("'parameters|detsize' : detector size in width/height [unit : pixel]")
        print("'parameters|pixsize' : pixel size of detector [unit : mm]")
        print("'parameters|stoprad' : radius of a circle region at the center of pattern that to be masked out [unit : pixel]")
        print("'parameters|polarization' : correction due to incident beam polarization, value from 'x', 'y' or 'none'")
        print("'make_data|num_data' : how many patterns do you want to generate")
        print("'make_data|fluence' : laser fluence [unit : photons/mm^2] (usually 1e10 ~ 1e14 is reasonable for most proteins)")
        return
    elif module=="run_simulation":
        print("This function is used to start simulation")
        print("    -> Input: skip_check (skip checking files' overwriting and unusual oversampling rate, defalt = False)")
        return
    else:
        raise ValueError("No module names "+str(module))

def generate_config_files(pdb_file, workpath = None, name=None, params = {}):
    global work_dir
    if not os.path.exists(pdb_file):
        print("Error!\nGive me a valid pdb file.\nExit.")
        return
    pdb_file = os.path.abspath(pdb_file)
    if workpath is None:
        workpath = sys.path[0]
    elif not os.path.exists(workpath):
        print("Error!\nGive me a valid work directory.\nExit.")
        return
    workpath = os.path.abspath(workpath)
    # make work_dir
    if name is not None:
        work_dir = os.path.join(workpath, name)
    else:
        all_dirs = os.listdir(workpath)
        nid = 0
        for di in all_dirs:
            if di[0:9] == "simulate_" and str.isdigit(di[9:]):
                nid = max(nid, int(di[8:]))
                nid += 1
        work_dir = os.path.join(workpath, 'simulate_' + format(nid, '02d'))
    if os.path.exists(work_dir):
        print("Project "+work_dir+" has already existed, overwrite? [y/n]")
        resp = raw_input()
        if resp=='y':
            os.system("rm -r "+work_dir)
            os.mkdir(work_dir)
        else:
            raise RuntimeError("Original project exists, exit.")
    else:
        os.mkdir(work_dir)
    # copy config.ini to work dir
    path = __file__.split('/sim.py')[0] + '/config.ini'
    config = ConfigParser.ConfigParser()
    config.read(path)
    if params!={}:
        for key in params.keys():
            section, par = key.split('|')
            config.set(section, par, params[key])
    else:
        print("\n Generate default config file.")
    config.set("make_densities","pdb_code", pdb_file.split('/')[-1].split('.')[0])
    with open(work_dir + '/config.ini', 'w') as f:
        config.write(f)
    # copy /aux dir to work dir
    path = __file__.split('/sim.py')[0] + '/aux'
    cmd = "cp -r " + path + " " + work_dir
    subprocess.check_call(cmd, shell=True)
    cmd = "cp " + pdb_file + " " + work_dir + "/aux"
    subprocess.check_call(cmd, shell=True)
    # copy other files to work dir
    path = __file__.split('/sim.py')[0] + '/code/*'
    cmd = "cp -r " + path + " " + work_dir
    subprocess.check_call(cmd, shell=True)
    # mkdir
    cmd = "mkdir " + work_dir + "/data"
    subprocess.check_call(cmd, shell=True)
    # compile make_data
    print("\nPlease run 'sim.run_simulation()' after generation.")
    path = __file__.split('/sim.py')[0] + '/src'
    cmd = "cp -r " + path + " " + work_dir
    subprocess.check_call(cmd, shell=True)
    subprocess.check_call(work_dir + '/src/compile.sh', shell=True)

def run_simulation(skip_check = False):
    global work_dir
    if work_dir is None:
        print("Please run 'sim.generate_config_files(pdb_file, workdir = None, name=None, params = {})' first !")
        return   
    os.chdir(work_dir)

    config = ConfigParser.ConfigParser()
    config.read(os.path.join(work_dir,"config.ini"))
    pat_num = config.get("make_data","num_data")
    save_pdb = os.path.join(work_dir,'data/') + config.get("make_densities","pdb_code")
    cmd = 'python ' + os.path.join(work_dir,'sim_setup.py') + ' -c ' + os.path.join(work_dir,"config.ini")
    if skip_check:
        cmd = cmd + ' --skip_check'
    subprocess.check_call(cmd, shell=True)
    cmd = 'python ' + os.path.join(work_dir,'py_src/read_emc.py') + ' ' + save_pdb + ' ' + pat_num
    subprocess.check_call(cmd, shell=True)
    # delete tmp file
    cmd = 'rm -rf ' + os.path.join(work_dir,'data/densityMap.bin') + ' ' + os.path.join(work_dir,'data/det_sim.dat')\
        + ' ' + os.path.join(work_dir,'data/intensities.bin') + ' ' + os.path.join(work_dir,'data/photons.emc')\
        + ' ' + os.path.join(work_dir,'data/quaternion_buffer') + ' ' + os.path.join(work_dir,'aux/henke_table')\
        + ' ' + os.path.join(work_dir,'make_data') + ' ' + os.path.join(work_dir,'make_densities.py')\
        + ' ' + os.path.join(work_dir,'make_detector.py') + ' ' + os.path.join(work_dir,'make_intensities.py')\
        + ' ' + os.path.join(work_dir,'py_src') + ' ' + os.path.join(work_dir,'sim_setup.py')\
        + ' ' + os.path.join(work_dir,'src') + ' ' + os.path.join(work_dir,'__init__*')\
        + ' ' + os.path.join(work_dir,'aux/scattering.npy')
    subprocess.check_call(cmd, shell=True)
    # change dir arch
    cmd = 'mv ' + os.path.join(work_dir,'aux') + ' ' + os.path.join(work_dir,'input')\
        + '; mv ' + os.path.join(work_dir,'data') + ' ' + os.path.join(work_dir,'output')
    subprocess.check_call(cmd, shell=True)

    print("\n== Complete ! ==")
    print("All simulation results are stored in '" + save_pdb + ".h5'\n")
