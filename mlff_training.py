import subprocess
import os
from utils import modify_incar
# ----- user data -------------------------------------------------------------
AIMDslurm = "slurm_scripts/run_perlmutter_gpu.sh"
# ---------------------------------------------------------------------------

# ----- Create the directory under mlff_training and copy POSCAR file -------------------------------------------------------------
workingDir = "mlff_training"
subprocess.call(f"cp quench_and_opt/POSCAR_OPTIMIZED {workingDir}/POSCAR", shell=True)

# ----- Copy INCAR file -------------------------------------------------------------
subprocess.call(f"cp INCAR_NPT_MLFF {workingDir}/INCAR", shell=True)

# ----- Generate and run slurm script -------------------------------------------------------------
subprocess.call(f"cp {AIMDslurm} helper_scripts/mlff_training.sh {workingDir}/run.sh", shell=True)
os.chdir(workingDir)
subprocess.call("sbatch run.sh", shell=True)