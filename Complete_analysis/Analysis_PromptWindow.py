print("Iniciando el script de análisis windows prompt...")
print("Importando librerias necesarias...")

import numpy as np
import matplotlib.pyplot as plt
import pandas as pd
from scipy.optimize import curve_fit
from collections import defaultdict
import matplotlib.ticker as ticker
import glob
import os
import pickle
import argparse

import functions_spills
import functions_analysis

from matplotlib import rcParams
rcParams['mathtext.fontset'] = 'stix'
rcParams['font.family'] = 'STIXGeneral'
rcParams['figure.figsize'] = [10, 8]
rcParams['font.size'] = 22

# Crear el parser
parser = argparse.ArgumentParser(description="Window size")

# Agregar argumento opcional con valor por defecto
parser.add_argument(
    "--window_size",
    type = int, 
    help="Window size to analyse nHits distribution",
    default=100
)

# Parsear argumentos
args = parser.parse_args()
window_size = args.window_size
print("Analizando window size", window_size)

with open('Filtered_data/datos_filtrados.pkl', 'rb') as f:
    valores_read, indices_read = pickle.load(f)

with open('Filtered_data/datos_filtrados_sig.pkl', 'rb') as f:
    valores_read_sig, indices_read_sig = pickle.load(f)

times_branch_filtered = functions_analysis.a_lista_de_arrays(valores_read, indices_read)
times_branch_filtered_sig = functions_analysis.a_lista_de_arrays(valores_read_sig, indices_read_sig)

print("Datos filtrados descargados")
N_events = len(times_branch_filtered)
N_events_sig = len(times_branch_filtered_sig)

print("Numero de eventos bkg", N_events)
print("Numero de eventos señal", N_events_sig)

nHitsDistribution_dict = {}

for event in np.arange(0, N_events, 1):
    if event%1000==0:
        print(f"Analizando evento {event}")
    _, nHits_i = functions_analysis.count_nHits(times_branch_filtered[event], window_size, 10, 300)
    if len(nHits_i) != 0:
        nHitsDistribution_dict[event] = nHits_i
print("Conteo nHits bkg finalizado")

nHitsDistribution_dict_sig = {}

for event in np.arange(0, N_events_sig, 1):
    if event%1000==0:
        print(f"Analizando evento {event}")
    _, nHits_i = functions_analysis.count_nHits(times_branch_filtered_sig[event], window_size, 10, 300)
    if len(nHits_i)!=0:
        nHitsDistribution_dict_sig[event] = nHits_i
print("Conteo nHits data finalizado")

all_n_hits = []
for nHits_list in nHitsDistribution_dict.values():
    all_n_hits.extend(nHits_list)

all_n_hits_sig = []
for nHits_list in nHitsDistribution_dict_sig.values():
    all_n_hits_sig.extend(nHits_list)

hist, bins_edges = np.histogram(all_n_hits, bins=100, range=(0, 300))
hist_sig, _ = np.histogram(all_n_hits_sig, bins = bins_edges)

plt.figure()
plt.step(bins_edges[:-1], hist, where='post', linewidth=1, color='red', label='Background')
plt.step(bins_edges[:-1], hist_sig * N_events / N_events_sig, where='post', linewidth=1, color='blue', label = 'Data')
plt.xlabel('Number of hits')
plt.ylabel('Windows')
plt.legend()
plt.title(f'Histogram nHits per {window_size} ns window')
plt.savefig(f"nHitsDistribution_window{window_size}.png")

print("Figura guardada")