import re
import subprocess
import os
from utils import *
# ----- user data -------------------------------------------------------------
molar_masses = {"Li": 6.9410, "Ta": 180.94788, "Cl": 35.45}     # g mol⁻¹
stoich       = {"Li": 1, "Ta": 1, "Cl": 6}                      # LiTaCl₆
density      = 2.96                      # g cm⁻³
melting_point = 1500 # K, will be rounded to the nearest multiples of 300 K, guranteed to be equal to or larger than original value.
box_diam     = 12.0                      # Å
potcarDict = {"Li": "Li", "Ta": "Ta_pv", "Cl": "Cl"}  # use a lower ENMAX for Li
# on perlmutter
packmolPath = "/pscratch/sd/x/xlliu9/Software/packmol/packmol"
potcarPath = "/global/common/software/nersc9/vasp/dependencies/pseudopotentials/PBE/potpaw_PBE.64"
AIMDslurm = "slurm_scripts/run_perlmutter_gpu.sh"

# on kepler
# packmolPath = "/home/xiaolin/software/packmol-20.15.2/packmol"
# potcarPath = "/home/xiaolin/VASP/paw-pbe-64"
# AIMDslurm = "slurm_scripts/run_kepler_gpu.sh"

# ---------------------------------------------------------------------------

# ----- Generate POSCAR File -------------------------------------------------------------
# Write pdb files for packmol input
pdbTemplate = (
    "HETATM    1  {el:<2}  {el:<3}A   1       0.000   0.000   0.000  1.00  0.00           {el:>2}\n"
    "END\n"
)

for el in stoich.keys():
    with open(f"{el}.pdb", "w") as f:
        f.write(pdbTemplate.format(el=el))
        print(f"Wrote {el}.pdb")
NA           = 6.022_140_76e23           # mol⁻¹  (exact) 
# 1. mass of one formula unit
M_formula = sum(molar_masses[e] * n for e, n in stoich.items())   # g/mol

# 2. volume of the simulation region (cm³)
V_cm3 = (box_diam**3) * 1e-24             # Å³ → cm³



# 3. number of formula units that match the target density
m_sample   = density * V_cm3                 # g
n_moles    = m_sample / M_formula            # mol
n_formula  = n_moles * NA                    # dimensionless
n_formula_rounded = int(n_formula + 1)  # closest whole molecule

# 4. atoms per element
atom_counts = {e: n * n_formula_rounded for e, n in stoich.items()}

# 4. compute exact diameter using the number of formula
n_moles_exact = n_formula_rounded / NA
V_cm3_exact = n_moles_exact * M_formula / density
box_diam_exact = (V_cm3_exact * 1e24)**(1/3)  # cm³ → Å³

print(f"Formula units     : {n_formula_rounded:.2f}")
print(f"Box diameter     : {box_diam_exact:.16f} Å")
print("Atoms to place   :")
for e, n in atom_counts.items():
    print(f"  {e}: {n}")

# write the information to init.inp
with open("init.inp", "w") as f:
    f.write(f"tolerance 2.0\n")
    f.write("filetype pdb\n")
    f.write(f"pbc {box_diam_exact:.16f} {box_diam_exact:.16f} {box_diam_exact:.16f}\n")
    f.write(f"output init.pdb\n\n")

    for element in stoich.keys():
        f.write(f"structure {element}.pdb\n")
        f.write(f"  number {atom_counts[element]}\n")
        f.write("end structure\n\n")

print(f"Packmol input written to init.inp")

# use packmol to generate an initial structure
subprocess.call(f"{packmolPath} < init.inp", shell=True)

# convert the init.pdb to VASP POSCAR format
from ase.io import read, write
atoms = read("init.pdb")
atoms.set_cell([box_diam_exact, box_diam_exact, box_diam_exact])
atoms.set_pbc([True, True, True])
write("POSCAR", atoms, format="vasp")

# clean up
subprocess.call("rm init.pdb init.inp", shell=True)
for el in stoich.keys():
    subprocess.call(f"rm {el}.pdb", shell=True)
os.makedirs("equilibrate_and_scale", exist_ok=True)
subprocess.call("cp POSCAR equilibrate_and_scale/", shell=True)

# ----- Generate POTCAR File -------------------------------------------------------------
# Read elements from the POSCAR file
with open("POSCAR", "r") as f:
    lines = f.readlines()
    elements = lines[5].split()
command = "cat "

try:
    potcarDict
except NameError:
    print("potcarDict is not defined will use default")
    potcarDict = vasp_potcar_recommended
else:
    print("potcarDict exists, will use it")

for pottype in elements:
    command += os.path.join(potcarPath, potcarDict[pottype], "POTCAR") + " "
command += " > POTCAR"

subprocess.call(command, shell=True)

# ----- Modify INCAR Files -------------------------------------------------------------
# modify the INCAR_NVT file used in the initial equilibration, scaling of lattice, and quench.
# get max ENMAX from POTCAR
max_enmax = 0.0
with open("POTCAR") as f:
    for line in f:
        if "ENMAX" in line:
            try:
                value = float(line.split()[2].split(";")[0])
                max_enmax = max(max_enmax, value)
            except (IndexError, ValueError):
                continue
print(f"ENCUT will be set to 1.3 * ENMAX : {1.3 * max_enmax:.2f} eV")
timestep = 2.0 # fs
if "Li" in elements or "H" in elements:
    timestep = 1.0

systemName = ""
for el in stoich.keys():
    systemName += f"{el}{stoich[el]}"
temperature = int((melting_point + 300 - 1)/ 300) * 300

cwd = os.getcwd()
os.chdir("incar_templates")

langevin_gamma_values = [str(5)] * len(stoich)

# Step 1: Generate INCAR_NVT_EQL used in section 1 for equilibration
modify_incar(
    "INCAR_NVT", "INCAR_NVT_EQL",
    {
        "SYSTEM": systemName,
        "ENCUT": f"{1.3 * max_enmax:.2f}",
        "POTIM": f"{timestep:.2f}",
        "TEBEG": temperature,
        "TEEND": temperature,
        "LANGEVIN_GAMMA": ' '.join(langevin_gamma_values),
    }
)

# Step 2: Create INCAR_NVT_SCALE with modified NSW for scaling according to pressure in section 1
modify_incar(
    "INCAR_NVT_EQL", "INCAR_NVT_SCALE",
    {
        "NSW": int(4 * 1e3 / timestep),
    }
)

# Step 3: Create INCAR_NVT_QUENCH with TEMP placeholders used in section 2
modify_incar(
    "INCAR_NVT_EQL", "INCAR_NVT_QUENCH",
    {
        "NSW": int(2 * 1e3 / timestep),
        "TEBEG": "TEMP",
        "TEEND": "TEMP",
    }
)

# Step 4: Modify SYSTEM and ENCUT in INCAR_OPT used in section 2
modify_incar(
    "INCAR_OPT", "INCAR_TEMP",
    {
        "SYSTEM": systemName,
        "ENCUT": f"{1.3 * max_enmax:.2f}",
    }
)

subprocess.call("mv INCAR_TEMP INCAR_OPT", shell=True)

# Step 4: Modify SYSTEM and ENCUT in INCAR_NPT_MLFF, INCAR_NVT_MLFF, INCAR_SP_AB, and INCAR_SP_ML
#  used in MLFF training and validation, and production in section 3 and 4
mlffINCARs = ["INCAR_NPT_MLFF", "INCAR_NVT_MLFF", "INCAR_SP_AB", "INCAR_SP_ML"]
for mlffINCAR in mlffINCARs:
    modify_incar(
        mlffINCAR, "INCAR_TEMP",
        {
            "SYSTEM": systemName,
            "ENCUT": f"{1.3 * max_enmax:.2f}",
            "LANGEVIN_GAMMA": ' '.join(langevin_gamma_values),
        }
    )
    subprocess.call(f"mv INCAR_TEMP {mlffINCAR}", shell=True)


os.chdir(cwd)
# ----- Modify, generate and run slurm script -------------------------------------------------------------
folder = "slurm_scripts"
# Regex pattern to find SLURM -J lines
pattern = re.compile(r"^(#SBATCH\s+-J\s+)(\S+)", re.IGNORECASE)

for filename in os.listdir(folder):
    if filename.endswith(".sh"):
        filepath = os.path.join(folder, filename)
        
        with open(filepath, "r") as f:
            lines = f.readlines()

        with open(filepath, "w") as f:
            for line in lines:
                match = pattern.match(line)
                if match:
                    line = f"{match.group(1)}{systemName}\n"
                f.write(line)

subprocess.call(f"cat {AIMDslurm} helper_scripts/equilibrate_and_scale.sh > equilibrate_and_scale/run.sh", shell=True)
os.chdir("equilibrate_and_scale")
subprocess.call("sbatch run.sh", shell=True)