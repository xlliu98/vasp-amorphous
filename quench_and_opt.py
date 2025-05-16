import subprocess
import os

# ----- user data -------------------------------------------------------------
startTemp = 1500 # K, starting temperature for quenching, will be rounded to the nearest multiples of 300 K, guranteed to be equal to or larger than original value.
endTemp=300
step=300
AIMDslurm = "run_kepler_gpu.sh"
# ---------------------------------------------------------------------------

# ----- Copy equilibrated POSCAR File -------------------------------------------------------------
workingDir = "quench_and_opt"
os.mkdir(workingDir, exist_ok=True)
subprocess.call(f"cp equilibrate_and_scale/POSCAR {workingDir}/POSCAR", shell=True)

# ----- Copy INCAR file -------------------------------------------------------------
subprocess.call(f"cp INCAR_NVT_QUENCH {workingDir}/INCAR", shell=True)

# ----- Generate and run slurm script -------------------------------------------------------------
subprocess.call(f"cp {AIMDslurm} {workingDir}/run.sh", shell=True)

with open("quench_and_opt.sh", "r") as infile, open(f"{workingDir}/run.sh", "a") as outfile:
    for line in infile:
        # Skip comments and empty lines
        stripped = line.strip()
        if "=" in stripped and not stripped.startswith("#"):
            key = stripped.split("=")[0].strip().upper()
            if key == "STARTTEMP":
                outfile.write(f"startTemp = {startTemp}\n")
                continue
            elif key == "ENDTEMP":
                outfile.write(f"endTemp = {endTemp}\n")
                continue    
            elif key == "STEP":
                outfile.write(f"step = {step}\n")
                continue
            else:
                outfile.write(line)
        else:
            outfile.write(line)
os.chdir(workingDir)
subprocess.call("sbatch run.sh", shell=True)