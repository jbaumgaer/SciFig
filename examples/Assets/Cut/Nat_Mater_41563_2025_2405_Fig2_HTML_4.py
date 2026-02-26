import matplotlib.pyplot as plt
import numpy as np

# --- Data Simulation ---
# Energy vs Valence
# Points: (Energy, Valence)
# Ru foil: 0
# RuO2: +4
# RuCl3? No, KB@Ru etc are derived from XANES edge shift
# Linear relationship: Valence = m * Energy + c

# Define points from image
# Ru foil (0) at ~22117.5
# RuO2 (+4) at ~22130.5
# Fit line
e_ref = np.array([22117.5, 22130.5])
v_ref = np.array([0, 4])
coef = np.polyfit(e_ref, v_ref, 1)
poly = np.poly1d(coef)

# Samples
# KB@Ru: +3.63 -> find Energy
v_kbru = 3.63
e_kbru = (v_kbru - coef[1]) / coef[0]

# KB@RuP-800: +2.83
v_800 = 2.83
e_800 = (v_800 - coef[1]) / coef[0]

# KB@RuP-550: +2.77
v_550 = 2.77
e_550 = (v_550 - coef[1]) / coef[0]

# KB@RuP-300: +2.69
v_300 = 2.69
e_300 = (v_300 - coef[1]) / coef[0]

# --- Plotting ---
fig, ax = plt.subplots(figsize=(6, 5), dpi=150)

# Dotted Line
x_line = np.linspace(22117, 22131, 10)
ax.plot(x_line, poly(x_line), ':', color='gray', zorder=1)

# Markers (Inverted Triangles 'v')
ms = 14
# Ru Foil
ax.plot(e_ref[0], v_ref[0], 'v', color='#555555', markeredgecolor='black', markersize=ms, label='Ru foil')
ax.text(e_ref[0]+0.5, v_ref[0], 'Ru foil (0)', va='center', fontsize=12)

# RuO2
ax.plot(e_ref[1], v_ref[1], 'v', color='#C08070', markeredgecolor='#C08070', markersize=ms, label='RuO$_2$')
ax.text(e_ref[1]-0.5, v_ref[1]+0.2, 'RuO$_2$ (+4)', ha='right', color='#A06050', fontsize=12)

# KB@Ru
ax.plot(e_kbru, v_kbru, 'v', color='#4682B4', markeredgecolor='#4682B4', markersize=ms)
ax.text(e_kbru-0.5, v_kbru, 'KB@Ru (+3.63)', ha='right', color='#3672A4', fontsize=12)

# KB@RuP-800
ax.plot(e_800, v_800, 'v', color='#448844', markeredgecolor='#448844', markersize=ms)
ax.text(e_800-0.5, v_800+0.3, 'KB@RuP-800 (+2.83)', ha='right', color='#337733', fontsize=12)

# KB@RuP-550
ax.plot(e_550, v_550, 'v', color='#006699', markeredgecolor='#006699', markersize=ms)
ax.text(e_550-0.5, v_550+0.1, 'KB@RuP-550 (+2.77)', ha='right', color='#005588', fontsize=12)

# KB@RuP-300
ax.plot(e_300, v_300, 'v', color='#993333', markeredgecolor='#993333', markersize=ms)
ax.text(e_300-0.5, v_300-0.2, 'KB@RuP-300 (+2.69)', ha='right', color='#882222', fontsize=12)


# Styling
ax.set_xlabel('Energy (eV)', fontsize=14)
ax.set_ylabel('Valence state of Ru', fontsize=14)
ax.set_xlim(22116, 22132)
ax.set_ylim(-0.5, 4.5)
ax.set_xticks([22116, 22120, 22124, 22128, 22132])

# Ticks
ax.tick_params(direction='in', top=True, right=True)

plt.tight_layout()
plt.show()
