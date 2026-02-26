import matplotlib.pyplot as plt
import numpy as np

# --- Data Simulation ---
# 3 Groups: 3A, 9A, 15A
labels = ['3 A', '9 A', '15 A']
sc92_vals = [28, 38, 55] # Pink
ibp_vals = [27, 34, 43] # Grey

x = np.arange(len(labels))
width = 0.3

# --- Plotting ---
fig, (ax1, ax2) = plt.subplots(2, 1, figsize=(5, 4), dpi=150, sharex=True, gridspec_kw={'height_ratios': [1, 3]})
plt.subplots_adjust(hspace=0.05)

# Colors
col_sc = '#F4B6B0' # Light Pink
col_ibp = '#AAB2BC' # Grey Blue

# Plot on both axes
for ax in [ax1, ax2]:
    ax.bar(x - width/2, sc92_vals, width, color=col_sc, label='SC92')
    ax.bar(x + width/2, ibp_vals, width, color=col_ibp, label='IBP-SC92')

# Break Y Axis
# Top limits
ax1.set_ylim(50, 70) # Show top part? No, max is 55. 
# Image shows scale 0-60 roughly, but with break.
# Let's assume break is between 10 and 25?
# The image shows axis starting at 0, then break, then 30, 50.
ax2.set_ylim(0, 20) # Bottom part
ax1.set_ylim(25, 60) # Top part

# Hide spines between
ax1.spines['bottom'].set_visible(False)
ax2.spines['top'].set_visible(False)
ax1.tick_params(bottom=False)
ax2.tick_params(top=False)

# Diagonals for break
d = .015 
kwargs = dict(transform=ax1.transAxes, color='k', clip_on=False)
ax1.plot((-d, +d), (-d, +d), **kwargs)        # top-left diagonal
# ax1.plot((1 - d, 1 + d), (-d, +d), **kwargs)  # top-right diagonal

kwargs.update(transform=ax2.transAxes)  # switch to the bottom axes
ax2.plot((-d, +d), (1 - d, 1 + d), **kwargs)  # bottom-left diagonal
# ax2.plot((1 - d, 1 + d), (1 - d, 1 + d), **kwargs)  # bottom-right diagonal

# Legend (Top only)
ax1.legend(loc='upper center', ncol=2, frameon=False, fontsize=12)
ax1.set_title('3 A', fontsize=12) # Title at top? Image says "3 A" at top but that's X label?
# Wait, X labels are 3 A, 9 A, 15 A. Title is likely something else or repeated.

# Labels
ax2.set_xticks(x)
ax2.set_xticklabels(labels, fontsize=14)
ax2.set_yticks([0])
ax1.set_yticks([30, 50])

# White grid lines (Horizontal)
ax1.yaxis.grid(True, color='white', linestyle='-', linewidth=1.5)
ax2.yaxis.grid(True, color='white', linestyle='-', linewidth=1.5)

# Background color (Peach/Beige)
fig.patch.set_facecolor('#FFF5EE')
ax1.set_facecolor('#FFF5EE')
ax2.set_facecolor('#FFF5EE')

plt.show()
