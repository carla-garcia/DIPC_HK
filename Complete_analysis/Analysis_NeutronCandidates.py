print("Iniciando el script de analisis candidatos neutrones...")
print("Importando librerias necesarias...")

import numpy as np
import matplotlib.pyplot as plt
import pandas as pd
import functions_spills
from scipy.optimize import curve_fit
from collections import defaultdict
import matplotlib.ticker as ticker
import glob
import os
import pickle

from matplotlib import rcParams
rcParams['mathtext.fontset'] = 'stix'
rcParams['font.family'] = 'STIXGeneral'
rcParams['figure.figsize'] = [10, 8]
rcParams['font.size'] = 22

#Signal data download #############################################################################################

print("Cargando datos de signal...")
root_dir_sig = "/data/cgarcia_2002/WCTE/data/2385_calib_time/"
root_files_sig = sorted(glob.glob(os.path.join(root_dir_sig, "*.root")))
root_files_sig = sorted(root_files_sig, key=lambda file_path: int(file_path.split("P")[-1].split(".")[0]))

print(f"Found {len(root_files_sig)} signal ROOT files.")

times_branch_sorted_sig, times_branch_sorted_TOF_sig, charge_branch_sorted_sig, mpmt_id_branch_sorted_sig, event_number_branch_sig, _ = functions_spills.multiple_partition(root_files_sig)
print("Total eventos sig", len(times_branch_sorted_TOF_sig))
print("Datos de signal cargados.")
N_events_sig = max(event_number_branch_sig) + 1

print("Cargando datos de bkg...")
root_dir_bkg = "/data/cgarcia_2002/WCTE/data/2384_calib_time/"
root_files_bkg = sorted(glob.glob(os.path.join(root_dir_bkg, "*.root")))
root_files_bkg = sorted(root_files_bkg, key=lambda file_path: int(file_path.split("P")[-1].split(".")[0]))

print(f"Found {len(root_files_bkg)} background ROOT files.")

times_branch_sorted, times_branch_sorted_TOF, charge_branch_sorted, mpmt_id_branch_sorted, event_number_branch, _ = functions_spills.multiple_partition(root_files_bkg)
print("Total eventos bkg", len(times_branch_sorted_TOF))
print("Datos de background cargados.")
N_events = max(event_number_branch) + 1

with open('/scratch/cgarcia_2002/Complete_analysis/Filtered_data/deleted_indices_nHits_BKG.pkl', 'rb') as f:
    deleted_indices_nHits = pickle.load(f)

with open('/scratch/cgarcia_2002/Complete_analysis/Filtered_data/deleted_indices_nHits_SIG.pkl', 'rb') as f:
    deleted_indices_nHits_sig = pickle.load(f)

times_branch_filtered = functions_spills.delete_indices_list(times_branch_sorted_TOF, deleted_indices_nHits)
times_branch_filtered_sig = functions_spills.delete_indices_list(times_branch_sorted_TOF_sig, deleted_indices_nHits_sig)

with open('Filtered_data/datos_filtrados.pkl', 'rb') as f:
    valores_read, indices_read = pickle.load(f)

with open('Filtered_data/datos_filtrados_sig.pkl', 'rb') as f:
    valores_read_sig, indices_read_sig = pickle.load(f)

def a_lista_de_arrays(plano, indices):
    return [plano[indices[i]:indices[i+1]] for i in range(len(indices)-1)]


times_branch_reconstructed = a_lista_de_arrays(valores_read, indices_read)
times_branch_reconstructed_sig = a_lista_de_arrays(valores_read_sig, indices_read_sig)


# Leer el CSV
df = pd.read_csv('/scratch/cgarcia_2002/Complete_analysis/Neutron_candidates/neutron_candidates_10-50_22-30_Sorted.csv')

# Asegurar tipos consistentes (por si event_number o start_time eran strings o enteros)
df['event_number'] = df['event_number'].astype(int)
df['start_time'] = df['start_time'].astype(float)

# Reconstruir el diccionario anidado
neutron_dict = defaultdict(lambda: defaultdict(list))

for _, row in df.iterrows():
    event_number = int(row['event_number'])
    start_time = row['start_time']
    neutron_time = row['neutron_time']
    neutron_dict[event_number][start_time].append(neutron_time)

# Para neutron_dict
neutron_dict = {k: dict(v) for k, v in neutron_dict.items()}

df_sig = pd.read_csv('/scratch/cgarcia_2002/Complete_analysis/Neutron_candidates/neutron_candidates_sig_10-50_22-30_Sorted.csv')

df_sig['event_number'] = df_sig['event_number'].astype(int)
df_sig['start_time'] = df_sig['start_time'].astype(float)

neutron_dict_sig = defaultdict(lambda: defaultdict(list))

for _, row in df_sig.iterrows():
    event_number = int(row['event_number'])
    start_time = row['start_time']
    neutron_time = row['neutron_time']
    neutron_dict_sig[event_number][start_time].append(neutron_time)

# Para neutron_dict_sig
neutron_dict_sig = {k: dict(v) for k, v in neutron_dict_sig.items()}

##################################################################################

window_ns = 100  # tamaño de la máscara temporal

hits_count_dict = {}

for event_number in neutron_dict:
    event_hits = times_branch_sorted_TOF[event_number]  # lista de tiempos del evento

    hits_count_dict[event_number] = {}

    for start_time in neutron_dict[event_number]:
        # Crear máscara booleana: True si el hit cae dentro de la ventana
        mask = (event_hits >= start_time) & (event_hits < start_time + window_ns)

        # Contar cuántos hits cumplen la condición
        n_hits = np.sum(mask)

        hits_count_dict[event_number][start_time] = n_hits

# 1. Flatten all the n_hits into a single list
all_n_hits = []

for event_dict in hits_count_dict.values():
    for n_hits in event_dict.values():
        all_n_hits.append(n_hits)

hits_count_dict_sig = {}

for event_number in neutron_dict_sig:
    event_hits = times_branch_sorted_TOF_sig[event_number]  # lista de tiempos del evento

    hits_count_dict_sig[event_number] = {}

    for start_time in neutron_dict_sig[event_number]:
        # Crear máscara booleana: True si el hit cae dentro de la ventana
        mask = (event_hits >= start_time) & (event_hits < start_time + window_ns)

        # Contar cuántos hits cumplen la condición
        n_hits = np.sum(mask)

        hits_count_dict_sig[event_number][start_time] = n_hits

# 1. Flatten all the n_hits into a single list
all_n_hits_sig = []

for event_dict in hits_count_dict_sig.values():
    for n_hits in event_dict.values():
        all_n_hits_sig.append(n_hits)

hist, bins_edges = np.histogram(all_n_hits, bins=50, range=(0, 100))
hist_sig, _ = np.histogram(all_n_hits_sig, bins = bins_edges)


# 2. Plot the histogram
plt.figure()
plt.step(bins_edges[:-1], hist, where='post', linewidth=1, color='red', label='Background')
plt.step(bins_edges[:-1], hist_sig * N_events / N_events_sig, where='post', linewidth=1, color='blue', label = 'Data')
plt.xlabel('Number of hits in prompt window')
plt.ylabel('Prompt candidates')
plt.legend()
plt.title('Histogram of n_hits per prompt window')
plt.savefig('Plots/nHitsDistribution_SigBkg_10-50_Sorted.png')

fig, axs = plt.subplots(2, 1, gridspec_kw={'height_ratios': [3, 1]})

# Top plot: Background and Signal
axs[0].step(bins_edges[:-1], hist, where='post', linewidth=1, color='red', label='Background')
axs[0].step(bins_edges[:-1], hist_sig * N_events / N_events_sig, where='post', linewidth=1, color='blue', label = 'Data')
axs[0].set_ylabel('Prompt candidates')
axs[0].set_xlabel('Number of hits in prompt window')
axs[0].set_title('Histogram of nHits per prompt window')
axs[0].legend()

# Bottom plot: Signal/Background Ratio
ratio = np.divide(
    hist_sig * N_events / N_events_sig,
    hist,
    out=np.full_like(hist, 0, dtype=float),
    where=hist > 0)
axs[1].step(bins_edges[:-1], ratio, linewidth = 1, where='post', color='green', label='Signal / Background')
axs[1].set_xlabel("Number of hits in prompt window")
axs[1].set_ylabel("S/B ratio")
axs[1].legend()
plt.tight_layout()
plt.savefig('Plots/nHitsDistribution_SigBkg_10-50_Ratio.png')


"""###################################################################

t_rms_list = []

# Loop over events
for event_number, start_times_dict in neutron_dict_sig.items():
    # Get the list of TOF times for this event
    tof_times = times_branch_sorted_TOF[event_number]
    
    for start_time, neutron_times in start_times_dict.items():
        for neutron_time in neutron_times:
            # Define 100 ns window from neutron_time
            lower_bound = neutron_time
            upper_bound = neutron_time + 100

            # Select hits within the window
            window_hits = [t for t in tof_times if lower_bound <= t < upper_bound]

            if len(window_hits) > 1:  # t_RMS needs at least 2 points
                mean_time = np.mean(window_hits)
                rms = np.sqrt(np.mean((np.array(window_hits) - mean_time) ** 2))
                t_rms_list.append(rms)

# Plot histogram of t_RMS values
plt.figure(figsize=(8, 6))
plt.hist(t_rms_list, bins=50, color='mediumseagreen', edgecolor='black')
plt.xlabel('t_RMS (ns)')
plt.ylabel('Frequency')
plt.title('Histogram of t_RMS in 100 ns windows around neutron times')
plt.grid(True)
plt.tight_layout()
plt.show()"""