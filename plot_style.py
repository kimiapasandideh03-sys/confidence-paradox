"""Shared plotting conventions. Analyses and output values remain unchanged."""
import matplotlib.pyplot as plt
PRIMARY = '#334E68'      # muted slate blue
TEAL = '#5B7F84'         # muted teal
CLAY = '#A06A5B'         # muted terracotta
GREY = '#7A828C'         # cool grey
LIGHT_GREY = '#D7DDE2'
INK = '#111111'

plt.rcParams.update({
    'font.family': 'DejaVu Sans',
    'font.size': 10,
    'axes.titlesize': 12,
    'axes.titleweight': 'semibold',
    'axes.labelsize': 10,
    'xtick.labelsize': 9,
    'ytick.labelsize': 9,
    'legend.fontsize': 8.5,
    'text.color': INK,
    'axes.labelcolor': INK,
    'axes.edgecolor': '#808080',
    'axes.linewidth': 0.8,
    'xtick.color': INK,
    'ytick.color': INK,
    'axes.spines.top': False,
    'axes.spines.right': False,
    'savefig.dpi': 220,
    'figure.facecolor': 'white',
    'axes.facecolor': 'white'
})

# Backward-compatible names used by scripts
NAVY = PRIMARY
ORANGE = CLAY
