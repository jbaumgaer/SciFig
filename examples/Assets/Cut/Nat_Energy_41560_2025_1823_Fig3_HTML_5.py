import matplotlib.pyplot as plt
import numpy as np

# --- Data Simulation ---
wl = np.linspace(500, 1000, 300)

def peak(x, center, width, height):
    return height * np.exp(-((x - center)**2) / (2 * width**2))

# 1. m-ZrO2 + perovskite (Large)
# HDI (Red Circle)
y_zro2_hdi = peak(wl, 800, 25, 1.0)
# Control (Blue Circle)
y_zro2_ctrl = peak(wl, 800, 25, 0.4)

# 2. m-TiO2 + perovskite (Small)
# HDI (Red Square)
y_tio2_hdi = peak(wl, 800, 25, 0.1)
# Control (Blue Square)
y_tio2_ctrl = peak(wl, 800, 25, 0.05)

# --- Plotting ---
fig, ax = plt.subplots(figsize=(6, 5), dpi=150)

# Plots
# m-ZrO2
ax.plot(wl[::5], y_zro2_hdi[::5], 'o', color='#FF5555', mfc='none', markersize=8, mew=2, label='HDI treated (ZrO$_2$)')
ax.plot(wl[::5], y_zro2_ctrl[::5], 'o', color='#4488CC', mfc='none', markersize=8, mew=2, label='Control (ZrO$_2$)')

# m-TiO2
ax.plot(wl[::5], y_tio2_hdi[::5], 's', color='#FF5555', mfc='none', markersize=6, mew=1.5, label='HDI treated (TiO$_2$)')
ax.plot(wl[::5], y_tio2_ctrl[::5], 's', color='#4488CC', mfc='none', markersize=6, mew=1.5, label='Control (TiO$_2$)')

# Text Boxes
ax.text(550, 0.9, 'm-ZrO$_2$ + perovskite', fontsize=12, bbox=dict(facecolor='white', edgecolor='black'))
ax.text(550, 0.65, 'm-TiO$_2$ + perovskite', fontsize=12, bbox=dict(facecolor='white', edgecolor='black'))

# Custom Legend within the boxes logic or simplified
# The image puts legends inside the text boxes area.
# I'll just rely on the plot markers for visual similarity.
ax.text(600, 0.85, '—o  HDI treated', color='black', fontsize=10)
ax.text(600, 0.80, '—o  Control', color='black', fontsize=10)

ax.text(600, 0.60, '—s  HDI treated', color='black', fontsize=10)
ax.text(600, 0.55, '—s  Control', color='black', fontsize=10)


# Styling
ax.set_xlabel('Wavelength (nm)', fontsize=14)
ax.set_ylabel('Intensity (a.u.)', fontsize=14)
ax.set_xlim(500, 1000)
ax.set_ylim(0, 1.1)
ax.set_yticks([]) # Hide Y ticks

# Ticks
ax.minorticks_on()
ax.tick_params(direction='in', top=True, right=True)

plt.tight_layout()
plt.show()
