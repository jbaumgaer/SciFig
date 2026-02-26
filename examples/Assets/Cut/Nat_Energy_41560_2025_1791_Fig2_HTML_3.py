import matplotlib.pyplot as plt
import numpy as np

# --- Data Simulation ---
ppm = np.linspace(-20, -120, 500) # Reversed axis

def lorentzian(x, center, width, height):
    return height * (width**2 / ((x - center)**2 + width**2))

# 1. FIPA (Top)
# Sharp peak at -72, broad base
y_fipa = lorentzian(ppm, -72, 0.2, 10) + lorentzian(ppm, -70, 2, 1) + lorentzian(ppm, -74, 2, 0.5)
# Wiggles/Noise
y_fipa += 0.2 * np.sin(ppm)

# 2. FIPA/PbI2 (Bottom)
# Sharp peak at -72, very flat baseline
y_mix = lorentzian(ppm, -72, 0.15, 8) 
y_mix += 0.05 * np.sin(ppm)

# Offset
y_fipa += 5

# --- Plotting ---
fig, ax = plt.subplots(figsize=(6, 5), dpi=150)

# Plot
ax.plot(ppm, y_fipa, color='gray', lw=1.5)
ax.text(-100, 8, 'FIPA', fontsize=12)

ax.plot(ppm, y_mix, color='#005566', lw=1.5)
ax.text(-100, 3, 'FIPA/PbI$_2$', fontsize=12)

# Styling
ax.set_xlabel('Chemical shift (ppm)', fontsize=14)
ax.set_xlim(-20, -120) # Reversed
ax.set_yticks([])
ax.set_ylim(-1, 15)

# Ticks
ax.minorticks_on()
ax.tick_params(direction='out', top=False, right=False)

plt.tight_layout()
plt.show()
