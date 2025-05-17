
cd POSCAR_for_validation/

for i in {0..49}; do
   echo "test configuration " $i
   cd ab_${i}
   ln -sf ../../../../../INCAR_SP_AB INCAR
   ln -sf ../../../../../POTCAR POTCAR
   ln -sf ../../../../../KPOINTS KPOINTS
   ${VASP_COMMAND} > vasp.out
   cd ../
done

