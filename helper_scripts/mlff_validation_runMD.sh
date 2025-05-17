
# used under validation/*K/ directory
ln -sf ../../POTCAR POTCAR
ln -sf ../../KPOINTS KPOINTS
ln -sf ../../mlff_refit/POSCAR POSCAR
ln -sf ../../mlff_refit/ML_FFN ML_FF

$VASP_COMMAND > vasp.out

delimiter=$(awk '$1 == "SYSTEM" {print $3}' INCAR)
python ../../extractPOSCAR.py "$delimiter" 