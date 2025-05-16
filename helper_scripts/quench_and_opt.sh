
startTemp=1500
endTemp=300
step=300

prevDir=""
NSW=$(awk '$1 == "NSW" {print $3}' INCAR)
POTIM=$(awk '$1 == "POTIM" {print $3}' INCAR)
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
    ln -sf ../../POTCAR POTCAR
    ln -sf ../../KPOINTS KPOINTS
    start_time=$(date '+%Y-%m-%d %H:%M:%S')
    echo "[$start_time] Starting quench at ${temp} K ..."

    $VASP_COMMAND > vasp.out
    end_time=$(date '+%Y-%m-%d %H:%M:%S')
    echo "[$end_time] VASP finished after $NSW steps with $POTIM fs/step at ${temp} K."

    cd ..
    prevDir=$rundir
done

echo "Quenching sequence completed."
echo "Starting optimization sequence..."
# Optimization sequence, assuming quench_300/CONTCAR is the starting point

# Loop over scales from 1.000 to 0.980 (inclusive), step -0.001
prevPOSCAR="quench_300/CONTCAR"
scale_script="../../scalePOSCAR.py"
for i in $(seq 0 20); do
    scale=$(awk -v n=$i 'BEGIN {printf "%.3f", 1.000 - 0.001 * n}')
    dir="${scale//./_}"

    echo ">>> Preparing $dir with scale = $scale"

    mkdir -p $dir
    cd $dir
    ln -sf ../../INCAR_OPT INCAR
    ln -sf ../../POTCAR POTCAR
    ln -sf ../../KPOINTS KPOINTS
    cp "../$prevPOSCAR" POSCAR

    # Generate scaled POSCAR
    python $scale_script "POSCAR" "$scale"
    mv POSCAR_scaled POSCAR

    echo "Running VASP in $dir ..."
    $VASP_COMMAND > vasp.out

    prevPOSCAR="$dir/CONTCAR"
    cd ..
done

echo "Optimization sequence finished..."