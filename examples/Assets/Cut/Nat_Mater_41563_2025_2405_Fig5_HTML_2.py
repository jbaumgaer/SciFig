import matplotlib.pyplot as plt
import numpy as np

# --- Data Simulation ---
wn = np.linspace(0, 4000, 500)

def peak(x, center, width, height):
    return height * np.exp(-((x - center)**2) / (2 * width**2))

# Fitting data (Smooth)
y_fit = peak(wn, 500, 300, 0.9) + peak(wn, 1600, 150, 0.4) + peak(wn, 3400, 200, 0.2) + peak(wn, 3700, 100, 0.4)

# Raw data (Noisy)
y_raw = y_fit + np.random.normal(0, 0.1, len(wn))
y_raw = np.maximum(0, y_raw)

# --- Plotting ---
fig, ax = plt.subplots(figsize=(6, 5), dpi=150)

# Raw
ax.plot(wn, y_raw, color='#DDAAAA', lw=0.8, label='Raw data')
# Fit
ax.plot(wn, y_fit, color='#AA4444', lw=2.5, label='Fitting data')

# Shaded region
ax.axvspan(2600, 4000, color='#FFEEEE', alpha=0.5, zorder=0)

# Text
ax.text(1500, 0.9, 'RuP$_2$', fontsize=14)

# Legend
ax.legend(frameon=False, loc='upper right', fontsize=12)

# Styling
ax.set_xlabel(r'Wave number (cm$^{-1}$)', fontsize=14)
ax.set_ylabel('VDOS (a.u.)', fontsize=14)
ax.set_xlim(0, 4000)
ax.set_ylim(0, 1.1)
ax.set_yticks([])

# Ticks
ax.minorticks_on()
ax.tick_params(direction='out', top=False, right=False)

plt.tight_layout()
plt.show()
