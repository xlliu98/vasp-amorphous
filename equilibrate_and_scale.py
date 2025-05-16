import subprocess
import os
from utils import vasp_potcar_recommended
# ----- user data -------------------------------------------------------------
molar_masses = {"Li": 6.9410, "Ta": 180.94788, "Cl": 35.45}     # g mol⁻¹
stoich       = {"Li": 1, "Ta": 1, "Cl": 6}                      # LiTaCl₆
density      = 2.96                      # g cm⁻³
melting_point = 1500 # K, will be rounded to the nearest multiples of 300 K, guranteed to be equal to or larger than original value.
box_diam     = 12.0                      # Å
packmolPath = "/home/xiaolin/software/packmol-20.15.2/packmol"
potcarPath = "/home/xiaolin/VASP/paw-pbe-64"
AIMDslurm = "run_kepler_gpu.sh"
MLFFslurm = "run_kepler_cpu.sh"
potcarDict = {"Li": "Li", "Ta": "Ta_pv", "Cl": "Cl"}  # use a lower ENMAX for Li
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
    print(f"  {e}: {n:.2f}")

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
subprocess.call("cp POSCAR equilibrate_and_scale", shell=True)

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
# write the INCAR file
input_incar = "INCAR_NVT"
eql_incar = "INCAR_NVT_EQL"

with open(input_incar, "r") as infile, open(eql_incar, "w") as outfile:
    for line in infile:
        # Skip comments and empty lines
        stripped = line.strip()
        if "=" in stripped and not stripped.startswith("#"):
            key = stripped.split("=")[0].strip().upper()
            if key == "SYSTEM":
                outfile.write(f"SYSTEM = {systemName}\n")
                continue
            elif key == "ENCUT":
                outfile.write(f"ENCUT = {1.3 * max_enmax:.2f}\n")
                continue
            elif key == "POTIM":
                outfile.write(f"POTIM = {timestep:.2f}\n")
                continue
            elif key == "TEBEG":
                outfile.write(f"TEBEG = {temperature}\n")
                continue
            elif key == "TEEND":
                outfile.write(f"TEEND = {temperature}\n")
                continue
            else:
                outfile.write(line)
        else:
            outfile.write(line)

scale_incar = "INCAR_NVT_SCALE"
with open(eql_incar, "r") as infile, open(scale_incar, "w") as outfile:
    for line in infile:
        # Skip comments and empty lines
        stripped = line.strip()
        if "=" in stripped and not stripped.startswith("#"):
            key = stripped.split("=")[0].strip().upper()
            if key == "NSW":
                outfile.write(f"NSW = {int(4 * 1e3/timestep)}\n")
                continue
            else:
                outfile.write(line)
        else:
            outfile.write(line)

quench_incar = "INCAR_NVT_QUENCH"
with open(eql_incar, "r") as infile, open(quench_incar, "w") as outfile:
    for line in infile:
        # Skip comments and empty lines
        stripped = line.strip()
        if "=" in stripped and not stripped.startswith("#"):
            key = stripped.split("=")[0].strip().upper()
            if key == "NSW":
                outfile.write(f"NSW = {int(2 * 1e3/timestep)}\n")
            elif key == "TEBEG":
                outfile.write(f"TEBEG = TEMP\n")
            elif key == "TEEND":
                outfile.write(f"TEEND = TEMP\n")
            else:
                outfile.write(line)
        else:
            outfile.write(line)

with open("INCAR_OPT", "r") as infile, open("INCAR_TEMP", "w") as outfile:
    for line in infile:
        # Skip comments and empty lines
        stripped = line.strip()
        if "=" in stripped and not stripped.startswith("#"):
            key = stripped.split("=")[0].strip().upper()
            if key == "SYSTEM":
                outfile.write(f"SYSTEM = {systemName}\n")
            elif key == "ENCUT":
                outfile.write(f"ENCUT = {1.3 * max_enmax:.2f}\n")
            else:
                outfile.write(line)
        else:
            outfile.write(line)
subprocess.call("mv INCAR_TEMP INCAR_OPT", shell=True)
# ----- Generate and run slurm script -------------------------------------------------------------
subprocess.call(f"cat {AIMDslurm} equilibrate_and_scale.sh > equilibrate_and_scale/run.sh", shell=True)
os.chdir("equilibrate_and_scale")
subprocess.call("sbatch run.sh", shell=True)