import os
import shutil
import subprocess
import numpy as np


def scalePOSCAR(filePath, scale):
    lines = []
    with open(filePath, 'r') as f:
        for line in f:
            if line.strip() == "":
                break  # stop at first empty or whitespace-only line, for MD CONTCAR
            lines.append(line)
    lattice = []
    for l in range(2, 5):
        for num in lines[l].split():
            lattice.append(float(num))
    lattice = np.array(lattice).reshape(3,3)
    for i in range(3):
        lattice[i][i] *= scale

    # print(lattice)
    # print("density = ", mass/(6.023 * lattice[0][0]**3 * 0.1), "g/cm^3")
    for l in range(2, 5):
        newLine = ""
        for num in lattice[l-2]:
            newLine += "   " +  f"{num:.16f}"
        newLine += "\n"
        lines[l] = newLine
    with open("POSCAR_scaled", 'w') as newGeom:
        newGeom.writelines(lines)

if __name__ == "__main__":
    scales = [1.0 + 0.001 * i for i in range(-20,1)]
    filePath = "../quench/quench_300/CONTCAR"
    for scale in scales:
        scalePOSCAR(filePath, scale)
        last_dir = "_".join(str(scale).split("."))
        os.makedirs(last_dir, exist_ok=True)
        shutil.copy("POSCAR_scaled", last_dir + "/POSCAR")
        os.chdir(last_dir)
        subprocess.call("ln -sf ../INCAR_OPT INCAR", shell=True)
        subprocess.call("ln -sf ../KPOINTS KPOINTS", shell=True)
        subprocess.call("ln -sf ../POTCAR POTCAR", shell=True)
        subprocess.call("ln -sf ../runOPT.sh runOPT.sh", shell=True)
        subprocess.call("sbatch " + "runOPT.sh", shell=True)
        os.chdir("..")




