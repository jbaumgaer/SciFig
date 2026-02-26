import matplotlib.pyplot as plt
import numpy as np

# --- Data Simulation ---
# K-path indices
k_nodes = [0, 1, 2, 3, 4, 5, 6, 7, 8, 9, 10, 11]
k_labels = ['$\Gamma$', '$\Delta$', 'X', 'Z', 'M', '$\Sigma$', '$\Gamma$', '$\Lambda$', 'R', 'S', 'X', 'S']
# Wait, labels continue... let's simplify to a standard path
# Gamma -> X -> M -> Gamma -> R -> X -> M ...
x = np.linspace(0, 12, 600)

# Conduction Band (Top)
# Minimum at Gamma (0) or R?
# Inset cube shows R is corner.
# Image shows Bandgap at R point.
# Valance band Max at R. Conduction band Min at R.
# Direct gap at R.

def band_structure(x, offset, amp, phase):
    return offset + amp * np.cos(x * np.pi + phase)

# Valence Bands (Below 0)
vb1 = band_structure(x, -2, 1.0, 0)
vb2 = band_structure(x, -2.5, 0.5, np.pi/2)
vb3 = band_structure(x, -3, 0.8, np.pi)
# Make R point (index ~8) the Max
# Let's construct piecewise or just a complex sum
# R is at x=8
# VB max at x=8, E=0
vb_main = -2 + 2 * np.cos( (x - 8)/2 * np.pi ) 
vb_main = -1 * np.abs(vb_main) # Roughly peaks at 8, 4, 0?
# Let's visually approximation
vb_main = -4 + 4 * np.exp(-0.5*(x-8)**2) + 2 * np.exp(-0.5*(x-0)**2) + 2 * np.exp(-0.5*(x-4)**2) 
# Clip
vb_main = np.minimum(0, vb_main)

# Conduction Bands (Above 0)
cb_main = 4 - 2 * np.exp(-0.5*(x-8)**2) - 1 * np.exp(-0.5*(x-0)**2)
# Clip
cb_main = np.maximum(2.2, cb_main)

# Shading (Bandgap)
# Fill between VB Max and CB Min
# Actually the grey area is the gap.
# Fill between -2 and 8? No, the grey area is between the valence and conduction bands.

# --- Plotting ---
fig, ax = plt.subplots(figsize=(8, 5), dpi=150)

# Plot Bands (Red lines)
# Multiple bands
for i in range(3):
    noise = np.sin(x * (i+2)) * 0.2
    ax.plot(x, cb_main + 1 + i*1.5 + noise, color='#AA3333', lw=1)
    ax.plot(x, vb_main - 0.5 - i*0.5 + noise, color='#AA3333', lw=1)

# Main gap edges
ax.plot(x, cb_main, color='#AA3333', lw=2)
ax.plot(x, vb_main, color='#AA3333', lw=2)

# Fill Gap
ax.fill_between(x, vb_main, cb_main, color='#EEEEEE', alpha=1.0)

# Vertical Lines
for k in k_nodes:
    ax.axvline(k, color='black', lw=0.5)

# Labels
ax.set_xticks(k_nodes)
ax.set_xticklabels(k_labels)
ax.set_ylabel('Energy (eV)', fontsize=14)
ax.set_xlabel('Position in the Brillouin zone', fontsize=14)
ax.set_xlim(0, 11)
ax.set_ylim(-3, 8)

# Annotations
ax.text(8.2, 1.1, 'Bandgap', fontsize=14, va='center')
ax.annotate('', xy=(8, 2.2), xytext=(8, 0), arrowprops=dict(arrowstyle='|-|', lw=2))
ax.text(8.2, 2.3, 'R$_6^-$', fontsize=12)
ax.text(8.2, -0.1, 'R$_6^+$', fontsize=12)

# Inset Cube (Simplified)
# ... using mplot3d inset is hard to align perfectly.
# I'll skip the cube inset for code brevity or use a placeholder box.
ax_ins = ax.inset_axes([0.3, 0.3, 0.25, 0.35])
ax_ins.text(0.5, 0.5, '[Brillouin Zone
Schematic]', ha='center')
ax_ins.set_xticks([])
ax_ins.set_yticks([])

plt.tight_layout()
plt.show()
