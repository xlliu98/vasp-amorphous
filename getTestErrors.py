import matplotlib.pyplot as plt
import numpy as np

dirs = [f"mlff_validation/{i}K/POSCAR_for_validation" for i in range(300, 501, 50)]


def getEnergy(OSZICAR):
    """
    Get the energy from the OSZICAR file.
    """
    with open(OSZICAR, "r") as f:
        lines = f.readlines()
        return float(lines[-1].split()[4])
def getForce(OUTCAR):
    """
    Get the forces from the OUTCAR file.
    """
    forces = []
    with open(OUTCAR, "r") as f:
        for line in f:
            if len(line.split()) > 2 and line.split()[1] == "TOTAL-FORCE":
                line = f.readline()
                line = f.readline()
                while len(line.split()) == 6:
                    for _ in range(3):
                        forces.append(float(line.split()[3 + _]))
                    line = f.readline()
                return np.array(forces)
def getStress(OUTCAR):
    """
    Get the stress from the OUTCAR file.
    """
    stress = []
    with open(OUTCAR, "r") as f:
        for line in f:
            if len(line.split()) == 8 and line.split()[1] == "kB":
                for _ in range(6):
                        stress.append(float(line.split()[2 + _]))
                return np.array(stress)
def get_rmse(dft_quantity, mlff_quantity, degrees_of_freedom):
    norm_error = np.linalg.norm(dft_quantity - mlff_quantity, axis=-1)
    error = np.sqrt(np.sum(norm_error**2, axis=-1) / degrees_of_freedom)
    return error


for d in dirs:
    data = {
        "energy": {"ML": [], "DFT": []},
        "force": {"ML": [], "DFT": []},
        "stress": {"ML": [], "DFT": []}
    }

    errors = {
        "energy": [],
        "force":  [],
        "stress": [],
    }
    for i in range(50):
        oszicar = f"{d}/ML_{i}/OSZICAR"
        outcar = f"{d}/ML_{i}/OUTCAR"
        data["energy"]["ML"].append(getEnergy(oszicar))
        data["force"]["ML"].append(getForce(outcar))
        data["stress"]["ML"].append(getStress(outcar))

        oszicar = f"{d}/ab_{i}/OSZICAR"
        outcar = f"{d}/ab_{i}/OUTCAR"
        data["energy"]["DFT"].append(getEnergy(oszicar))
        data["force"]["DFT"].append(getForce(outcar))
        data["stress"]["DFT"].append(getStress(outcar))

    Nions = len(data["force"]["ML"][0])// 3

    errors["energy"] = [(dft - ml)/Nions for dft, ml in zip(data["energy"]["DFT"], data["energy"]["ML"])]
    errors["force"] = [get_rmse(dft, ml, Nions * 3) for dft, ml in zip(data["force"]["DFT"], data["force"]["ML"])]
    errors["stress"] = [get_rmse(dft, ml, 6) for dft, ml in zip(data["stress"]["DFT"], data["stress"]["ML"])]


    errors_normalized = {key: 0.0 for key in errors.keys()}
    print(f"Errors for {d}:")
    for key in errors.keys():
        errors_normalized[key] = np.sum(errors[key]) / len(errors[key])
        print(f"Normalized {key} error: {errors_normalized[key]}")


    count = 0
    fig, axes = plt.subplots(3, 1, sharex=True)
    x = np.arange(len(errors["energy"]))
    ylabels = {"energy":"Energy per Atom (eV)", "force":"RMSE Force (eV/Å)", "stress": "RMSE Stress (GPa)"}
    for count, (k, v) in enumerate(errors.items()):
        ax = axes[count]
        ax.plot(x, v, 'k')
        if count == len(axes) - 1:
            ax.set_xlabel(r"Configuration Number")
        ax.set_ylabel(ylabels[k])
        ax.set_xlim(0)

    plt.savefig("_".join(d.split("/")) + "_test_errors.png", dpi=600, bbox_inches='tight')



