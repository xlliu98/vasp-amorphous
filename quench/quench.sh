#!/bin/bash
#SBATCH -A m697 
#SBATCH -C gpu
#SBATCH -q regular
#SBATCH -N 1
#SBATCH --gpu-bind=none
#SBATCH -t 48:00:00
#SBATCH --job-name="iScale"
#SBATCH --mail-user=xiaolin.liu@vanderbilt.edu
#SBATCH --mail-type=FAIL

module load vasp/6.4.3-gpu
# One can use up to 16 OpenMP threads-per-MPI-rank when using
#  4 GPUs-per-node.
export OMP_NUM_THREADS=1
export OMP_PLACES=threads
export OMP_PROC_BIND=spread

VASP_COMMAND="srun -n 4 -c 32 -G 4 --cpu-bind=cores --gpu-bind=none vasp_gam"

startTemp=1500
endTemp=300
step=300

prevDir=""

for temp in $(seq $startTemp -$step $endTemp); do
    rundir="quench_${temp}"
    mkdir -p $rundir

    if [ "$temp" -eq "$startTemp" ]; then
        cp POSCAR $rundir/POSCAR
    else
        cp ${prevDir}/CONTCAR $rundir/POSCAR
    fi

    cp INCAR $rundir/INCAR

    # Replace TEMP in INCAR with actual temperature
    sed -i "s/TEMP/${temp}/g" $rundir/INCAR

    cd $rundir
    ln -sf ../POTCAR POTCAR
    ln -sf ../KPOINTS KPOINTS
    start_time=$(date '+%Y-%m-%d %H:%M:%S')
    echo "[$start_time] Starting quench at ${temp} K ..."

    $VASP_COMMAND > vasp.out &

    # Extract NSW from INCAR
    NSW=$(awk '$1 == "NSW" {print $3}' INCAR)
    echo "[$end_time] Will run $NSW steps at ${temp} K."
    # Monitor until OSZICAR reaches step == NSW
    while true; do
        if [ -f OSZICAR ]; then
            last_line=$(tail -n 1 OSZICAR)
            if [[ $last_line =~ ^[[:space:]]*${NSW} ]]; then
                end_time=$(date '+%Y-%m-%d %H:%M:%S')
                echo "[$end_time] VASP completed $NSW steps at ${temp} K."
                break
            fi
        fi
        sleep 60
    done

    cd ..
    prevDir=$rundir
done

echo "Quenching sequence completed."


