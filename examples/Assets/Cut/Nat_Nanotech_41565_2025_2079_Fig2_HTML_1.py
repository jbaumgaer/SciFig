import matplotlib.gridspec as gridspec
import matplotlib.pyplot as plt
import numpy as np

# --- Data Simulation ---
# Y-axis: Data sequence (time/state)
steps = np.linspace(0, 100, 200)

# Heatmap 1: Q ~ 1.3 - 1.4 ((003) reflection)
q1 = np.linspace(1.2, 1.5, 100)
# Peak center shifts like a Z-shape or sine wave
# Starts at 1.32, moves to 1.38, back to 1.32
center_shift_1 = 1.32 + 0.06 * np.exp(-((steps - 50)/20)**2)
# Add splitting behavior
X1, Y_steps = np.meshgrid(q1, steps)
Z1 = np.zeros_like(X1)
for i, y in enumerate(steps):
    mu = center_shift_1[i]
    # Simulate peak profile
    profile = np.exp(-((q1 - mu)/0.015)**2)
    Z1[i, :] = profile

# Heatmap 2: Q ~ 2.6 - 2.8 ((101), (006)/(102))
q2 = np.linspace(2.55, 2.8, 100)
X2, _ = np.meshgrid(q2, steps)
Z2 = np.zeros_like(X2)
# Static peak at 2.68 (Al or inactive phase?)
Z2 += 0.8 * np.exp(-((X2 - 2.68)/0.008)**2)
# Moving peak (weaker)
center_shift_2 = 2.60 + 0.02 * np.exp(-((steps - 50)/20)**2)
Z2 += 0.5 * np.exp(-((X2 - center_shift_2)/0.02)**2)


# Waterfall Profiles (Right Panel)
voltages = ['OCP', 'C, 4.1 V', 'C, 4.2 V', 'C, 4.4 V', 'C, 4.5 V', 'D, 4.1 V', 'D, 3.8 V', 'D, 2.7 V']
colors_wf = ['salmon', 'wheat', 'wheat', 'skyblue', 'skyblue', 'wheat', 'wheat', 'salmon']
profiles = []
# Create dummy peaks for waterfall
x_wf = np.linspace(0, 1, 100)
for i in range(len(voltages)):
    pos = 0.3 + 0.4 * (i / len(voltages)) # Shift position
    if i == 4: pos = 0.6 # Jump
    prof = np.exp(-((x_wf - pos)/0.05)**2)
    profiles.append(prof)


# --- Plotting ---
fig = plt.figure(figsize=(10, 6), dpi=150)
gs = gridspec.GridSpec(1, 3, width_ratios=[1, 1.2, 0.8], wspace=0.1)

# Panel 1: (003)
ax1 = fig.add_subplot(gs[0])
ax1.imshow(Z1, aspect='auto', extent=[1.2, 1.5, 0, 100], cmap='RdBu_r', vmin=-0.2, vmax=1.2)
ax1.set_xlabel(r'Q ($\AA^{-1}$)', fontsize=12)
ax1.set_ylabel('Data sequence', fontsize=12)
ax1.set_yticks([])
# Annotations
ax1.arrow(1.25, 10, 0, 30, color='white', linestyle='--', width=0.002, head_width=0.01)
ax1.text(1.22, 25, 'Charging', rotation=90, color='white', ha='center')
ax1.arrow(1.25, 90, 0, -30, color='white', linestyle='--', width=0.002, head_width=0.01)
ax1.text(1.22, 75, 'Discharging', rotation=90, color='white', ha='center')
ax1.text(1.32, 102, '(003)', ha='center', fontsize=10)
ax1.axhline(50, color='gray', linestyle='--')
# 5.9% Arrow
ax1.annotate('', xy=(1.32, 40), xytext=(1.40, 40), arrowprops=dict(arrowstyle='<->', color='gray'))
ax1.text(1.36, 35, '5.9%', color='gray', ha='center', fontsize=9)


# Panel 2: (101) etc
ax2 = fig.add_subplot(gs[1])
ax2.imshow(Z2, aspect='auto', extent=[2.55, 2.8, 0, 100], cmap='RdBu_r', vmin=-0.2, vmax=1.2)
ax2.set_xlabel(r'Q ($\AA^{-1}$)', fontsize=12)
ax2.set_yticks([])
ax2.axhline(50, color='white', lw=2) # Split line
ax2.text(2.68, 102, '(006)/(102)', ha='center', fontsize=10)
ax2.text(2.60, 102, '(101)', ha='center', fontsize=10)

# Panel 3: Waterfall
ax3 = fig.add_subplot(gs[2])
ax3.axis('off')
y_base = 0
for i, (prof, col, lbl) in enumerate(zip(profiles, colors_wf, voltages)):
    y_offset = i * 1.5
    ax3.fill_between(x_wf, y_offset, y_offset + prof, color=col, alpha=0.8)
    ax3.plot(x_wf, y_offset + prof, color='goldenrod', lw=0.5)
    ax3.text(1.05, y_offset + 0.2, lbl, fontsize=10)

plt.tight_layout()
plt.show()
