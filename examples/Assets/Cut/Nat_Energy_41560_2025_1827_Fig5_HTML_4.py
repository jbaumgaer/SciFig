import matplotlib.pyplot as plt
import numpy as np

# --- Data Simulation ---
energy = np.linspace(8330, 8360, 300)

def peak(x, center, width, height):
    # Asymmetric peak for edge
    return height * np.exp(-((x - center)**2) / (2 * width**2)) * (1 + 0.5*np.tanh(x-center))

# Base step
step = 0.5 * (1 + np.tanh((energy - 8343)/5))

# Top Panel (Charging)
y_pristine = step + peak(energy, 8350, 3, 0.8)
y_chg_43 = step + peak(energy, 8351.5, 3, 0.8)
y_chg_45 = step + peak(energy, 8352.8, 3, 0.8)

# Bottom Panel (Discharging)
y_dch_42 = step + peak(energy, 8352.5, 3, 0.8)
y_dch_40 = step + peak(energy, 8351.5, 3, 0.8)
y_dch_30 = step + peak(energy, 8350, 3, 0.8)

# --- Plotting ---
fig, (ax1, ax2) = plt.subplots(2, 1, figsize=(6, 7), dpi=150, sharex=True, gridspec_kw={'hspace': 0})

# Top
ax1.plot(energy, y_pristine, color='#883333', lw=2, label='Pristine')
ax1.plot(energy, y_chg_43, color='#EE4444', lw=2, label='Char. 4.3 V')
ax1.plot(energy, y_chg_45, color='#FFAA66', lw=2, label='Char. 4.5 V')

# Annotations Top
ax1.annotate('', xy=(8350, 1.4), xytext=(8352.8, 1.4), arrowprops=dict(arrowstyle='<->', color='#445566'))
ax1.text(8351.4, 1.45, '2.80 eV', ha='center', fontsize=10)
ax1.vlines([8350, 8352.8], 1.0, 1.4, linestyle='--', color='gray')

# Bottom
ax2.plot(energy, y_dch_42, color='#FFEEAA', lw=2, label='Dischar. 4.2 V')
ax2.plot(energy, y_dch_40, color='#88CCEE', lw=2, label='Dischar. 4.0 V')
ax2.plot(energy, y_dch_30, color='#3366AA', lw=2, label='Dischar. 3.0 V')

# Legend
ax1.legend(frameon=False, loc='upper left', fontsize=10)
ax2.legend(frameon=False, loc='upper left', fontsize=10)

# Styling
ax2.set_xlabel('Energy (eV)', fontsize=14)
ax1.set_ylabel('Normalized $\chi\mu$ (a.u.)', fontsize=14) # Shared Y label logic better placed manually?
# Just putting it on top panel
# ax1.yaxis.set_label_coords(-0.1, 0) # Center?

ax1.set_xlim(8330, 8360)
ax1.set_ylim(0, 1.6)
ax2.set_ylim(0, 1.6)
ax1.set_yticks([])
ax2.set_yticks([])

# Text SC92
ax2.text(0.95, 0.1, 'SC92', transform=ax2.transAxes, ha='right', fontsize=12)

plt.tight_layout()
plt.show()
