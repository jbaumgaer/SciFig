import matplotlib.pyplot as plt
import numpy as np

# --- Data Simulation ---
vals = [37, 10, 26, 1]
labels = ['$V_{m oc}$', 'Bulk', 'HTL', 'ETL']
colors = ['lightgray', '#BBDDFF', '#66AADD', '#1166AA']

# --- Plotting ---
fig, ax = plt.subplots(figsize=(4, 3), dpi=150)

# Bar Chart
bars = ax.bar(range(len(vals)), vals, color=colors, width=0.5)

# Value Labels
for bar, val in zip(bars, vals):
    ax.text(bar.get_x() + bar.get_width()/2, val + 2, f'{val} meV', ha='center', fontsize=11)

# Styling
ax.set_ylabel(r'QFLS, $q\Delta V_{m oc}$' + '
increasement (meV)', fontsize=12)
ax.set_xticks(range(len(vals)))
ax.set_xticklabels(labels, fontsize=12)
ax.set_ylim(0, 50)

# Text "From QFLS"
ax.text(3.8, 25, 'From
QFLS', fontsize=12, va='center')

# Ticks
ax.tick_params(direction='in', top=False, right=False)

plt.tight_layout()
plt.show()
