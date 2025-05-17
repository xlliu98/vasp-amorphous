start_temp=300
delta_T=100
duration_ps=20
num_segments=3

for i in $(seq 0 $((num_segments - 1))); do
    T1=$((start_temp + i * delta_T))
    T2=$((T1 + delta_T))
    dir="${T1}K_${T2}K_${duration_ps}ps"
    mkdir -p "$dir"
    echo "Created: $dir"
    cd "$dir" 
    ln -sf ../../POTCAR POTCAR
    ln -sf ../../KPOINTS KPOINTS
    cp ../POSCAR ./
    cp ../INCAR ./
    if [ -f ../ML_AB ]; then
        cp ../ML_AB ./
        echo "Copied ML_AB to $dir"
    fi
    # Update INCAR with T1 and T2
    awk -v t1=$T1 -v t2=$T2 '
        BEGIN { IGNORECASE=1 }
        $1 == "TEBEG" { print "TEBEG = " t1; next }
        $1 == "TEEND" { print "TEEND = " t2; next }
        { print }
    ' INCAR > INCAR_TMP && mv INCAR_TMP INCAR

    echo "Running VASP in $dir ..."
    $VASP_COMMAND > vasp.out
    cp CONTCAR ../POSCAR
    cp ML_ABN ../ML_AB
    cd ..
done
