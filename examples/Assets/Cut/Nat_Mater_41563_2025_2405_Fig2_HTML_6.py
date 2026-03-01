import matplotlib.pyplot as plt
import numpy as np

# --- Data Simulation ---
r = np.linspace(0, 6, 300)

def peak(x, center, width, height):
    # Lorentzian-like shape
    return height / (1 + ((x - center)/width)**2)

# References
# Ru foil: Strong Ru-Ru at ~2.4
y_ru = peak(r, 2.4, 0.2, 1.0) + peak(r, 4.5, 0.5, 0.1)
# RuO2: Ru-O at ~1.5, Ru-Ru/O at ~3.1
y_ruo2 = peak(r, 1.5, 0.3, 0.8) + peak(r, 3.1, 0.4, 0.4)
# KB@Ru: Mixed
y_kbru = peak(r, 1.5, 0.4, 0.6) + peak(r, 2.4, 0.5, 0.2) + peak(r, 3.2, 0.5, 0.2)

# Samples (Ru-P peaks)
# 300: Ru-P dominant at ~2.0? Or mix. Image shows broad peak 1.5-2.0
y_300 = peak(r, 1.6, 0.4, 0.7) + peak(r, 2.6, 0.3, 0.1)
# 550:
y_550 = peak(r, 1.5, 0.4, 0.8) + peak(r, 2.6, 0.3, 0.15)
# 800:
y_800 = peak(r, 1.5, 0.4, 0.8) + peak(r, 3.2, 0.5, 0.2)

# Noise and Offset
noise = 0.02
y_ru += np.random.normal(0, noise, len(r)) + 4.0
y_ruo2 += np.random.normal(0, noise, len(r)) + 3.2
y_kbru += np.random.normal(0, noise, len(r)) + 2.4
y_300 += np.random.normal(0, noise, len(r)) + 1.6
y_550 += np.random.normal(0, noise, len(r)) + 0.8
y_800 += np.random.normal(0, noise, len(r)) + 0.0

# --- Plotting ---
fig, ax = plt.subplots(figsize=(6, 6), dpi=150)

# Plots
ax.plot(r, y_ru, 'k--', label='Ru foil', lw=1.5)
ax.plot(r, y_ruo2, '--', color='#D2691E', label='RuO$_2$', lw=1.5)
ax.plot(r, y_kbru, '--', color='#4682B4', label='KB@Ru', lw=1.5)

ax.plot(r, y_300, '-', color='#993333', label='KB@RuP-300', lw=1.5)
ax.plot(r, y_550, '-', color='#006699', label='KB@RuP-550', lw=1.5)
ax.plot(r, y_800, '-', color='#336633', label='KB@RuP-800', lw=1.5)

# Labels
ax.text(5.8, 4.2, 'Ru foil', ha='right', fontsize=12)
ax.text(5.8, 3.4, 'RuO$_2$', ha='right', color='#D2691E', fontsize=12)
ax.text(5.8, 2.6, 'KB@Ru', ha='right', color='#4682B4', fontsize=12)
ax.text(5.8, 1.8, 'KB@RuP-300', ha='right', color='#993333', fontsize=12)
ax.text(5.8, 1.0, 'KB@RuP-550', ha='right', color='#006699', fontsize=12)
ax.text(5.8, 0.2, 'KB@RuP-800', ha='right', color='#336633', fontsize=12)

# Annotations (Dashed lines and Text)
ax.plot([1.5, 1.5], [0.5, 3.8], 'k--', lw=1.5, alpha=0.7) # Ru-O
ax.text(0.8, 3.6, 'Ru-O', fontsize=12)

ax.plot([2.4, 2.4], [3.8, 4.8], 'k--', lw=1.5, alpha=0.7) # Ru-Ru
ax.text(2.6, 4.4, 'Ru-Ru', fontsize=12)

ax.plot([1.8, 1.8], [0.5, 2.2], 'k--', lw=1.5, alpha=0.7) # Ru-P
ax.text(2.0, 2.0, 'Ru-P', fontsize=12)

# Styling
ax.set_xlabel(r'$R$ ($\AA$)', fontsize=14)
ax.set_ylabel(r'FT ($k^3 x(k)$)', fontsize=14)
ax.set_xlim(0, 6)
ax.set_yticks([]) # Hide Y ticks
ax.set_ylim(-0.5, 5.0)

plt.tight_layout()
plt.show()
