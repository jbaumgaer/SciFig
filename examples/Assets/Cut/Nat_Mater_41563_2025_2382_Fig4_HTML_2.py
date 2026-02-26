import matplotlib.pyplot as plt
import numpy as np

# --- Data Simulation ---
# Time axes
t1 = np.linspace(0, 20, 100)
t2 = np.linspace(0, 250, 100)
t3 = np.linspace(0, 50, 100)

def decay(t, T1):
    return np.exp(-t/T1)

# 1. -SiO2 (Fast)
y1_fit = decay(t1, 3.91)
y1_data = y1_fit + np.random.normal(0, 0.08, len(t1))

# 2. -alkene(H) (Slow)
y2_fit = decay(t2, 86.05)
y2_data = y2_fit + np.random.normal(0, 0.08, len(t2))

# 3. -alkene(H)-Gd (Fast)
y3_fit = decay(t3, 7.74)
y3_data = y3_fit + np.random.normal(0, 0.08, len(t3))

# --- Plotting ---
fig, axes = plt.subplots(1, 3, figsize=(9, 4), dpi=150, sharey=True)
plt.subplots_adjust(wspace=0.1)

# Plot 1
axes[0].plot(t1, y1_data, color='lightgray', lw=1.5)
axes[0].plot(t1, y1_fit, color='gray', lw=3)
axes[0].text(15, 0.8, '-SiO$_2$:
$T_1 = 3.91$ $\mu$s', ha='right', fontsize=12)

# Plot 2
axes[1].plot(t2, y2_data, color='#BBDDFF', lw=1.5)
axes[1].plot(t2, y2_fit, color='#336699', lw=3)
axes[1].text(180, 0.8, '-alkene(H):
$T_1 = 86.05$ $\mu$s', ha='right', color='#004488', fontsize=12)

# Plot 3
axes[2].plot(t3, y3_data, color='#FFCCCC', lw=1.5)
axes[2].plot(t3, y3_fit, color='#CC3333', lw=3)
axes[2].text(40, 0.8, '-alkene(H)-Gd:
$T_1 = 7.74$ $\mu$s', ha='right', color='#990000', fontsize=12)

# Styling
axes[0].set_ylabel('Intensity (a.u.)', fontsize=14)
axes[1].set_xlabel(r'Time, $	au$ ($\mu$s)', fontsize=14)

for ax in axes:
    ax.tick_params(direction='in', top=True, right=True)
    ax.set_ylim(-0.1, 1.1)

plt.show()
