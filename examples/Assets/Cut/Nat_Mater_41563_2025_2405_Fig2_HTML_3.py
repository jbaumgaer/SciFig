import matplotlib.pyplot as plt
import numpy as np

# --- Data Simulation ---
energy = np.linspace(22050, 22500, 500)
edge_pos = 22117 # Ru K-edge approx

def xanes_model(e, edge, shift=0, osc_amp=0.05, osc_freq=0.05):
    # Step function
    step = 0.5 * (1 + np.tanh((e - (edge + shift)) / 10))
    # White line peak
    peak = 0.8 * np.exp(-((e - (edge + shift + 15))**2) / (2 * 10**2))
    # Oscillations (EXAFS)
    k = np.sqrt(np.maximum(0, e - (edge+shift) - 20)) * 0.51
    osc = osc_amp * np.sin(2 * k * 2 + 1) * np.exp(-0.02*k) * step

    return step + peak + osc

# References
y_rufoil = xanes_model(energy, edge_pos, shift=0, osc_amp=0.1) # Black Dash
y_ruo2 = xanes_model(energy, edge_pos, shift=2.5, osc_amp=0.05) # Orange Dash
y_kbru = xanes_model(energy, edge_pos, shift=0.5, osc_amp=0.08) # Blue Dash

# Samples
y_300 = xanes_model(energy, edge_pos, shift=1.0, osc_amp=0.06) # Red
y_550 = xanes_model(energy, edge_pos, shift=0.8, osc_amp=0.07) # Blue
y_800 = xanes_model(energy, edge_pos, shift=0.6, osc_amp=0.07) # Green

# --- Plotting ---
fig, ax = plt.subplots(figsize=(6, 5), dpi=150)

# Plots
ax.plot(energy, y_rufoil, 'k--', label='Ru foil', lw=1.5)
ax.plot(energy, y_ruo2, '--', color='#D2691E', label='RuO$_2$', lw=1.5)
ax.plot(energy, y_kbru, '--', color='#4682B4', label='KB@Ru', lw=1.5)

ax.plot(energy, y_300, '-', color='#993333', label='KB@RuP-300', lw=1.5)
ax.plot(energy, y_550, '-', color='#006699', label='KB@RuP-550', lw=1.5)
ax.plot(energy, y_800, '-', color='#336633', label='KB@RuP-800', lw=1.5)

# Styling
ax.set_xlabel('Energy (eV)', fontsize=14)
ax.set_ylabel('Intensity (a.u.)', fontsize=14)
ax.set_xlim(22050, 22500)
ax.set_ylim(0, 1.8)
ax.set_yticks([])

# Legend
ax.legend(frameon=False, loc='lower right', fontsize=11)

# Inset Zoom
ax_ins = ax.inset_axes([0.2, 0.3, 0.35, 0.35])
# Plot fit range
e_zoom = np.linspace(22100, 22140, 100)
ax_ins.plot(e_zoom, xanes_model(e_zoom, edge_pos, 0, 0.1), 'k--', lw=1.5) # Ru
ax_ins.plot(e_zoom, xanes_model(e_zoom, edge_pos, 2.5, 0.05), '--', color='#D2691E', lw=1.5) # RuO2
ax_ins.plot(e_zoom, xanes_model(e_zoom, edge_pos, 0.5, 0.08), '--', color='#4682B4', lw=1.5) # KB@Ru

ax_ins.plot(e_zoom, xanes_model(e_zoom, edge_pos, 1.0, 0.06), '-', color='#993333', lw=1.5)
ax_ins.plot(e_zoom, xanes_model(e_zoom, edge_pos, 0.8, 0.07), '-', color='#006699', lw=1.5)
ax_ins.plot(e_zoom, xanes_model(e_zoom, edge_pos, 0.6, 0.07), '-', color='#336633', lw=1.5)

ax_ins.set_xlim(22110, 22125)
ax_ins.set_ylim(0.4, 0.9)
ax_ins.set_xticks([])
ax_ins.set_yticks([])

# Arrow in Inset
ax_ins.arrow(22112, 0.6, 8, 0, head_width=0.05, color='black')

# Connection lines (Optional)
# from matplotlib.patches import ConnectionPatch
# ... omitted for simplicity

plt.tight_layout()
plt.show()
