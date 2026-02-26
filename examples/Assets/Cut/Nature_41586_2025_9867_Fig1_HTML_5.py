import matplotlib.pyplot as plt
import numpy as np

# --- Data Simulation ---
# Mass
mz_val = 136.8781
mz_range = np.linspace(136.5, 137.2, 100)

# Intensities (Alternating)
intensities = [0.1, 2.5e7, 0.2, 2.7e7, 0.1]
colors = ['blue', 'red', 'blue', 'red', 'blue']

# --- Plotting ---
fig, axes = plt.subplots(5, 1, figsize=(4, 6), dpi=150, sharex=True)
plt.subplots_adjust(hspace=0.1)

for i, (ax, inten, col) in enumerate(zip(axes, intensities, colors)):
    ax.vlines(mz_val, 0, inten, color=col, lw=2)
    ax.set_ylim(0, 3e7)
    
    # Y Ticks
    if i < 4:
        ax.set_yticks([0, 2e7])
        ax.set_yticklabels(['0', '2'])
    else:
        ax.set_yticks([0, 2e7])
        ax.set_yticklabels(['0', '2'])
        
    if i != 2:
        ax.set_ylabel('') # Only middle label? Or all?
        
# Text
axes[1].text(136.9, 2.5e7, r'$m/z = 136.8781$', fontsize=12)
axes[0].text(136.5, 2.5e7, r'$	imes 10^7$', fontsize=10)
fig.text(0.02, 0.5, 'Intensity (cps)', va='center', rotation='vertical', fontsize=14)

# Inset Molecule (Placeholder)
axes[1].text(136.6, 1e7, 'Cl-S$^+$-Cl
    | 
   Cl', fontsize=10)

# X Label
axes[-1].set_xlabel('$m/z$', fontsize=14)
axes[-1].set_xlim(136.5, 137.2)

plt.show()
