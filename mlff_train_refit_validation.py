import subprocess
import os
from utils import modify_incar
# ----- user data -------------------------------------------------------------
temps = list(range(300, 501, 50)) # Temperature range for MLFF validation 
trainingSlurm = "slurm_scripts/run_perlmutter_gpu.sh"
refitSlurm = "slurm_scripts/run_perlmutter_cpu_4nodes_debug.sh"
mlffSlurm = "slurm_scripts/run_perlmutter_cpu_1node_1h.sh"
mlffValidationAb = "slurm_scripts/run_perlmutter_gpu_1node_1h.sh"
mlffValidationML = "slurm_scripts/run_perlmutter_cpu_1node_1h.sh"
# ---------------------------------------------------------------------------

# ----- Create the directory under mlff_training and copy POSCAR file -------------------------------------------------------------
cwd = os.getcwd()
workingDir = "mlff_training"
subprocess.call(f"cp quench_and_opt/POSCAR_OPTIMIZED {workingDir}/POSCAR", shell=True)

# ----- Copy INCAR file -------------------------------------------------------------
subprocess.call(f"cp INCAR_NPT_MLFF {workingDir}/INCAR", shell=True)

# ----- Generate and run slurm script -------------------------------------------------------------
subprocess.call(f"cat {trainingSlurm} helper_scripts/mlff_training.sh > {workingDir}/run.sh", shell=True)
os.chdir(workingDir)
trainingJob = subprocess.run(["sbatch", "run.sh"], capture_output=True, text=True)
traingJobId = trainingJob.stdout.strip().split()[-1]

# ----- Refit -------------------------------------------------------------
os.chdir(cwd)
workingDir = "mlff_training/refit"
os.makedirs(workingDir, exist_ok=True)
os.chdir(workingDir)
# ----- Copy and modify INCAR file for refit -------------------------------------------------------------
modify_incar(
    "../INCAR", "INCAR",
    {
        "ML_MODE": "refit"
    }
)

# ----- Generate and run slurm script -------------------------------------------------------------
os.chdir(cwd)
subprocess.call(f"cat {refitSlurm} helper_scripts/mlff_refit.sh > {workingDir}/run.sh", shell=True)
os.chdir(workingDir)
refitJob = subprocess.run(["sbatch", f"--dependency=afterok:{traingJobId}", "run.sh"],
                      capture_output=True, text=True)
refitJobId = refitJob.stdout.strip().split()[-1]
print(f"Chained refit job to training job: {refitJobId} depends on {traingJobId}")



# ----- Validation -------------------------------------------------------------
os.chdir(cwd)
prevWorkingDir = workingDir
workingDir = "mlff_validation"
os.makedirs(workingDir, exist_ok=True)
subprocess.call(f"cat {mlffSlurm} helper_scripts/mlff_validation_runMD.sh > {workingDir}/runMD.sh", shell=True)
subprocess.call(f"cat {mlffValidationAb} helper_scripts/mlff_validation_runAB.sh > {workingDir}/runAB.sh", shell=True)
subprocess.call(f"cat {mlffValidationML} helper_scripts/mlff_validation_runML.sh > {workingDir}/runML.sh", shell=True)
os.chdir(workingDir)

# ----- Copy and modify INCAR file for test run -------------------------------------------------------------
modify_incar(
    f"../{prevWorkingDir}/INCAR", "INCAR",
    {
        "ML_MODE": "run",
        "NSW" : "50000"
    }
)
with open("INCAR", "a") as f:
    f.write("ML_OUTBLOCK = 20")

# ----- Generate and run slurm script -------------------------------------------------------------
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
    subprocess.call("ln -sf ../runMD.sh runMD.sh", shell=True)
    mlffMDJob = subprocess.run(["sbatch", f"--dependency=afterok:{refitJobId}", "runMD.sh"],
                      capture_output=True, text=True)
    mlffMDJobId = mlffMDJob.stdout.strip().split()[-1]
    print(f"Chained mlff MD job to refit job: {mlffMDJobId} depends on {refitJobId}")
    subprocess.call("ln -sf ../runAB.sh runAB.sh", shell=True)
    subprocess.call("ln -sf ../runML.sh runML.sh", shell=True)
    subprocess.call(f"sbatch --dependency=afterok:{mlffMDJobId} runAB.sh", shell=True)
    subprocess.call(f"sbatch --dependency=afterok:{mlffMDJobId} runML.sh", shell=True)
    os.chdir("../")



