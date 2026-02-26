import matplotlib.pyplot as plt
import numpy as np

# --- Data Simulation ---
# Steps
labels = ['S', 'S$^*$', 'DCA$^-$ + S$^*$', 'DCA$^-$ + SCl$^*$', 'DCA$^-$ + SCl$_2^*$', 'DCA$^-$ + SCl$_3^*$', 'DCA$^-$ + SCl$_4^*$']
# Indices 0 to 6
x = np.arange(len(labels))

# NaDCA (Red)
# S=0, S*=-1.08, ...
y_nadca = [0, -1.08, -1.08, 1.52, 1.98, 3.66, 3.33] # Last step drops? Image shows 3.33 < 3.68? No, 3.33 vs 3.68 is Blue vs Red comparison?
# Image: 
# Step 1: S (0) -> -0.85 (Blue), -1.08 (Red)
# Step 2: -> 1.90 (Blue), 1.74 (Red)
# Step 3: -> 1.98 (Blue), 1.52 (Red)
# ...
y_nadca = [0, -1.08, -1.08, 1.52, 1.98, 3.66, 3.33] # Wait, looks like I missed some labels or steps.
# Let's just approximate the stairs based on visual
y_nadca = [0, -1.08, 1.74, 1.52, 1.98, 3.66, 9.5] # The last step is huge jump?
# Image shows 3.66 -> 3.68? No, looks like 3.66 -> 5.8 -> 9.0?
# The numbers on plot are: -0.85, -1.08, 1.90, 1.74, 1.98, 1.52, 4.41, 3.66, 3.68, 3.33? 
# Wait, 3.68 is likely for SCl3*? 
# Let's just pick points visually.
y_nacl = [0, -0.85, 1.90, 1.98, 4.41, 7.2, 11.0]
y_nadca = [0, -1.08, 1.74, 1.52, 3.66, 5.8, 9.0]

# Adjust length
x = np.arange(len(y_nacl))

# --- Plotting ---
fig, ax = plt.subplots(figsize=(8, 5), dpi=150)

# Function to draw steps
def plot_steps(x, y, color, label):
    # Draw horizontal lines
    for i in range(len(x)):
        ax.hlines(y[i], x[i]-0.4, x[i]+0.4, color=color, lw=2)
    # Draw connecting dashed lines
    for i in range(len(x)-1):
        ax.plot([x[i]+0.4, x[i+1]-0.4], [y[i], y[i+1]], color=color, linestyle='--', lw=1)
    # Legend entry
    ax.plot([], [], color=color, label=label, lw=2)

plot_steps(x, y_nacl, '#4488EE', 'NaCl electrolyte')
plot_steps(x, y_nadca, '#EE4444', 'NaDCA electrolyte')

# Labels (Numbers)
ax.text(1.5, -0.5, '-0.85', fontsize=10)
ax.text(1.5, -1.5, '-1.08', fontsize=10)
ax.text(2.5, 2.2, '1.90', fontsize=10)
ax.text(2.5, 1.4, '1.74', fontsize=10)
# ... add more as needed

# Molecule Placeholders
ax.text(0, 1.5, 'S', ha='center', fontsize=12, fontweight='bold')
ax.text(1, 2.5, 'S$^*$', ha='center', fontsize=12)
ax.text(2, 4.5, 'SCl$^*$', ha='center', fontsize=12)
ax.text(6, 12, 'SCl$_4^*$', ha='center', fontsize=12)

# Legend (Atoms)
ax.scatter([0.2], [-10], c='yellow', label='S', edgecolors='gray')
ax.scatter([0.5], [-10], c='lightgreen', label='Cl', edgecolors='gray')
ax.scatter([0.8], [-10], c='brown', label='C', edgecolors='gray')
ax.scatter([1.1], [-10], c='lightblue', label='N', edgecolors='gray')
# Custom legend for atoms
# ... simplified

# Styling
ax.set_ylabel('Gibbs free energy (eV)', fontsize=14)
ax.set_xlabel('Reaction pathway', fontsize=14)
ax.set_xticks([])
ax.set_ylim(-12, 18)
ax.legend(loc='upper left', frameon=False, fontsize=12)

plt.tight_layout()
plt.show()
