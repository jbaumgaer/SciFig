import matplotlib.pyplot as plt
import numpy as np

# --- Data Simulation ---
# K-path indices
k_nodes = [0, 1, 2, 3, 4, 5, 6, 7, 8, 9, 10, 11]
k_labels = [r'$\Gamma$', r'$\Delta$', 'X', 'Z', 'M', r'$\Sigma$', r'$\Gamma$', r'$\Lambda$', 'R', 'S', 'X', 'S', 'R', 'T', 'M']
# Need more nodes
x = np.linspace(0, 14, 700)

def band_structure(x, offset, amp, phase):
    return offset + amp * np.cos(x * np.pi + phase)

# Valence Bands (Below 0)
# Maximum at R (index 8)
# R is at x=8
vb_main = -3 + 3 * np.exp(-0.5*(x-8)**2) # Peak at 0 at R
# Add X peak (index 2)
vb_main += 1 * np.exp(-0.5*(x-2)**2) - 2
# Add M peak (index 4)
vb_main += 2 * np.exp(-0.5*(x-4)**2) - 2
# Add Gamma peak (index 0, 6)
vb_main -= 1 * np.exp(-0.5*(x-6)**2)
vb_main = np.clip(vb_main, -3, 0)

# Conduction Bands (Above 0)
# Minimum at R (index 8) ~3eV
cb_main = 6 - 3 * np.exp(-0.5*(x-8)**2) # Min at 3
# Max at Gamma
cb_main += 1 * np.exp(-0.5*(x-6)**2)
# Dip at M
cb_main -= 1 * np.exp(-0.5*(x-4)**2)
cb_main = np.clip(cb_main, 3, 7)

# --- Plotting ---
fig, ax = plt.subplots(figsize=(8, 5), dpi=150)

# Fill Gap
ax.fill_between(x, vb_main, cb_main, color='#EEEEEE', alpha=1.0)

# Plot Bands (Red lines)
# Bold lines
ax.plot(x, cb_main, color='#AA3333', lw=2)
ax.plot(x, vb_main, color='#AA3333', lw=2)

# Thin lines
for i in range(1, 4):
    ax.plot(x, cb_main + i*0.8, color='#AA3333', lw=0.8, alpha=0.7)
    ax.plot(x, vb_main - i*0.8, color='#AA3333', lw=0.8, alpha=0.7)

# Vertical Lines
ticks = [0, 1, 2, 3, 4, 5, 6, 7, 8, 9, 10, 11, 12, 13, 14]
for k in ticks:
    ax.axvline(k, color='black', lw=0.5)

# Labels
ax.set_xticks(ticks)
ax.set_xticklabels([r'$\Gamma$', r'$\Delta$', 'X', 'Z', 'M', r'$\Sigma$', r'$\Gamma$', r'$\Lambda$', 'R', 'S', 'X', 'S', 'R', 'T', 'M'])
ax.set_ylabel('Energy (eV)', fontsize=14)
ax.set_xlim(0, 14)
ax.set_ylim(-3.5, 8)

# Title
ax.set_title('Cubic Perovskite CsPbCl$_3$', fontsize=12)

plt.tight_layout()
plt.show()
