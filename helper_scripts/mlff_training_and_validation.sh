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
done
