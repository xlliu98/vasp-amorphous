 
ln -sf ../POTCAR POTCAR
ln -sf ../KPOINTS KPOINTS
ln -sf ../mlff_training/POSCAR POSCAR
ln -sf ../mlff_training/ML_AB ML_AB
$VASP_COMMAND > vasp.out
