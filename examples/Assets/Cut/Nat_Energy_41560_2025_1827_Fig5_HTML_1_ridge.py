import matplotlib.pyplot as plt
import numpy as np
from matplotlib.collections import LineCollection
from matplotlib.colors import ListedColormap, BoundaryNorm

# --- Data Simulation (Same as before) ---
steps = np.linspace(0, 100, 200) # Slightly lower res for performance
two_theta = np.linspace(18.4, 20.1, 300) 
TT, S = np.meshgrid(two_theta, steps)

def ridge_path(s):
    center = np.ones_like(s) * 18.9
    mask_low = s < 50
    center[mask_low] = 18.9 - 0.25 * np.sin(np.pi * s[mask_low] / 50)
    mask_high = s >= 50
    center[mask_high] = 18.7 + 0.2 * np.sin(np.pi * (s[mask_high]-50) / 50)
    center2 = np.ones_like(s) * np.nan
    mask_split = (s > 35) & (s < 65)
    center2[mask_split] = 19.5 + 0.45 * np.sin(np.pi * (s[mask_split]-35)/30)
    return center, center2

def generate_z(tt, s, path1, path2, width=0.08):
    z = np.zeros_like(tt)
    z += 0.05 
    
    # Reshape paths to (N, 1) for broadcasting against (N, M)
    p1 = path1[:, np.newaxis]
    p2 = path2[:, np.newaxis]
    
    # Path 1
    z += 1.2 * np.exp(-((tt - p1)/width)**2)
    # Path 2
    mask = ~np.isnan(p2)
    # Since p2 has NaNs, we handle mask carefully
    # But np.exp works fine with NaNs (returns NaNs)
    z2 = 0.9 * np.exp(-((tt - p2)/width)**2)
    z += np.nan_to_num(z2)
    
    z = np.clip(z, 0, 1.2)
    return z

p1_sc, p2_sc = ridge_path(steps)
mask_split = (steps > 35) & (steps < 65)
p2_sc[mask_split] = 19.5 + 0.5 * np.sin(np.pi * (steps[mask_split]-35)/30) 
Z_sc = generate_z(TT, S, p1_sc, p2_sc)

p1_ibp, p2_ibp = ridge_path(steps)
p2_ibp[mask_split] = 19.2 + 0.25 * np.sin(np.pi * (steps[mask_split]-35)/30)
Z_ibp = generate_z(TT, S, p1_ibp, p2_ibp)

# --- Helper: Multicolored Line ---
def plot_colored_line(ax, x, y, c, cmap='bwr', lw=1.5, zorder=1):
    # Create a set of line segments so that we can color them individually
    # This creates the points as a N x 1 x 2 array so that we can stack points
    # together easily to get the segments. The segments array for line collection
    # needs to be (numlines) x (points per line) x 2 (for x and y)
    points = np.array([x, y]).T.reshape(-1, 1, 2)
    segments = np.concatenate([points[:-1], points[1:]], axis=1)

    # Create a continuous norm to map from data points to colors
    norm = plt.Normalize(0.0, 1.0) # Z is 0-1.2, but we want Blue at 0.0, Red at 1.0
    lc = LineCollection(segments, cmap=cmap, norm=norm, zorder=zorder)
    
    # Set the values used for colormapping
    lc.set_array(c)
    lc.set_linewidth(lw)
    line = ax.add_collection(lc)
    return line

# --- Plotting ---
fig, axes = plt.subplots(1, 2, figsize=(10, 8), dpi=150, sharey=True)

# Define Scale for Z height
# We want peaks to overlap significantly
# Step spacing is 100/200 = 0.5 units per step.
# Z max is 1.2.
# If scale is 10, Z_visual max is 12.
# This covers ~24 steps. Good overlap.
z_scale = 15

# Iterate Back to Front (Top to Bottom)
# steps are 0..100.
# We want "Top" (100) to be in Back. "Bottom" (0) in Front.
# Standard plot: Back is drawn first.
# So iterate i from len(steps)-1 down to 0.

def plot_ridge(ax, Z_data, title, split_text):
    # Set Background Color of Axis to Blue-ish?
    # No, the figure has Blue background.
    # We can set ax.set_facecolor('#445577')?
    # But bwr colormap has Blue at 0.
    # If we fill with White, we hide the blue background.
    # Let's fill with the *Background Color* of the plot, which should be the "Low Z" color.
    # bwr(0) is Blue.
    bg_color = plt.cm.bwr(0.0) 
    ax.set_facecolor(bg_color)
    
    # Loop
    for i in range(len(steps)-1, -1, -1):
        y_base = steps[i]
        z_row = Z_data[i, :]
        y_curve = y_base + z_row * z_scale
        
        # 1. Fill to hide behind
        # We fill from y_curve down to... y_base?
        # If we fill down to y_base, we hide the line *at* y_base from the previous iteration?
        # No, previous iteration (Back) is already drawn.
        # We are drawing Front on top of Back.
        # So we hide what is *behind* this current curve.
        # Filling with 'white' makes it look like snowy mountains.
        # Filling with 'bg_color' makes it look like the mountain rises from the sea.
        # But if we fill with bg_color, we hide the *peaks* behind us. Correct.
        ax.fill_between(two_theta, y_base, y_curve, facecolor=bg_color, zorder=i)
        
        # 2. Draw the Line with Gradient
        # But plot_colored_line is slow if called 200 times.
        # Let's try simple plot first? No, we need gradient.
        # Optimize: downsample?
        plot_colored_line(ax, two_theta, y_curve, z_row, zorder=i+0.1, lw=1.5)

    ax.set_ylim(0, 100 + 1.2 * z_scale)
    ax.set_xlim(18.4, 20.1)
    ax.set_xlabel(r'2$	heta$ (degree)', fontsize=12)
    
    # Remove ticks/spines for cleaner look
    ax.spines['top'].set_visible(False)
    ax.spines['right'].set_visible(False)
    ax.spines['left'].set_visible(False)
    ax.get_yaxis().set_ticks([])
    
    # Title
    ax.text(19.9, 10, title, color='white', ha='right', fontsize=12, fontweight='bold', transform=ax.transData)
    ax.text(19.9, 105, '(003)', color='black', ha='right', fontsize=12, transform=ax.transData)
    
    # Annotations
    y_mark = 50 + 0.6 * z_scale # Approx height of peak at step 50
    x1 = 18.7
    x2 = 19.9 if 'SC92' in title else 19.41
    
    # We need to project the Z-shift into Y?
    # The dashed lines in the figure are vertical (constant Theta).
    ax.vlines(x1, 35 + 0.6*z_scale, 65 + 0.6*z_scale, colors='k', linestyles='--', alpha=0.5)
    ax.vlines(x2, 35 + 0.6*z_scale, 65 + 0.6*z_scale, colors='k', linestyles='--', alpha=0.5)
    
    ax.text((x1+x2)/2, y_mark + 5, split_text, ha='center', fontsize=9)
    ax.annotate('', xy=(x1, y_mark), xytext=(x2, y_mark), arrowprops=dict(arrowstyle='<->', color='black'))


plot_ridge(axes[0], Z_sc, 'SC92', '1.28°')
plot_ridge(axes[1], Z_ibp, 'IBP-SC92', '0.71°')

# Guide Arrows (2D)
ax_guide = fig.add_axes([0.02, 0.2, 0.1, 0.6]) 
ax_guide.axis('off')
ax_guide.set_ylim(0, 100)
ax_guide.arrow(0.5, 10, 0, 35, width=0.15, head_width=0.4, color='#7799BB', length_includes_head=True)
ax_guide.text(0.2, 27, 'Charging', rotation=90, va='center', ha='center', fontsize=11)
ax_guide.arrow(0.5, 60, 0, 35, width=0.15, head_width=0.4, color='#7799BB', length_includes_head=True)
ax_guide.text(0.2, 77, 'Discharging', rotation=90, va='center', ha='center', fontsize=11)

plt.tight_layout()
plt.savefig('Nat_Energy_41560_2025_1827_Fig5_HTML_1_ridge.png', dpi=150)
