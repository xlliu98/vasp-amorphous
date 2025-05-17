import subprocess
import os

# ----- user data -------------------------------------------------------------
AIMDslurm = "slurm_scripts/run_perlmutter_cpu_4nodes_debug.sh"
# ---------------------------------------------------------------------------

# ----- Copy a dummy POSCAR file  -------------------------------------------------------------
cwd = os.getcwd()
workingDir = "mlff_training/refit"
os.makedirs(workingDir, exist_ok=True)
os.chdir(workingDir)
subprocess.call(f"cp ../POSCAR POSCAR", shell=True)

# ----- Copy and modify INCAR file for refit -------------------------------------------------------------
modify_incar(
    "../INCAR", "INCAR",
    {
        "ML_MODE": "refit"
    }
)

# ----- Generate and run slurm script -------------------------------------------------------------
os.chdir(cwd)
subprocess.call(f"cp {AIMDslurm} helper_scripts/mlff_refit.sh {workingDir}/run.sh", shell=True)
os.chdir(workingDir)
subprocess.call("sbatch run.sh", shell=True)