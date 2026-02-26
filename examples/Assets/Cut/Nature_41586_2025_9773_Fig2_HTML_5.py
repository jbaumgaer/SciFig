import matplotlib.pyplot as plt
import numpy as np

# --- Data Simulation ---
# Bar Chart
vals = [103, 73]
labels = ['Control', 'Dipolar
passivation']
colors = ['#77AADD', '#115599']

# --- Plotting ---
fig, ax = plt.subplots(figsize=(3, 5), dpi=150)

bars = ax.bar([0, 1], vals, color=colors, width=0.5)

# Value Labels
ax.text(0, 105, '103 mV', ha='center', fontsize=12)
ax.text(1, 75, '73 mV', ha='center', fontsize=12)

# Styling
ax.set_ylabel(r'$V_{m oc,rad} - V_{m oc}$ (mV)', fontsize=14)
ax.set_xticks([0, 1])
ax.set_xticklabels(labels, fontsize=12)
ax.set_ylim(0, 120)

# Ticks
ax.tick_params(direction='in', top=False, right=False)

plt.tight_layout()
plt.show()
