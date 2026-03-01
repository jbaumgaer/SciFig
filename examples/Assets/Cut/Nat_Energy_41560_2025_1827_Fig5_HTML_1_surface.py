import matplotlib.pyplot as plt
import numpy as np

# --- Data Simulation ---
# Y-axis: State of Charge (Steps)
steps = np.linspace(0, 100, 300) # Higher res for smooth surface
# X-axis: 2 Theta
two_theta = np.linspace(18.4, 20.1, 300)
TT, S = np.meshgrid(two_theta, steps)

# Function to generate the ridge path
def ridge_path(s):
    center = np.ones_like(s) * 18.9

    # Lower half (Charging)
    mask_low = s < 50
    center[mask_low] = 18.9 - 0.25 * np.sin(np.pi * s[mask_low] / 50)

    # Upper half (Discharging)
    mask_high = s >= 50
    center[mask_high] = 18.7 + 0.2 * np.sin(np.pi * (s[mask_high]-50) / 50)

    # The Split/Jump part (High Voltage Phase)
    center2 = np.ones_like(s) * np.nan
    mask_split = (s > 35) & (s < 65)
    center2[mask_split] = 19.5 + 0.45 * np.sin(np.pi * (s[mask_split]-35)/30)

    return center, center2

# Generate Intensity Z
def generate_z(tt, s, path1, path2, width=0.08):
    z = np.zeros_like(tt)
    # Base background noise/blue level
    z += 0.05

    # Path 1
    z += 1.2 * np.exp(-((tt - path1)/width)**2)
    # Path 2
    mask = ~np.isnan(path2)
    z[mask] += 0.9 * np.exp(-((tt[mask] - path2[mask])/width)**2)

    # Normalize Z to 0-1 range for colormap
    z = np.clip(z, 0, 1.2)
    return z

# SC92 (Left)
p1_sc, p2_sc = ridge_path(steps)
# Make separation wider for SC92
mask_split = (steps > 35) & (steps < 65)
p2_sc[mask_split] = 19.5 + 0.5 * np.sin(np.pi * (steps[mask_split]-35)/30)
Z_sc = generate_z(TT, S, p1_sc, p2_sc)

# IBP-SC92 (Right)
p1_ibp, p2_ibp = ridge_path(steps)
# Make separation narrower
p2_ibp[mask_split] = 19.2 + 0.25 * np.sin(np.pi * (steps[mask_split]-35)/30)
Z_ibp = generate_z(TT, S, p1_ibp, p2_ibp)


# --- Plotting ---
fig = plt.figure(figsize=(12, 6), dpi=150)

# Common settings
elev = 55
azim = -90

def style_3d_ax(ax, z_data, title, split_width_text):
    # Plot Surface
    # bwr: Blue-White-Red.
    surf = ax.plot_surface(TT, S, z_data, cmap='bwr',
                           linewidth=0, antialiased=False,
                           rstride=2, cstride=2, shade=True, lightsource=None)

    # View Angle
    ax.view_init(elev=elev, azim=azim)
    ax.set_box_aspect((1, 2, 0.5)) # Stretch Y

    # Remove Panes & Grid
    ax.xaxis.pane.fill = False
    ax.yaxis.pane.fill = False
    ax.zaxis.pane.fill = False
    ax.xaxis.pane.set_edgecolor('w')
    ax.yaxis.pane.set_edgecolor('w')
    ax.zaxis.pane.set_edgecolor('w')
    ax.grid(False)

    # Hide Z axis
    ax.set_zticks([])

    # Limits
    ax.set_xlim(18.4, 20.1)
    ax.set_ylim(0, 100)

    # X Labels
    ax.set_xlabel(r'2$	heta$ (degree)', fontsize=12, labelpad=5)
    ax.set_xticks([18.5, 19.2, 19.9])

    # Y Labels (Hidden)
    ax.set_yticks([])

    # Annotations
    ax.text(19.9, 0, 0.2, title, fontsize=12, color='white', ha='right', fontweight='bold')
    ax.text(19.9, 95, 0.2, '(003)', fontsize=12, color='black', ha='right')

    # Measurement Lines
    y_pos = 50
    x1 = 18.7
    x2 = 19.9 if 'SC92' in title else 19.41

    ax.plot([x1, x1], [35, 65], [0.5, 0.5], 'k--', lw=0.8, alpha=0.6, zorder=10)
    ax.plot([x2, x2], [35, 65], [0.5, 0.5], 'k--', lw=0.8, alpha=0.6, zorder=10)
    ax.plot([x1, x2], [y_pos, y_pos], [0.5, 0.5], color='#444444', lw=1, marker='|', markersize=5)
    mid = (x1 + x2) / 2
    ax.text(mid, y_pos, 0.7, split_width_text, ha='center', fontsize=9, color='black', zorder=20)


# Subplot 1
ax1 = fig.add_subplot(1, 2, 1, projection='3d')
style_3d_ax(ax1, Z_sc, 'SC92', '1.28°')

# Subplot 2
ax2 = fig.add_subplot(1, 2, 2, projection='3d')
style_3d_ax(ax2, Z_ibp, 'IBP-SC92', '0.71°')

# 2D Guide Arrows
ax_guide = fig.add_axes([0.02, 0.2, 0.1, 0.6])
ax_guide.axis('off')
ax_guide.set_ylim(0, 100)
ax_guide.arrow(0.5, 10, 0, 35, width=0.15, head_width=0.4, color='#7799BB', length_includes_head=True)
ax_guide.text(0.2, 27, 'Charging', rotation=90, va='center', ha='center', fontsize=11)
ax_guide.arrow(0.5, 60, 0, 35, width=0.15, head_width=0.4, color='#7799BB', length_includes_head=True)
ax_guide.text(0.2, 77, 'Discharging', rotation=90, va='center', ha='center', fontsize=11)
ax_guide.text(0.8, 5, 'OCV', ha='center', fontsize=10)
ax_guide.text(0.8, 50, '4.5 V', ha='center', fontsize=10)
ax_guide.text(0.8, 95, '2.7 V', ha='center', fontsize=10)

plt.tight_layout()
plt.savefig('Nat_Energy_41560_2025_1827_Fig5_HTML_1_surface.png', dpi=150)
