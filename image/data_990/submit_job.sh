#!/bin/bash

### Job Name
#PBS -N test
### Output Files
#PBS -o test.stdout
#PBS -e test.stderr
### Queue Name
#PBS -q low 
### Number of nodes
#PBS -l nodes=1:ppn=24


# Print the job's working directory and enter it.
echo Current directory `pwd`
echo Working directory is $PBS_O_WORKDIR
cd $PBS_O_WORKDIR
echo Current idrectory is `pwd`

# Print some other environment information
echo Runing on host `hostname`
echo Time is `date`
echo Directory is `pwd`
# Submit the command below to your job submitting system to run 3d phasing
/home/jjy/anaconda2/bin/mpirun -n 5 /home/jjy/anaconda2/bin/python /home/jjy/anaconda2/lib/python2.7/site-packages/spipy/phase/template_2d/phase.py /public/home/jjy/phase2d/Data/results/data_990/input.h5
