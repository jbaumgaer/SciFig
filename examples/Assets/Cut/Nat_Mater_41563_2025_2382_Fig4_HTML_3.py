import matplotlib.pyplot as plt
import numpy as np

# --- Data Simulation ---
# Time
t1 = np.linspace(0, 2.0, 300)
t2 = np.linspace(0, 1.1, 300)

def osc_decay(t, T2, freq):
    # Oscillating decay
    return 0.975 + 0.025 * np.exp(-t/T2) * np.cos(2*np.pi*freq*t)

# 1. -alkene(H) (Blue)
y1_fit = 0.975 + 0.025 * np.exp(-(t1/1.0)**2) * np.cos(2*np.pi*4*t1) # Gaussian decay envelope looks better
y1_data = y1_fit + np.random.normal(0, 0.002, len(t1))

# 2. -C7F16 (Red)
y2_fit = 0.975 + 0.025 * np.exp(-(t2/0.84)**2) * np.cos(2*np.pi*5*t2)
y2_data = y2_fit + np.random.normal(0, 0.002, len(t2))

# --- Plotting ---
fig, (ax1, ax2) = plt.subplots(1, 2, figsize=(8, 4), dpi=150, sharey=True)
plt.subplots_adjust(wspace=0.1)

# Left (Blue)
ax1.plot(t1, y1_data, color='#BBDDFF', lw=1.5)
ax1.plot(t1, y1_fit, color='#336699', lw=3)
ax1.text(1.8, 0.99, '-alkene(H):
$T_2^* = 1.00$ $\mu$s', ha='right', color='#004488', fontsize=12)

# Right (Red)
ax2.plot(t2, y2_data, color='#FFCCCC', lw=1.5)
ax2.plot(t2, y2_fit, color='#CC3333', lw=3)
ax2.text(1.0, 0.99, '-C$_7$F$_{16}$:
$T_2^* = 0.84$ $\mu$s', ha='right', color='#990000', fontsize=12)

# Styling
ax1.set_ylabel('Intensity (a.u.)', fontsize=14)
fig.text(0.5, 0.02, r'Free precession time, $	au$ ($\mu$s)', ha='center', fontsize=14)

for ax in [ax1, ax2]:
    ax.tick_params(direction='in', top=True, right=True)
    ax.set_ylim(0.94, 1.01)

plt.show()
