# vasp runs under mlff_validation/300K/POSCAR_for_validation/ab_0
cd POSCAR_for_validation/

for i in {0..49}; do
   echo "test configuration " $i
   cd ab_${i}
   ln -sf ../../../../incar_templates/INCAR_SP_AB INCAR
   ln -sf ../../../../POTCAR POTCAR
   ln -sf ../../../../KPOINTS KPOINTS
   ${VASP_COMMAND} > vasp.out
   cd ../
done

