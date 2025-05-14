import matplotlib.pyplot as plt
import numpy as np
import os
import subprocess

# ----- user data -------------------------------------------------------------
timestep = 1.0 # in fs
timeAvg = 2 # in ps
initialTime = 10 # in ps
maxRestart = 10
Nions = 64 # number of ions
last_n_ps_steps = int(timeAvg * 1e3 / timestep)
dirs = ["eql_1500"]
# ---------------------------------------------------------------------------   

def getET(filePath):   
    with open(filePath, mode='r') as f:        
        E=[]
        T=[]        
        for line in f:
            T.append(float(line.split()[2]))
            E.append(float(line.split()[6]))
        return E,T

def getPorV(filePath, pos):
    with open(filePath, mode='r') as f:        
        PorV = []     
        for line in f:
            PorV.append(float(line.split()[pos]))
        return PorV 

def getRunning(property, time, steps):
    time_running = time[steps-1:]
    property_running = []
    property_running.append(np.sum(property[:steps]))
    for i in range(len(time_running) - 1):
        property_running.append(property_running[-1] + property[i + steps] - property[i])
    property_running = [_/steps for _ in property_running]
    return time_running, property_running

log_files = ["et.log", "p.log", "v.log"]

# Patterns to grep
grep_patterns = {
    "et.log": 'T= ',
    "p.log": 'total pressure',
    "v.log": 'volume of cell'
}


for top_dir in dirs:
    log_paths = {log: os.path.join(top_dir, log) for log in log_files}
    
    # Clear old logs
    for path in log_paths.values():
        if os.path.exists(path):
            os.remove(path)
    def grep_and_append(src_file, pattern, out_file):
        try:
            result = subprocess.run(["grep", pattern, src_file], capture_output=True, text=True)
            if result.stdout:
                with open(out_file, "a") as f:
                    f.write(result.stdout)
        except Exception as e:
            print(f"Error processing {src_file}: {e}")

    # Main dir files
    for log, pattern in grep_patterns.items():
        src_file = os.path.join(top_dir, "OSZICAR" if log == "et.log" else "OUTCAR")
        grep_and_append(src_file, pattern, log_paths[log])

    # Nested restart files, up to 10 restarts
    for i in range(1, maxRestart + 1):
        mid_dir = f"restart{i}"
        if not os.path.exists(os.path.join(top_dir, mid_dir)):
            print(f"Directory {mid_dir} does not exist, stopping search.")
            break
        for log, pattern in grep_patterns.items():
            src_file = os.path.join(top_dir, mid_dir, "OSZICAR" if log == "et.log" else "OUTCAR")
            grep_and_append(src_file, pattern, log_paths[log])

    initialSteps = int(initialTime * 1e3 / timestep)
    E, T = getET(top_dir + "/et.log")
    time = np.linspace(0, len(T)*timestep/1e3, len(T))
    P = getPorV(top_dir + "/p.log", -2)
    timep = np.linspace(0, len(P)*timestep/1e3, len(P))
    V = getPorV(top_dir + "/v.log", -1)
    timev = np.linspace(0, len(V)*timestep/1e3, len(V))
    
    if len(E) > initialSteps:
        print(f"Trimming the initial {initialSteps} steps")
        E = E[initialSteps:]
        T = T[initialSteps:]
        time = time[initialSteps:]
        P = P[initialSteps:]
        timep = timep[initialSteps:]
        V = V[initialSteps:]
        timev = timev[initialSteps:]
    

    steps = int(timeAvg * 1e3 / timestep)
    if len(time) > steps:
        time_running, E_running = getRunning(E, time, steps)
        timep_running, P_running = getRunning(P, timep, steps)
        timet_running, T_running = getRunning(T, time, steps)
        timev_running, V_running = getRunning(V, timev, steps)
        data_running = {"Energy/eV": (E_running,time_running), "Temperature/K": (T_running,timet_running), 
                "Pressure/kB": (P_running,timep_running), r"Volume/Å$^3$":(V_running, timev_running)}
    Ediff = []
    time_running2 = []
    if len(time) > steps * 2:
        time_running2, E_running2 = getRunning(E, time, steps * 2)
        for i in range(len(E_running2)):
            Ediff.append((E_running2[-1 - i] - E_running[-1 - i])*1e3)
        Ediff.reverse()
    print("dir = ", top_dir , ", time: ", time[-1], "ps") 
    print(f"last {timeAvg} ps avg pressure: ", np.mean(P[-last_n_ps_steps:]))
    print(f"last {timeAvg * 2} ps avg pressure: ", np.mean(P[-last_n_ps_steps*2:]))
    print(f"last {timeAvg} ps avg energy: ", np.mean(E[-last_n_ps_steps:]))
    print(f"last {timeAvg * 2} ps avg energy: ", np.mean(E[-last_n_ps_steps*2:]))
    print(f"Energy difference: {(np.mean(E[-last_n_ps_steps*2:]) - np.mean(E[-last_n_ps_steps:]))*1e3} meV")


    data = {"Energy/eV": (E,time), "Temperature/K": (T,time), "Pressure/kB": (P,timep), r"Volume/Å$^3$":(V, timev), "E Diff/meV":(Ediff, time_running2)}
    fig, axes = plt.subplots(5, 1, sharex=True, figsize=(8, 10))
    for count, (k, v) in enumerate(data.items()):
        ax = axes[count]
        ax.plot(v[1], v[0], 'k')
        if len(time) > steps and k in data_running:
            ax.plot(data_running[k][1], data_running[k][0], 'g')
        if k == "Pressure/kB":
            ax.axhline(5, color='g', lw=1.0, linestyle="--")
            ax.axhline(-5, color='g', lw=1.0, linestyle="--")
        if k == "E Diff/meV":
            ax.axhline(Nions, color='g', lw=1.0, linestyle="--")
            ax.axhline(-Nions, color='g', lw=1.0, linestyle="--")
        if count == len(axes) - 1:
            ax.set_xlabel(r"$\Delta t$ (ps)")
        ax.set_ylabel(k)
        ax.set_xlim(initialTime)

    plt.savefig("_".join(top_dir.split("/")) + "_ETPV.png", dpi=600, bbox_inches='tight')


