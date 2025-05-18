
ln -sf ../incar_templates/INCAR_NVT_EQL INCAR
ln -sf ../POTCAR POTCAR
ln -sf ../KPOINTS KPOINTS
POTIM=$(awk '$1 == "POTIM" {print $3}' INCAR)
NIONS=$(awk 'NR==7 {for(i=1;i<=NF;i++) sum+=$i; print sum}' POSCAR)

steps_per_ps=$(awk -v p="$POTIM" 'BEGIN { printf "%.0f", 1000 / p }')
window_2ps=$((2 * steps_per_ps))
window_4ps=$((4 * steps_per_ps))
tolerance_meV=$NIONS  # 1 meV/atom × NIONS

echo "Running VASP..."
$VASP_COMMAND > vasp.out &    # run in background
vasp_pid=$!

while kill -0 $vasp_pid 2>/dev/null; do
    if [ -f OSZICAR ]; then
        ionic_lines=$(grep -E '^\s*[0-9]+ T=' OSZICAR | tee ionic_oszicar.log | wc -l)

        if (( ionic_lines >= window_4ps )); then
            tail -n $window_4ps ionic_oszicar.log | awk '{ print $7 }' > F_values.log

            avgF_2ps=$(tail -n $window_2ps F_values.log | awk '{s+=$1} END {print s/NR}')
            avgF_4ps=$(awk '{s+=$1} END {print s/NR}' F_values.log)
            delta=$(awk -v a=$avgF_2ps -v b=$avgF_4ps 'BEGIN {print (a - b) * 1000}')
            abs_delta=$(awk -v d=$delta 'BEGIN {print (d < 0 ? -d : d)}')

            echo "Energy convergence ΔF = $abs_delta meV"

            if (( $(awk -v d=$abs_delta -v t=$tolerance_meV 'BEGIN {print (d < t)}') )); then
                echo "F converged within $tolerance_meV meV. Terminating VASP..."
                kill $vasp_pid
                wait $vasp_pid 2>/dev/null
                break
            fi
        fi
    fi
    sleep 60
done




# Parameters for iterative scaling
max_iter=20
tolerance_kbar=5
mkdir -p "scale"
cd "scale" 
ln -sf ../../incar_templates/INCAR_NVT_SCALE INCAR
ln -sf ../../POTCAR POTCAR
ln -sf ../../KPOINTS KPOINTS
# Extract values from INCAR
NSW=$(awk '$1 == "NSW" {print $3}' INCAR)
POTIM=$(awk '$1 == "POTIM" {print $3}' INCAR)
# Compute total run time (ps) and timestep (fs)
timestep_fs=$POTIM
avg_window_ps=2
run_time_ps=$(awk -v n="$NSW" -v p="$POTIM" 'BEGIN { printf "%.3f\n", n * p / 1000 }')
steps_to_average=$(awk -v avg=2 -v p="$POTIM" 'BEGIN { printf "%.0f\n", avg * 1000 / p }')


cd ..
# Parse pressure from OUTCAR in the first equilibrated run
echo "Extracting pressure..."
grep "total pressure" OUTCAR | awk '{print $(NF-1)}' > p.log
tail -n $steps_to_average p.log > p_tail.log
avg_p=$(awk '{sum+=$1} END {print sum/NR}' p_tail.log)
echo "Average pressure over last ${avg_window_ps} ps = $avg_p kBar"

# Rescale using Python
echo "Rescaling lattice with pressure $avg_p kBar, assuming bulk modulus 50.0 GPa"
python ../scalePOSCAR.py CONTCAR $(awk -v p="$avg_p" 'BEGIN { printf "%.6f", p / 500 }')

cd "scale" 
cp ../POSCAR_scaled POSCAR

# Print result
echo "Running $NSW steps at $POTIM fs/step = $run_time_ps ps total"
echo "Averaging over $avg_window_ps ps = $steps_to_average steps"
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

    end_time=$(date '+%Y-%m-%d %H:%M:%S')
    echo "[$end_time] VASP completed $NSW steps."

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
        cp CONTCAR ../POSCAR
        break
    fi

    # Rescale using Python
    echo "Rescaling lattice with pressure $avg_p kBar, assuming bulk modulus 50.0 GPa"
    python ../../../scalePOSCAR.py CONTCAR $(awk -v p="$avg_p" 'BEGIN { printf "%.6f", p / 500 }')

    # Backup and prepare next POSCAR
    cp POSCAR_scaled ../POSCAR

    cd ..
    cp POSCAR history/POSCAR_after_iter_$i
done

echo "=== Iterative scaling finished ==="

echo "=== Final equilibration ==="
cd ..
mkdir -p "final_eql"
cp scale/POSCAR final_eql/POSCAR
cp INCAR final_eql/INCAR
cd final_eql
ln -sf ../../POTCAR POTCAR
ln -sf ../../KPOINTS KPOINTS
# chang NSW in INCAR to 10 ps/POTIM
POTIM=$(awk '$1 == "POTIM" {print $3}' INCAR)
# Compute number of steps: 10 ps = 10000 fs
NSW=$(awk -v potim="$POTIM" 'BEGIN { printf "%d", 10000 / potim }')

# Replace NSW line in INCAR with new value
awk -v nsw="$NSW" '
    BEGIN { IGNORECASE = 1 }
    $1 == "NSW" {
        print "NSW = " nsw
        next
    }
    { print }
' INCAR > INCAR_tmp && mv INCAR_tmp INCAR
echo "Running VASP..."
$VASP_COMMAND > vasp.out 
cp CONTCAR ../POSCAR
echo "=== Final equilibration done==="