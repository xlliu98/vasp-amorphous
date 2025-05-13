#!/bin/bash
#SBATCH --time=144:00:00
#SBATCH --ntasks=1
#SBATCH --gres=gpu:1
#SBATCH -J test
#SBATCH -o slurm_%j.out
#SBATCH -e slurm_%j.err
module load VASP
vasp_exe=`which vasp_gam`
echo "cuda:$CUDA_VISIBLE_DEVICES"

VASP_COMMAND="mpirun -np ${SLURM_NTASKS} $vasp_exe"

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


