#!/bin/bash
#SBATCH -A m697 
#SBATCH -C gpu
#SBATCH -q shared
#SBATCH -N 1
#SBATCH --ntasks-per-node=1
#SBATCH -c 32
#SBATCH --gpus-per-task=1
#SBATCH --gpu-bind=none
#SBATCH -t 00:30:00
#SBATCH -J vasp_job
#SBATCH --mail-user=xiaolin.liu@vanderbilt.edu
#SBATCH --mail-type=FAIL

module load vasp/6.4.3-gpu

# One can use up to 16 OpenMP threads-per-MPI-rank when using
#  4 GPUs-per-node.
export OMP_NUM_THREADS=16
export OMP_PLACES=threads
export OMP_PROC_BIND=spread

VASP_COMMAND="srun -n 1 -c 32 -G 1 --cpu-bind=cores --gpu-bind=none vasp_gam"
