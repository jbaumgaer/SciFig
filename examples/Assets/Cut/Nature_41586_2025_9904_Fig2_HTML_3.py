import matplotlib.pyplot as plt
import numpy as np

# --- Data Simulation ---
# Groups
labels = ['Exciplex-free
cohost', 'Single host', 'ExciPh']
x = np.arange(len(labels))
width = 0.3

# Values
# Without PU (Blue)
v_wo = [75, 82, 80]
# With PU (Green)
v_w = [68, 65, 82]

# --- Plotting ---
fig, ax = plt.subplots(figsize=(5, 5), dpi=150)

c_wo = '#224466'
c_w = '#116633'

rects1 = ax.bar(x - width/2, v_wo, width, label='Without PU', color=c_wo, edgecolor='black')
rects2 = ax.bar(x + width/2, v_w, width, label='With PU', color=c_w, edgecolor='black')

# Annotations (Dashed lines and Text)
# 1. Exciplex-free
ax.plot([x[0]-width/2, x[0]+width/2], [75, 75], 'k--', lw=1, color='gray')
ax.plot([x[0]-width/2, x[0]+width/2], [68, 68], 'k--', lw=1, color='gray')
ax.text(x[0], 76, '$-$7%', ha='center', va='bottom', fontsize=12)

# 2. Single host
ax.plot([x[1]-width/2, x[1]+width/2], [82, 82], 'k--', lw=1, color='gray')
ax.plot([x[1]-width/2, x[1]+width/2], [65, 65], 'k--', lw=1, color='gray')
ax.text(x[1], 70, '$-$16.8%', ha='center', va='bottom', fontsize=12)

# 3. ExciPh
ax.plot([x[2]-width/2, x[2]+width/2], [80, 80], 'k--', lw=1, color='gray')
ax.plot([x[2]-width/2, x[2]+width/2], [82, 82], 'k--', lw=1, color='gray')
ax.text(x[2], 83, '+2.2%', ha='center', va='bottom', fontsize=12)
# Star
ax.scatter(x[2]+width/2, 92, marker='*', s=300, color='#116633')

# Styling
ax.set_ylabel('PLQY (%)', fontsize=14)
ax.set_xticks(x)
ax.set_xticklabels(labels, rotation=30, ha='right', fontsize=12)
ax.set_ylim(0, 100)

# Legend
ax.legend(frameon=False, loc='upper right', ncol=2, fontsize=10)

# Ticks
ax.minorticks_on()
ax.tick_params(direction='out', top=False, right=False)
ax.spines['top'].set_visible(False)
ax.spines['right'].set_visible(False)

plt.tight_layout()
plt.show()
