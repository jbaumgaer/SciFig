import matplotlib.pyplot as plt
import numpy as np

# --- Data Simulation ---
wn = np.linspace(1500, 8000, 1000)

def lorentzian(x, center, width, height):
    return height / (1 + ((x - center)/width)**2)

# C2H (Blue)
y_c2h = np.zeros_like(wn)
# v(C=C) ~1850 (sharp, high) - actually ~1600 in image?
# Image: First peak at < 2000. Let's say 1850.
y_c2h += lorentzian(wn, 1850, 50, 80) 
# v(C-H) ~3300
y_c2h += lorentzian(wn, 3300, 60, 20)
# 2v(C-H) ~6400
y_c2h += lorentzian(wn, 6400, 80, 8)
# Overtones / Comb
y_c2h += lorentzian(wn, 7400, 100, 10) + lorentzian(wn, 7600, 100, 8)

# C2D (Olive)
y_c2d = np.zeros_like(wn)
# v(C=C) ~1800 (smaller)
y_c2d += lorentzian(wn, 1800, 50, 15)
# v(C-D) ~2400
y_c2d += lorentzian(wn, 2400, 60, 5)
# 3v(C=C) ~4800 (sharp)
y_c2d += lorentzian(wn, 4750, 40, 60) # Wait, 3v(C=C) label points to ~4700 peak for Olive?
# Let's match labels
# Blue Peak 1: v(C=C) ~1850
# Olive Peak 1: v(C=C) ~1700 (small)
# Olive Peak 2: v(C-D) ~2400
# Blue Peak 2: v(C-H) ~3250
# Olive Peak 3: 3v(C=C)? ~4700 (High)
# Olive Peak 4: 2v(C-D) ~4800? 
# Label says "3v(C=C)" pointing to ~4600 small peak.
# Label "2v(C-D)" pointing to ~4800 large peak.

y_c2d = lorentzian(wn, 1750, 50, 15) + lorentzian(wn, 2400, 50, 5) + 
        lorentzian(wn, 4600, 50, 8) + lorentzian(wn, 4800, 40, 60) + 
        lorentzian(wn, 6900, 100, 3) # 3v(C-D)

# Add noise/baseline
y_c2h += np.random.normal(0, 0.2, len(wn))
y_c2d += np.random.normal(0, 0.2, len(wn))

# --- Plotting ---
fig, ax = plt.subplots(figsize=(10, 4), dpi=150)

# Main Plot
ax.plot(wn, y_c2h, color='#113366', lw=1.5, label='C$_2$H')
ax.plot(wn, y_c2d, color='#888844', lw=1.5, label='C$_2$D')
ax.scatter(wn[::20], y_c2h[::20], color='#446699', s=10, alpha=0.5)
ax.scatter(wn[::20], y_c2d[::20], color='#AAAA66', s=10, alpha=0.5)

# Labels
ax.text(1850, 85, r'$
u$(C=C)', color='#113366', ha='center', fontweight='bold')
ax.text(3250, 25, r'$
u$(C-H)', color='#113366', ha='center', fontweight='bold')
ax.text(4800, 65, r'2$
u$(C-D)', color='#888844', ha='center', fontweight='bold')

# Styling
ax.set_xlabel(r'Wavenumber (cm$^{-1}$)', fontsize=14)
ax.set_ylabel('Normalized Rate
(events / M pulses)', fontsize=12)
ax.set_xlim(1500, 8000)
ax.set_ylim(0, 100)

# Legend
ax.legend(frameon=True, loc='upper center', bbox_to_anchor=(0.5, 0.9))

# Insets (Placeholders)
# Left Inset (2000-3000)
ax_ins1 = ax.inset_axes([0.2, 0.5, 0.25, 0.4])
ax_ins1.plot(wn, y_c2h, color='#113366')
ax_ins1.plot(wn, y_c2d, color='#888844')
ax_ins1.set_xlim(1800, 3200)
ax_ins1.set_ylim(0, 5)
ax_ins1.set_xticks([2000, 2500, 3000])

# Right Inset (6000-7500)
ax_ins2 = ax.inset_axes([0.65, 0.5, 0.25, 0.4])
ax_ins2.plot(wn, y_c2h, color='#113366')
ax_ins2.plot(wn, y_c2d, color='#888844')
ax_ins2.set_xlim(6000, 7800)
ax_ins2.set_ylim(0, 10)

plt.tight_layout()
plt.show()
