import subprocess
import os
from utils import modify_incar
# ----- user data -------------------------------------------------------------
temps = list(range(300, 501, 50))
AIMDslurm = "slurm_scripts/run_perlmutter_gpu_1node_1h.sh"
MLFFslurm = "slurm_scripts/run_perlmutter_cpu_1node_1h.sh"
# ---------------------------------------------------------------------------

# ----- Copy the POSCAR and ML_FF file  -------------------------------------------------------------
cwd = os.getcwd()
prevWorkingDir = "mlff_training/refit"
workingDir = "mlff_validation"
os.makedirs(workingDir, exist_ok=True)
os.chdir(workingDir)
subprocess.call(f"cp ../{prevWorkingDir}/POSCAR POSCAR", shell=True)
subprocess.call(f"ln -sf ../{prevWorkingDir}/ML_FF ML_FF", shell=True)
# ----- Copy and modify INCAR file for refit -------------------------------------------------------------
modify_incar(
    "../{prevWorkingDir}/INCAR", "INCAR",
    {
        "ML_MODE": "run",
        "NSW" : "50000"
    }
)

# ----- Generate and run slurm script -------------------------------------------------------------
os.chdir(cwd)
subprocess.call(f"cp {AIMDslurm} helper_scripts/mlff_refit.sh {workingDir}/run.sh", shell=True)
os.chdir(workingDir)
subprocess.call("sbatch run.sh", shell=True)