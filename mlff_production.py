import subprocess
import os
from utils import modify_incar
# ----- user data -------------------------------------------------------------
temps = list(range(300, 501, 50)) # Temperature range for MLFF production, same as in validation 
mlffSlurm = "slurm_scripts/run_perlmutter_cpu.sh" # script to run MLFF on perlmutter

# ---------------------------------------------------------------------------

# ----- Create the directory and copy POSCAR file -------------------------------------------------------------
cwd = os.getcwd()
workingDir = "mlff_production"
subprocess.call(f"cp quench_and_opt/POSCAR_OPTIMIZED {workingDir}/POSCAR", shell=True)

# ----- Copy INCAR file -------------------------------------------------------------
subprocess.call(f"cp incar_templates/INCAR_NVT_MLFF {workingDir}/INCAR", shell=True)

# ----- Link ML_FF file -------------------------------------------------------------
subprocess.call(f"ln -sf mlff_refit/ML_FF {workingDir}/ML_FF", shell=True)

# ----- Generate and run slurm script -------------------------------------------------------------
subprocess.call(f"cat {mlffSlurm} helper_scripts/mlff_production.sh >  {workingDir}/run.sh", shell=True)
os.chkdir(workingDir)
for temp in temps:
    currDir = f"{temp}K"
    os.makedirs(currDir, exist_ok=True)
    os.chdir(currDir)
    modify_incar(
        "../INCAR", "INCAR",
        {
            "TEBEG": str(temp),
            "TEEND": str(temp),
        }
    )
    subprocess.call("ln -sf ../run.sh run.sh", shell=True)
    subprocess.call("ln -sf ../POSCAR POSCAR", shell=True)
    subprocess.call("ln -sf ../ML_FF ML_FF", shell=True)
    subprocess.call("ln -sf ../../KPOINTS KPOINTS", shell=True)
    subprocess.call("ln -sf ../../POTCAR POTCAR", shell=True)
    subprocess.call("sbatch run.sh", shell=True)
    os.chdir("../")



