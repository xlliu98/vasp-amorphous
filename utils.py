
def modify_incar(input_file, output_file, substitutions):
    with open(input_file, "r") as infile, open(output_file, "w") as outfile:
        for line in infile:
            stripped = line.strip()
            if "=" in stripped and not stripped.startswith("#"):
                key = stripped.split("=")[0].strip().upper()
                if key in substitutions:
                    outfile.write(f"{key} = {substitutions[key]}\n")
                else:
                    outfile.write(line)
            else:
                outfile.write(line)



# see https://www.vasp.at/wiki/index.php/Available_pseudopotentials for the latest
vasp_potcar_recommended = {
    "H":     "H",           # Default is sufficient
    "He":    "He",

    "Li":    "Li_sv",       # Use _sv for Li to include 1s in valence 
    "Be":    "Be",
    "B":     "B",
    "C":     "C",
    "N":     "N",
    "O":     "O",
    "F":     "F",
    "Ne":    "Ne",

    "Na":    "Na_pv",       # Include 2p in valence
    "Mg":    "Mg",    
    "Al":    "Al",
    "Si":    "Si",
    "P":     "P",
    "S":     "S",
    "Cl":    "Cl",
    "Ar":    "Ar",

    "K":     "K_sv",        # _sv includes 3s and 3p
    "Ca":    "Ca_sv",
    "Sc":    "Sc_sv",
    "Ti":    "Ti_sv",
    "V":     "V_sv",
    "Cr":    "Cr_pv",
    "Mn":    "Mn_pv",
    "Fe":    "Fe",
    "Co":    "Co",
    "Ni":    "Ni",
    "Cu":    "Cu",
    "Zn":    "Zn",

    "Ga":    "Ga_d",
    "Ge":    "Ge_d",
    "As":    "As",
    "Se":    "Se",
    "Br":    "Br",
    "Kr":    "Kr",

    "Rb":    "Rb_sv",
    "Sr":    "Sr_sv",
    "Y":     "Y_sv",
    "Zr":    "Zr_sv",
    "Nb":    "Nb_pv",
    "Mo":    "Mo_sv",
    "Tc":    "Tc_pv",
    "Ru":    "Ru_pv",
    "Rh":    "Rh_pv",
    "Pd":    "Pd",
    "Ag":    "Ag",
    "Cd":    "Cd",

    "In":    "In_d",
    "Sn":    "Sn_d",
    "Sb":    "Sb",
    "Te":    "Te",
    "I":     "I",
    "Xe":    "Xe",

    "Cs":    "Cs_sv",
    "Ba":    "Ba_sv",
    "La":    "La",          # Or La_3 for some contexts
    "Ce":    "Ce",
    "Pr":    "Pr_3",
    "Nd":    "Nd_3",
    "Pm":    "Pm_3",
    "Sm":    "Sm_3",
    "Eu":    "Eu_2",
    "Gd":    "Gd_3",
    "Tb":    "Tb_3",
    "Dy":    "Dy_3",
    "Ho":    "Ho_3",
    "Er":    "Er_3",
    "Tm":    "Tm_3",
    "Yb":    "Yb_2",
    "Lu":    "Lu_3",

    "Hf":    "Hf_pv",
    "Ta":    "Ta_pv",
    "W":     "W_sv",
    "Re":    "Re",
    "Os":    "Os",
    "Ir":    "Ir",
    "Pt":    "Pt",
    "Au":    "Au",
    "Hg":    "Hg",

    "Tl":    "Tl_d",
    "Pb":    "Pb_d",
    "Bi":    "Bi_d",
    "Po":    "Po_d",
    "At":    "At",
    "Rn":    "Rn",
    "Fr":    "Fr_sv",
    "Ra":    "Ra_sv",
    "Ac":    "Ac",
    "Th":    "Th",
    "Pa":    "Pa",
    "U":     "U",
    "Np":    "Np",
    "Pu":    "Pu",
    "Am":    "Am",
    "Cm":    "Cm",
}

