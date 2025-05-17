# vasp runs under mlff_validation/300K/POSCAR_for_validation/ML_0
cd POSCAR_for_validation/

for i in {0..49}; do
   echo "test configuration " $i
   cd ML_${i}
   ln -sf ../../../../incar_templates/INCAR_SP_ML INCAR
   ln -sf ../../../ML_FF ML_FF
   ln -sf ../../../../POTCAR POTCAR
   ln -sf ../../../../KPOINTS KPOINTS
   ${VASP_COMMAND} > vasp.out
   cd ../
done

