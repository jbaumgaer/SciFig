import matplotlib.pyplot as plt
import numpy as np

# --- Data Simulation ---
soc = np.linspace(0, 105, 100)

# Voltage Profile (Grey line)
# Typical NCM charge curve
vol = 3.6 + 0.005 * soc + 0.1 * np.exp((soc-50)/20) 
vol = np.clip(vol, 3.0, 4.5)
# Add steps
vol += 0.05 * np.tanh((soc-5)/2) # Initial rise

# Gas Evolution (SC92 - Left)
# CO2 (Blue)
co2_sc = np.zeros_like(soc)
co2_sc[soc > 70] = 0.5 * np.exp((soc[soc > 70]-70)/10)
co2_sc[soc > 90] = co2_sc[soc > 90] + 5 * np.exp((soc[soc > 90]-90)/5)

# O2 (Red)
o2_sc = np.zeros_like(soc)
o2_sc[soc > 70] = 0.1 * np.exp((soc[soc > 70]-70)/10)

# Gas Evolution (IBP-SC92 - Right)
# Reduced
co2_ibp = co2_sc * 0.3
o2_ibp = o2_sc * 0.2

# --- Plotting ---
fig, (ax1, ax2) = plt.subplots(1, 2, figsize=(10, 5), dpi=150, sharey=True)
plt.subplots_adjust(wspace=0.05)

# Panel 1: SC92
# Left Axis: Voltage
ax1.plot(soc, vol, color='#999999', lw=3)
ax1.set_ylabel('Voltage (V)', fontsize=14)
ax1.set_xlabel('SOC (%)', fontsize=14)
ax1.set_xlim(-5, 105)
ax1.set_ylim(2.9, 4.6)

# Right Axis: Gas
ax1r = ax1.twinx()
ax1r.plot(soc[::2], co2_sc[::2], 'o', color='#4488CC', markeredgecolor='white', markersize=6, label='CO$_2$')
ax1r.plot(soc[::2], o2_sc[::2], 'o', color='#EE4444', markeredgecolor='white', markersize=6, label='O$_2$')
ax1r.set_ylim(-1, 30)
ax1r.set_yticks([]) # Hide ticks on left panel right axis

# Panel 2: IBP-SC92
# Left Axis: Voltage
ax2.plot(soc, vol, color='#999999', lw=3)
ax2.set_xlabel('SOC (%)', fontsize=14)
ax2.set_xlim(-5, 105)

# Right Axis: Gas
ax2r = ax2.twinx()
ax2r.plot(soc[::2], co2_ibp[::2], 'o', color='#4488CC', markeredgecolor='white', markersize=6, label='CO$_2$')
ax2r.plot(soc[::2], o2_ibp[::2], 'o', color='#EE4444', markeredgecolor='white', markersize=6, label='O$_2$')
ax2r.set_ylim(-1, 30)
ax2r.set_ylabel(r'mmol min$^{-1}$', fontsize=14, rotation=270, labelpad=20)

# Annotations (Dashed lines)
# SC92
ax1.hlines([4.087, 4.236], 0, 90, linestyle='--', color='gray')
ax1.vlines([70, 90], 2.9, 4.3, linestyle='--', color='gray')
ax1.text(30, 4.1, '4.087 V', ha='center')
ax1.text(60, 4.25, '4.236 V', ha='center')

# IBP
ax2.hlines([4.214, 4.347], 0, 90, linestyle='--', color='gray')
ax2.vlines([80, 95], 2.9, 4.4, linestyle='--', color='gray')
ax2.text(40, 4.23, '4.214 V', ha='center')
ax2.text(70, 4.36, '4.347 V', ha='center')

# Labels
ax1.text(0.05, 0.95, 'SC92', transform=ax1.transAxes, fontsize=12)
ax2.text(0.05, 0.95, 'IBP-SC92', transform=ax2.transAxes, fontsize=12)

# Legends
ax1r.legend(loc='lower left', bbox_to_anchor=(0.1, 0.1), frameon=False)
ax2r.legend(loc='lower left', bbox_to_anchor=(0.1, 0.1), frameon=False)

plt.show()
