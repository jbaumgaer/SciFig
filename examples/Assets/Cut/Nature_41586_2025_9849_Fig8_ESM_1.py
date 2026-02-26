import matplotlib.pyplot as plt
import numpy as np

# --- Data Simulation ---
# Groups: 5, 10, 15, 20, 25 nm
groups = [5, 10, 15, 20, 25]
colors = ['#EEDD44', '#DD8844', '#CC4466', '#882288', '#440088'] # Yellow to Purple

data = []
# Generate random data around decreasing means? Or increasing?
# 5nm: ~1.9 (Spread 1.8-2.0)
data.append(np.random.normal(1.9, 0.08, 6))
# 10nm: ~2.01
data.append(np.random.normal(2.01, 0.01, 6))
# 15nm: ~1.98
data.append(np.random.normal(1.98, 0.01, 5))
# 20nm: ~1.96
data.append(np.random.normal(1.96, 0.01, 5))
# 25nm: ~1.96
data.append(np.random.normal(1.96, 0.01, 5))

# --- Plotting ---
fig, ax = plt.subplots(figsize=(6, 5), dpi=150)

for i, (g, d, col) in enumerate(zip(groups, data, colors)):
    # Scatter points (Left of group center)
    # Jitter x
    x_scat = g - 1.5 + np.random.uniform(-0.5, 0.5, len(d))
    ax.scatter(x_scat, d, color=col, s=40, alpha=0.9, edgecolors='none')
    
    # Distribution curve (Right of group center)
    y_dist = np.linspace(min(d)-0.05, max(d)+0.05, 50)
    mu = np.mean(d)
    sig = np.std(d) + 0.01 # Avoid zero div
    x_dist = g + 0.5 + 20 * (1/(sig*np.sqrt(2*np.pi))) * np.exp(-0.5*((y_dist-mu)/sig)**2) * 0.05 # Scaling
    
    # Plot curve line
    ax.plot(x_dist, y_dist, color=col, lw=1.5)

# Styling
ax.set_xlabel('ICO:H thickness (nm)', fontsize=14)
ax.set_ylabel('Voltage (V)', fontsize=14)
ax.set_ylim(1.78, 2.06)
ax.set_xlim(2, 28)

# Ticks
ax.minorticks_on()
ax.tick_params(direction='in', top=True, right=True)

plt.tight_layout()
plt.show()
