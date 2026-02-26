import matplotlib.pyplot as plt
import numpy as np

# --- Data Simulation ---
soc = np.linspace(0, 90, 50)

# SC-NC 91 (Blue)
# Decreases from 2.877 to 2.815
a_nc = 2.877 - 0.0007 * soc
# Slight curvature
a_nc -= 0.000005 * soc**2
# Split/Jump at ~50%? No, the blue curve splits at ~60% in image?
# Actually looks like one curve.
# Let's check image again: Blue dots go 0->50, then gap, then 55->90 (lower branch).
# Ah, there is a jump.
mask_nc_1 = soc < 50
mask_nc_2 = soc > 55
soc_nc_1 = soc[mask_nc_1]
a_nc_1 = 2.877 - 0.0008 * soc_nc_1
soc_nc_2 = soc[mask_nc_2]
a_nc_2 = 2.83 - 0.0005 * (soc_nc_2 - 55)

# SC-NM 91 (Red)
# Higher starting a
a_nm = 2.883 - 0.0006 * soc
# At 70%, it splits into Pink and Yellow
mask_nm_main = soc < 70
soc_nm_main = soc[mask_nm_main]
a_nm_main = 2.883 - 0.00075 * soc_nm_main

# Accelerated (Pink)
soc_nm_acc = np.linspace(70, 85, 10)
a_nm_acc = 2.83 - 0.0006 * (soc_nm_acc - 70)

# Sluggish (Yellow)
soc_nm_slg = np.linspace(70, 85, 10)
a_nm_slg = 2.831 - 0.0002 * (soc_nm_slg - 70) # Flatter

# --- Plotting ---
fig, ax = plt.subplots(figsize=(6, 5), dpi=150)

# Blue (SC-NC 91)
ax.plot(soc_nc_1, a_nc_1, 'o', color='#4488EE', markersize=6, label='SC-NC 91')
ax.plot(soc_nc_2, a_nc_2, 'o', color='#4488EE', markersize=6)

# Red (SC-NM 91 low SoC)
ax.plot(soc_nm_main, a_nm_main, 'o', color='#FF5555', markersize=6, label='SC-NM 91 (low SoC)')

# Pink (Accelerated)
ax.plot(soc_nm_acc, a_nm_acc, 'o', color='#FF9999', markersize=6, label='SC-NM 91 (accelerated)')

# Yellow (Sluggish)
ax.plot(soc_nm_slg, a_nm_slg, 'o', color='#FFCC88', markersize=6, label='SC-NM 91 (sluggish)')

# Dashed Lines
ax.hlines(2.824, 0, 85, linestyle='--', color='black')
ax.hlines(2.813, 0, 85, linestyle='--', color='black')

# Text
ax.text(5, 2.825, r'$\Delta a_{\max} = 2.1\%$', color='#CC3333', fontsize=12, va='bottom')
ax.text(5, 2.814, r'$\Delta a_{\max} = 2.1\%$', color='#0066AA', fontsize=12, va='bottom')

# Arrow
ax.annotate('', xy=(45, 2.835), xytext=(48, 2.832), arrowprops=dict(arrowstyle='->', color='gold', lw=2))

# Styling
ax.set_xlabel('SoC (%)', fontsize=14)
ax.set_ylabel(r'$a$ lattice ($\AA$)', fontsize=14)
ax.set_xlim(0, 95)
ax.set_ylim(2.805, 2.89)

# Legend
ax.legend(frameon=False, loc='upper right', fontsize=10)

# Ticks
ax.minorticks_on()
ax.tick_params(direction='out', top=False, right=False)
ax.spines['top'].set_visible(False)
ax.spines['right'].set_visible(False)

plt.tight_layout()
plt.show()
