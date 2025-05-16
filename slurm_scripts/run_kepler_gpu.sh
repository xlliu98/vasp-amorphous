#!/bin/bash
#SBATCH --time=144:00:00
#SBATCH --ntasks=1
#SBATCH --gres=gpu:1
#SBATCH -J test
#SBATCH -o slurm_%j.out
#SBATCH -e slurm_%j.err
module load VASP
vasp_exe=$(which vasp_gam)
VASP_COMMAND="mpirun -np ${SLURM_NTASKS} $vasp_exe"
