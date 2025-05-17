#!/bin/bash
#SBATCH -N 1
#SBATCH --ntasks-per-node=16
#SBATCH --cpus-per-task=16
#SBATCH -C cpu
#SBATCH -q debug
#SBATCH -J AIMD
#SBATCH --mail-user=xiaolin.liu@vanderbilt.edu
#SBATCH --mail-type=FAIL
#SBATCH -t 00:30:00
module load vasp/6.4.3-cpu
#OpenMP settings:
export OMP_NUM_THREADS=8
export OMP_PLACES=threads
export OMP_PROC_BIND=spread

VASP_COMMAND="srun -n ${SLURM_NTASKS} -c  ${SLURM_CPUS_PER_TASK} --cpu_bind=cores vasp_gam"
