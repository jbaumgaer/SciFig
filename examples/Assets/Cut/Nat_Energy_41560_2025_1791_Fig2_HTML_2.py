import matplotlib.pyplot as plt
import numpy as np

# --- Data Simulation ---
two_theta = np.linspace(4, 15, 500)

def lorentzian(x, center, width, height):
    return height * (width**2 / ((x - center)**2 + width**2))

baseline = 0.5

# 1. IPA (Top)
y_ipa = baseline + lorentzian(two_theta, 4.5, 0.1, 1.5) + lorentzian(two_theta, 5.2, 0.15, 4.0) + \
        lorentzian(two_theta, 6.8, 0.2, 0.8) + lorentzian(two_theta, 10.5, 0.2, 0.3) + \
        lorentzian(two_theta, 12.5, 0.2, 0.5)

# 2. DIPA (Middle)
y_dipa = baseline + lorentzian(two_theta, 5.2, 0.15, 3.5) + lorentzian(two_theta, 6.8, 0.2, 0.3) + \
         lorentzian(two_theta, 10.5, 0.2, 0.3) + lorentzian(two_theta, 12.5, 0.1, 6.0)

# 3. FIPA (Bottom)
y_fipa = baseline + lorentzian(two_theta, 4.5, 0.1, 0.5) + lorentzian(two_theta, 5.2, 0.2, 0.3) + \
         lorentzian(two_theta, 12.5, 0.1, 7.0)

# Offset
y_dipa += 6
y_ipa += 12

# --- Plotting ---
fig, ax = plt.subplots(figsize=(6, 6), dpi=150)

# Plot
ax.plot(two_theta, y_ipa, color='gray', lw=1.5)
ax.text(9, 14, 'IPA', fontsize=12)

ax.plot(two_theta, y_dipa, color='#009999', lw=1.5)
ax.text(9, 8, 'DIPA', fontsize=12)

ax.plot(two_theta, y_fipa, color='#005566', lw=1.5)
ax.text(9, 2, 'FIPA', fontsize=12)

# Styling
ax.set_xlabel(r'2$\theta$ (°)', fontsize=14)
ax.set_ylabel('Intensity (a.u.)', fontsize=14)
ax.set_xlim(4, 15)
ax.set_ylim(0, 18)
ax.set_yticks([])

# Ticks
ax.minorticks_on()
ax.tick_params(direction='out', top=False, right=False)

plt.tight_layout()
plt.show()
