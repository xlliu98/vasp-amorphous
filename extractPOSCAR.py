import os
import shutil
import subprocess
import sys

count = 0
trjFile = "XDATCAR"
delimiter = sys.argv[1]
with open(trjFile, 'r') as file:
    for line in file:
        if line.strip() == delimiter and count != 0:
            break
        count += 1

with open(trjFile, 'r') as file:
    lines = file.readlines()

nStruct = len(lines)/count
dist = int(nStruct//50)

newFolder = "POSCAR_for_validation"
os.makedirs(newFolder, exist_ok=True)
os.chdir(newFolder)
for i in range(0, 50):
    mlDir = "ML_" + str(i)
    abDir = "ab_" + str(i)
    for newDir in [mlDir, abDir]:
        os.makedirs(newDir, exist_ok=True)
        os.chdir(newDir)
        with open("POSCAR", 'w') as file:
            file.writelines(lines[count * i * dist:count*(i * dist + 1)])
        os.chdir("../")
