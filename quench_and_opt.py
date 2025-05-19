import subprocess
import os

# ----- user data -------------------------------------------------------------
startTemp = 1500 # K, starting temperature for quenching, will be rounded to the nearest multiples of 300 K, guranteed to be equal to or larger than original value.
endTemp=300
step=300
# on perlmutter
AIMDslurm = "slurm_scripts/run_perlmutter_gpu_shared.sh"
=======
# on kepler
#AIMDslurm = "slurm_scripts/run_kepler_gpu.sh"
# ---------------------------------------------------------------------------

# ----- Copy equilibrated POSCAR File -------------------------------------------------------------
workingDir = "quench_and_opt"
os.makedirs(workingDir, exist_ok=True)
subprocess.call(f"cp equilibrate_and_scale/POSCAR {workingDir}/POSCAR", shell=True)

# ----- Copy INCAR file -------------------------------------------------------------
subprocess.call(f"cp incar_templates/INCAR_NVT_QUENCH {workingDir}/INCAR", shell=True)

# ----- Generate and run slurm script -------------------------------------------------------------
subprocess.call(f"cp {AIMDslurm} {workingDir}/run.sh", shell=True)

with open("helper_scripts/quench_and_opt.sh", "r") as infile, open(f"{workingDir}/run.sh", "a") as outfile:
    for line in infile:
        # Skip comments and empty lines
        stripped = line.strip()
        if "=" in stripped and not stripped.startswith("#"):
            key = stripped.split("=")[0].strip().upper()
            if key == "STARTTEMP":
                outfile.write(f"startTemp={startTemp}\n")
            elif key == "ENDTEMP":
                outfile.write(f"endTemp={endTemp}\n")    
            elif key == "STEP":
                outfile.write(f"step={step}\n")
            else:
                outfile.write(line)
        else:
            outfile.write(line)
os.chdir(workingDir)
subprocess.call("sbatch run.sh", shell=True)
