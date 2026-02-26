import matplotlib.pyplot as plt
import numpy as np
import matplotlib.gridspec as gridspec

# --- Data Simulation ---
# Capacity Y-axis: 0 to 1600
cap = np.linspace(0, 1600, 200)

# Voltage Profile (Left)
# Charge (0-800)
# Discharge (800-1500)
vol = np.zeros_like(cap)
# Charge
mask_chg = cap <= 800
vol[mask_chg] = 3.8 + 0.2 * (cap[mask_chg]/800)**3
# Discharge
mask_dch = cap > 800
vol[mask_dch] = 3.8 - 0.2 * ((cap[mask_dch]-800)/800)**0.5 # Sharp drop? 
# Actually discharge usually starts high and drops.
# Image: Line goes Up (Charge), then step, then Down (Discharge)?
# No, it's Capacity on Y.
# X is Voltage.
# Bottom part: Charge (V increases ~3.8->4.0 as Cap increases 0->800)
# Top part: Discharge (V decreases 3.8->2.0 as Cap increases 800->1500)
# Wait, Y is Capacity.
# 0 -> 800: Charge. V is X.
# 800 -> 1600: Discharge.
v_chg = 3.8 + 0.2 * (np.linspace(0, 1, 100))**5 # Stays near 3.8 then rises
v_dch = 3.8 - 1.5 * (np.linspace(0, 1, 100))**5 # Stays near 3.8 then drops

# Raman Map (Right)
# X: Raman shift
shift = np.linspace(100, 350, 200)
C, S = np.meshgrid(cap, shift)

# Peaks
# S: ~150 and ~220. Present at low cap (0-400) and high cap (1200-1600)?
# Or maybe disappeared in middle (charged state)?
# Image: "S" at bottom (0-400) and top (1200+). Middle is empty?
# "SCl4" at ~290. Appears in middle (600-1000).

Z = np.zeros_like(C)

# S Peaks
mask_s = (C < 400) | (C > 1200)
Z += 1.0 * mask_s * np.exp(-((S - 150)/10)**2)
Z += 1.0 * mask_s * np.exp(-((S - 220)/10)**2)

# SCl4 Peak
mask_scl4 = (C > 600) & (C < 1000)
Z += 1.0 * mask_scl4 * np.exp(-((S - 290)/10)**2)

# Smooth transitions
Z =  1.0 * np.exp(-((C - 200)/200)**2) * np.exp(-((S - 150)/10)**2) # S bottom
Z += 1.0 * np.exp(-((C - 200)/200)**2) * np.exp(-((S - 220)/10)**2) # S bottom
Z += 1.0 * np.exp(-((C - 1400)/200)**2) * np.exp(-((S - 150)/10)**2) # S top
Z += 1.0 * np.exp(-((C - 1400)/200)**2) * np.exp(-((S - 220)/10)**2) # S top

Z += 1.0 * np.exp(-((C - 800)/150)**2) * np.exp(-((S - 290)/10)**2) # SCl4 middle

# Add noise
Z += np.random.normal(0, 0.05, Z.shape)

# --- Plotting ---
fig = plt.figure(figsize=(10, 5), dpi=150)
gs = gridspec.GridSpec(1, 2, width_ratios=[1, 3], wspace=0.05)

# Left: Voltage
ax1 = fig.add_subplot(gs[0])
ax1.plot(v_chg, np.linspace(0, 800, 100), 'k-')
ax1.plot(v_dch, np.linspace(800, 1600, 100), 'k-')
ax1.set_xlabel('Voltage (V)', fontsize=12)
ax1.set_ylabel('Capacity (mAh g$^{-1}$)', fontsize=12)
ax1.set_xlim(2, 4.2)
ax1.set_ylim(0, 1600)
ax1.axhline(800, color='gray', linestyle='--')
ax1.text(3.5, 400, 'Charge', rotation=90, ha='center', va='center')
ax1.text(3.5, 1200, 'Discharge', rotation=90, ha='center', va='center')

# Right: Heatmap
ax2 = fig.add_subplot(gs[1], sharey=ax1)
# Coolwarm or similar (Blue background, Red peaks)
cmap = plt.cm.coolwarm 
im = ax2.imshow(Z.T, aspect='auto', extent=[100, 350, 0, 1600], origin='lower', cmap=cmap, vmin=-0.2, vmax=1.2)

ax2.set_xlabel('Raman shift (cm$^{-1}$)', fontsize=12)
ax2.set_xlim(100, 350)
ax2.tick_params(labelleft=False)

# Labels
ax2.text(150, 600, 'S', color='white', ha='center')
ax2.text(220, 600, 'S', color='white', ha='center')
ax2.text(290, 1000, 'SCl$_4$', color='white', ha='center')

# Colorbar
cbar = fig.colorbar(im, ax=ax2, pad=0.02, shrink=0.5)
cbar.set_ticks([0, 1])
cbar.set_ticklabels(['Low', 'High'])

plt.show()
