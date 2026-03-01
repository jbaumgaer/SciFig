import matplotlib.pyplot as plt
import numpy as np

fig, (ax1, ax2) = plt.subplots(1, 2, figsize=(10, 4), dpi=150)

# --- Left Panel: Density n vs x ---
x = np.linspace(0, 10, 500)
# Overlapping waves
y1 = 0.5 * (np.sin(2 * x) + 1) * np.exp(-0.05 * (x - 5)**2)
y2 = 0.5 * (np.sin(2 * x + 1.5) + 1) * np.exp(-0.05 * (x - 5)**2)
# Envelope/Total
y_total = np.maximum(y1, y2)

ax1.fill_between(x, y1, color='indigo', alpha=0.4)
ax1.fill_between(x, y2, color='indigo', alpha=0.4)
ax1.plot(x, y1, color='indigo', lw=2, alpha=0.6)
ax1.plot(x, y2, color='indigo', lw=2, alpha=0.6)

# Annotation 'd'
ax1.annotate('', xy=(3.8, 0.8), xytext=(5.5, 0.8), arrowprops=dict(arrowstyle='<->', lw=2))
ax1.text(4.65, 0.85, '$d$', ha='center', fontsize=14)

# Styling
ax1.set_xlabel('$x$', fontsize=14)
ax1.set_ylabel('Density $n$', fontsize=14)
ax1.set_xticks([])
ax1.set_yticks([])
# Thick axes
for spine in ax1.spines.values():
    spine.set_linewidth(2)
ax1.spines['top'].set_visible(False)
ax1.spines['right'].set_visible(False)

# --- Right Panel: Energy E vs hk ---
k = np.linspace(-2, 2, 200)
# Double well potential
E = 0.5 * (k**2 - 1.5)**2

ax2.plot(k, E, color='indigo', lw=3)

# Discrete levels (dots) in the wells
k_points_left = np.linspace(-1.5, -0.8, 4)
k_points_right = np.linspace(0.8, 1.5, 4)
E_points_left = 0.5 * (k_points_left**2 - 1.5)**2 + 0.1
E_points_right = 0.5 * (k_points_right**2 - 1.5)**2 + 0.1

ax2.scatter(k_points_left, E_points_left, s=100, color='rebeccapurple', alpha=0.6, zorder=5)
ax2.scatter(k_points_right, E_points_right, s=100, color='rebeccapurple', alpha=0.6, zorder=5)

# Fading dots
ax2.scatter([-1.7], [0.8], s=100, color='rebeccapurple', alpha=0.2)
ax2.scatter([1.7], [0.8], s=100, color='rebeccapurple', alpha=0.2)


# Annotation scaling
ax2.annotate('', xy=(-0.5, 1.5), xytext=(0.5, 1.5), arrowprops=dict(arrowstyle='<->', lw=2))
ax2.text(0, 0.5, r'$\propto 1/d$', ha='center', fontsize=14)

# Styling
ax2.set_xlabel(r'$\hbar k$', fontsize=14)
ax2.set_ylabel('Energy $E$', fontsize=14)
ax2.set_xticks([])
ax2.set_yticks([])
for spine in ax2.spines.values():
    spine.set_linewidth(2)
ax2.spines['top'].set_visible(False)
ax2.spines['right'].set_visible(False)

plt.tight_layout()
plt.show()
