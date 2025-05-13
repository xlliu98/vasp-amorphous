#!/bin/bash
#SBATCH --time=144:00:00
#SBATCH --ntasks=1
#SBATCH --gres=gpu:1
#SBATCH -J test
#SBATCH -o slurm_%j.out
#SBATCH -e slurm_%j.err
module load VASP
vasp_exe=$(which vasp_gam)
echo "cuda:$CUDA_VISIBLE_DEVICES"

VASP_COMMAND="mpirun -np ${SLURM_NTASKS} $vasp_exe"
ulimit -s unlimited

# Parameters
max_iter=10
tolerance_kbar=5
run_time_ps=4
timestep_fs=1
avg_window_ps=2
steps_to_average=$((1000 * avg_window_ps / timestep_fs))
NSW=$(awk '$1 == "NSW" {print $3}' INCAR)
echo "Will run $NSW steps each iteration."
mkdir -p history

for ((i=1; i<=max_iter; i++)); do
    echo "=== Iteration $i ==="
    start_time=$(date '+%Y-%m-%d %H:%M:%S')
    echo "[$start_time] Starting iteration ..."
    run_dir="run_$i"
    mkdir -p "$run_dir"
    cp POSCAR "$run_dir"
    cd "$run_dir"

    ln -sf ../INCAR INCAR
    ln -sf ../POTCAR POTCAR
    ln -sf ../KPOINTS KPOINTS
    # Run VASP
    echo "Running VASP..."
    $VASP_COMMAND > vasp.out
    while true; do
        if [ -f OSZICAR ]; then
            last_line=$(tail -n 1 OSZICAR)
            if [[ $last_line =~ ^[[:space:]]*${NSW} ]]; then
                end_time=$(date '+%Y-%m-%d %H:%M:%S')
                echo "[$end_time] VASP completed $NSW steps."
                break
            fi
        fi
        sleep 60
    done
    # Parse pressure from OUTCAR
    echo "Extracting pressure..."
    grep "total pressure" OUTCAR | awk '{print $(NF-1)}' > p.log
    tail -n $steps_to_average p.log > p_tail.log
    avg_p=$(awk '{sum+=$1} END {print sum/NR}' p_tail.log)
    echo "Average pressure over last ${avg_window_ps} ps = $avg_p kBar"

    # Check if pressure is within tolerance
    abs_p=$(echo ${avg_p#-})  # remove minus sign
    if (( $(echo "$abs_p < $tolerance_kbar" | bc -l) )); then
        echo "Converged: Pressure within ±${tolerance_kbar} kBar."
        break
    fi

    # Rescale using Python
    echo "Rescaling lattice with pressure $avg_p kBar..."
    python ../scalePOSCAR.py POSCAR $avg_p

    # Backup and prepare next POSCAR
    cp POSCAR ../POSCAR_last
    cp POSCAR_scaled ../POSCAR

    cd ..
    cp POSCAR history/POSCAR_after_iter_$i
done

echo "=== Iterative scaling finished ==="


