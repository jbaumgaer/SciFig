import matplotlib.pyplot as plt
import numpy as np
from matplotlib.colors import LightSource

# --- Data Simulation ---
# Y-axis: State of Charge (Steps)
steps = np.linspace(0, 100, 200)
# X-axis: 2 Theta
two_theta = np.linspace(18.4, 20.1, 200)
TT, S = np.meshgrid(two_theta, steps)

# Function to generate the ridge path
def ridge_path(s, split_point=50, shift_mag=1.0):
    # s is 0 to 100
    # 0 -> 50: Charging (Shift right then abrupt left?)
    # Based on image:
    # Starts at ~18.9
    # Shifts to ~18.7 (lower angle)
    # Then jumps to ~19.9 (high angle) at top of charge
    
    center = np.ones_like(s) * 18.9
    
    # Lower half (Charging)
    mask_low = s < 50
    # Parabolic shift left
    center[mask_low] = 18.9 - 0.2 * np.sin(np.pi * s[mask_low] / 50)
    
    # Upper half (Discharging) - Mirror?
    mask_high = s >= 50
    center[mask_high] = 18.7 + 0.2 * np.sin(np.pi * (s[mask_high]-50) / 50)
    
    # The Split/Jump part (High Voltage Phase)
    # At s ~ 40-60, there is a second peak at higher angle
    center2 = np.ones_like(s) * np.nan
    mask_split = (s > 35) & (s < 65)
    # Grows from 19.5 to 19.9 then back?
    center2[mask_split] = 19.5 + 0.4 * np.sin(np.pi * (s[mask_split]-35)/30)
    
    return center, center2

# Generate Intensity Z
def generate_z(tt, s, path1, path2, width=0.1):
    z = np.zeros_like(tt)
    # Path 1
    z += np.exp(-((tt - path1)/width)**2)
    # Path 2
    mask = ~np.isnan(path2)
    z[mask] += 0.8 * np.exp(-((tt[mask] - path2[mask])/width)**2)
    return z

# SC92 (Left) - Large Shift
p1_sc, p2_sc = ridge_path(steps, shift_mag=1.2)
# Modify p2_sc to go further right
mask_split = (steps > 35) & (steps < 65)
p2_sc[mask_split] = 19.3 + 0.6 * np.sin(np.pi * (steps[mask_split]-35)/30) # Max ~19.9

Z_sc = generate_z(TT, S, p1_sc, p2_sc)

# IBP-SC92 (Right) - Smaller Shift
p1_ibp, p2_ibp = ridge_path(steps) # Base path
# Modify p2_ibp to shift less
p2_ibp[mask_split] = 19.1 + 0.3 * np.sin(np.pi * (steps[mask_split]-35)/30) # Max ~19.4

Z_ibp = generate_z(TT, S, p1_ibp, p2_ibp)


# --- Plotting ---
fig, axes = plt.subplots(1, 2, figsize=(8, 6), dpi=150, sharey=True)

# Custom Colormap for 3D effect (Blue to White to Red)
# Or just standard RdBu_r
cmap = plt.cm.RdBu_r

# Plot SC92
axes[0].imshow(Z_sc, aspect='auto', extent=[18.4, 20.1, 0, 100], cmap=cmap, vmin=-0.5, vmax=1.5)
axes[0].text(0.95, 0.05, 'SC92', transform=axes[0].transAxes, color='white', ha='right', fontsize=12)
axes[0].text(0.95, 0.95, '(003)', transform=axes[0].transAxes, color='black', ha='right', fontsize=12)

# Annotations SC92
axes[0].plot([18.7, 18.7], [35, 65], 'k--', alpha=0.5) # Left marker
axes[0].plot([19.9, 19.9], [35, 65], 'k--', alpha=0.5) # Right marker (approx)
axes[0].annotate('', xy=(18.7, 50), xytext=(19.9, 50), arrowprops=dict(arrowstyle='<->', color='#444444'))
axes[0].text(19.3, 52, '1.28°', ha='center', fontsize=10)


# Plot IBP-SC92
axes[1].imshow(Z_ibp, aspect='auto', extent=[18.4, 20.1, 0, 100], cmap=cmap, vmin=-0.5, vmax=1.5)
axes[1].text(0.95, 0.05, 'IBP-SC92', transform=axes[1].transAxes, color='white', ha='right', fontsize=12)
axes[1].text(0.95, 0.95, '(003)', transform=axes[1].transAxes, color='black', ha='right', fontsize=12)

# Annotations IBP
axes[1].plot([18.7, 18.7], [35, 65], 'k--', alpha=0.5)
axes[1].plot([19.4, 19.4], [35, 65], 'k--', alpha=0.5)
axes[1].annotate('', xy=(18.7, 50), xytext=(19.4, 50), arrowprops=dict(arrowstyle='<->', color='#444444'))
axes[1].text(19.05, 52, '0.71°', ha='center', fontsize=10)


# Y Axis Labels (Arrows)
axes[0].set_yticks([])
# Draw arrows manually
axes[0].arrow(18.3, 10, 0, 30, clip_on=False, width=0.02, head_width=0.1, color='#7799BB')
axes[0].text(18.2, 25, 'Charging', rotation=90, ha='center', va='center')
axes[0].arrow(18.3, 60, 0, 30, clip_on=False, width=0.02, head_width=0.1, color='#7799BB')
axes[0].text(18.2, 75, 'Discharging', rotation=90, ha='center', va='center')
axes[0].text(18.2, 5, 'OCV', ha='center')
axes[0].text(18.2, 50, '4.5 V', ha='center')
axes[0].text(18.2, 95, '2.7 V', ha='center')

# X Labels
for ax in axes:
    ax.set_xlabel(r'2$	heta$ (degree)', fontsize=14)
    ax.set_xticks([18.5, 19.2, 19.9])

plt.tight_layout()
plt.show()
