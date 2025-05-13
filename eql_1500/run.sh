#!/bin/bash
#SBATCH --time=144:00:00
#SBATCH --ntasks=1
#SBATCH --gres=gpu:1
#SBATCH -J test
#SBATCH -o slurm_%j.out
#SBATCH -e slurm_%j.err
module load VASP
vasp_exe=`which vasp_gam`
echo "cuda:$CUDA_VISIBLE_DEVICES"
echo "started at $(date)"
mpirun -np ${SLURM_NTASKS} $vasp_exe > vasp.out
echo "finished at $(date)"
