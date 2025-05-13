import os
import subprocess
import matplotlib.pyplot as plt

def extract_energies(scales, log_file="e0_relaxed.log"):
    with open(log_file, "w") as log:
        for scale in scales:
            new_dir = "_".join(str(scale).split("."))
            oszicar_path = os.path.join(new_dir, "OSZICAR")
            if os.path.exists(oszicar_path):
                cmd = f"grep E0 '{oszicar_path}' | tail -1"
                try:
                    output = subprocess.check_output(cmd, shell=True, text=True).strip()
                    log.write(f"{new_dir}/ {output}\n")
                except subprocess.CalledProcessError:
                    print(f"Failed to read E0 from {oszicar_path}")
            else:
                print(f"Missing: {oszicar_path}")

def get_e_from_log(file_path):
    scales, energies = [], []
    with open(file_path, "r") as f:
        for line in f:
            tokens = line.split()
            scale_str = tokens[0].rstrip('/')
            scale = float(".".join(scale_str.split("_")))
            energy = float(tokens[5])  # assuming E0 is 6th token
            scales.append(scale)
            energies.append(energy)
    return scales, energies

# ---- Run everything ----
scales = [1.0 + 0.001 * i for i in range(-20, 1)]
extract_energies(scales, log_file="e0_relaxed.log")
scales, energies = get_e_from_log("e0_relaxed.log")

plt.plot(scales, energies, 'o-')
plt.xlabel("Lattice scaling factor")
plt.ylabel("Final E0 (eV)")
plt.title("Relaxed E0 vs. Scaling")
plt.grid(True)
plt.savefig("e_scales.png", dpi=300, bbox_inches='tight')
print("Plot saved as e_scales.png")


