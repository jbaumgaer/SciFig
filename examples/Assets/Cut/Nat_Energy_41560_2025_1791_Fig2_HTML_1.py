import matplotlib.pyplot as plt
import numpy as np

# --- Data Simulation ---
wavenumber = np.linspace(3500, 2800, 500)

def peak(x, center, width, depth):
    return -depth * np.exp(-((x - center)**2) / (2 * width**2))

# Common Baseline
baseline = 100

# 1. IPA
y_ipa = baseline + peak(wavenumber, 3350, 60, 20) # Broad OH
y_ipa += peak(wavenumber, 2970, 5, 45) # Sharp CH
y_ipa += peak(wavenumber, 2930, 10, 15)
y_ipa += peak(wavenumber, 2880, 10, 10)

# 2. IPA + PbI2 (Shifted/Changed)
y_ipa_pbi2 = baseline + peak(wavenumber, 3320, 60, 25) # Shifted OH
y_ipa_pbi2 += peak(wavenumber, 2970, 5, 40)
y_ipa_pbi2 += peak(wavenumber, 2930, 8, 12)
y_ipa_pbi2 += peak(wavenumber, 2880, 8, 8)
# Add slope
y_ipa_pbi2 -= (wavenumber - 2800) * 0.02

# 3. FIPA
y_fipa = baseline + peak(wavenumber, 3380, 50, 35) # Sharpish NH/OH
y_fipa += peak(wavenumber, 3050, 20, 5)
y_fipa += peak(wavenumber, 2950, 40, 5) # Broad underlying

# 4. FIPA + PbI2
y_fipa_pbi2 = baseline + peak(wavenumber, 3400, 60, 30)
y_fipa_pbi2 += peak(wavenumber, 3150, 80, 15) # Broad new feature
y_fipa_pbi2 += peak(wavenumber, 2850, 40, 10)
y_fipa_pbi2 -= (wavenumber - 2800) * 0.03


# --- Plotting ---
fig, axes = plt.subplots(2, 2, figsize=(8, 6), dpi=150, sharex=True, sharey='row')
plt.subplots_adjust(wspace=0, hspace=0)

# Dataset mapping
plots = [
    (axes[0, 0], y_ipa, 'gray', 'IPA'),
    (axes[1, 0], y_ipa_pbi2, '#005566', 'IPA + PbI$_2$'),
    (axes[0, 1], y_fipa, 'gray', 'FIPA'),
    (axes[1, 1], y_fipa_pbi2, '#005566', 'FIPA + PbI$_2$')
]

for ax, y, col, lbl in plots:
    ax.plot(wavenumber, y, color=col, linewidth=1.5)
    ax.text(2850, np.min(y)+5, lbl, ha='right', fontsize=12)

    # Ticks
    ax.set_xlim(3500, 2800) # Reversed axis
    ax.tick_params(direction='out')

# Y Labels (only left)
axes[0, 0].set_ylabel('Transmittance (%)', fontsize=12)
axes[0, 0].yaxis.set_label_coords(-0.15, 0) # Center across rows? No, just top row?
# Actually y-axis is shared by row, so label usually goes on the far left center
fig.text(0.04, 0.5, 'Transmittance (%)', va='center', rotation='vertical', fontsize=12)

# X Label
fig.text(0.5, 0.04, r'Wavenumber (cm$^{-1}$)', ha='center', fontsize=12)

# Hide inner ticks/labels if needed
axes[0, 0].set_xticklabels([])
axes[0, 1].set_xticklabels([])
axes[0, 1].set_yticks([])
axes[1, 1].set_yticks([])

plt.show()
