from ase.io.vasp import read_vasp_xdatcar
from ase.io import read
from ase.neighborlist import neighbor_list
import numpy as np

dirs = ["2units/ML_300_600/mlff_production/300K"]
ionic_radii = {'O': 1.26, 'Na': 1.16, 'Mg': 0.86, "Al": 0.675}  # in Å, taken from crystal ionic radii: https://en.wikipedia.org/wiki/Ionic_radius
radii = ionic_radii
threshold = 0.8
for top_dir in dirs:
    # Read atomic structure and trajectory
    frames = read_vasp_xdatcar(f"{top_dir}/XDATCAR", index=":")

    threshold_pairs = []
    cutoffs = [radii[el] for el in frames[0].get_chemical_symbols()]
    cutoff_matrix = np.add.outer(cutoffs, cutoffs)
    for frame_idx, atoms in enumerate(frames):
        # Use max cutoff for neighbor list
        i_idx, j_idx, distances = neighbor_list("ijd", atoms, np.max(cutoff_matrix))

        for i, j, d in zip(i_idx, j_idx, distances):
            if j <= i:
                continue
            el1 = atoms[i].symbol
            el2 = atoms[j].symbol
            rsum = radii[el1] + radii[el2]
            if d < threshold * rsum:
                threshold_pairs.append((frame_idx, i, el1, j, el2, d, rsum))
    print(f"checking XDATCAR in {top_dir}")
    for fidx, i, el1, j, el2, dist, rsum in threshold_pairs:
        print(f"Frame {fidx}: {el1}{i}-{el2}{j} = {dist:.2f} Å < {threshold} * {rsum:.2f} Å")





