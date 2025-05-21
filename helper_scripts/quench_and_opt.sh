
startTemp=1500
endTemp=300
step=300

NSW=$(awk '$1 == "NSW" {print $3}' INCAR)
POTIM=$(awk '$1 == "POTIM" {print $3}' INCAR)
for temp in $(seq $startTemp -$step $endTemp); do
    rundir="quench_${temp}"
    mkdir -p $rundir
    cp POSCAR $rundir/POSCAR
    cp INCAR $rundir/INCAR

    # Replace TEMP in INCAR with actual temperature
    sed -i "s/TEMP/${temp}/g" $rundir/INCAR

    cd $rundir
    ln -sf ../../POTCAR POTCAR
    ln -sf ../../KPOINTS KPOINTS
    start_time=$(date '+%Y-%m-%d %H:%M:%S')
    echo "[$start_time] Starting quench at ${temp} K ..."

    $VASP_COMMAND > vasp.out
    cp CONTCAR ../POSCAR
    end_time=$(date '+%Y-%m-%d %H:%M:%S')
    echo "[$end_time] VASP finished after $NSW steps with $POTIM fs/step at ${temp} K."

    cd ..
done

echo "Quenching sequence completed."
echo "Starting optimization sequence..."
# Optimization sequence, assuming POSCAR is the starting point

# Loop over scales from 0.999 to 0.980 (inclusive) successively, with step size = -0.001
scale_script="../../scalePOSCAR.py"

# Define absolute target scales
abs_scales=()
for i in $(seq 0 20); do
    abs=$(awk -v n=$i 'BEGIN {printf "%.6f", 1.000 - 0.001 * n}')
    abs_scales+=("$abs")
done

# Loop through scale pairs
for ((i = 1; i < ${#abs_scales[@]}; i++)); do
    prev_scale=${abs_scales[$((i - 1))]}
    curr_scale=${abs_scales[$i]}
    dir=$(printf "scale_%03d" $i)

    # Compute relative scale: curr / prev
    rel_scale=$(awk -v a=$curr_scale -v b=$prev_scale 'BEGIN {printf "%.16f", a / b}')

    echo ">>> Preparing $dir with relative scale = $rel_scale (from $prev_scale to $curr_scale)"

    mkdir -p "$dir"
    cd "$dir"

    ln -sf ../../incar_templates/INCAR_OPT INCAR
    ln -sf ../../POTCAR POTCAR
    ln -sf ../../KPOINTS KPOINTS
    cp ../POSCAR POSCAR

    python "$scale_script" POSCAR "$rel_scale"
    mv POSCAR_scaled POSCAR

    echo "Running VASP in $dir ..."
    $VASP_COMMAND > vasp.out

    cp CONTCAR ../POSCAR
    cd ..
done


echo "Optimization sequence finished..."