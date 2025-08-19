# -*- coding: utf-8 -*-
"""
Created on Thu Apr  3 14:45:01 2025

@author: Dominique Neuhaus

Temperature Correction Model for DGM Substructures

- Plot MRI parameters vs. temperature 
    - (with 95% CI)
    - Temp range extension to [4,37]
    - Indication of statistical significance.
- Assess correlation with pearson (p and r)
- Get slope a and y-axis intersect b



"""

import os
import pandas as pd
import numpy as np
import matplotlib.pyplot as plt
import seaborn as sns
from scipy.stats import linregress, pearsonr, t
from glob import glob
from matplotlib.lines import Line2D
import matplotlib.patches as mpatches

# SETTINGS
base_dir = r"input/path/to/nifti/files"
temp_file = r"input/path/to/excel/containing/forehead/temperatures/during/scan"
output_csv = r"output/path/to/csv/file"
output_plot_dir = r"output/path/to/plots"
os.makedirs(output_plot_dir, exist_ok=True)

# STYLE & FONT
sns.set(style="whitegrid")
import matplotlib
matplotlib.rcParams.update({
    'font.size': 30,
    'axes.titlesize': 30,
    'axes.labelsize': 30,
    'legend.fontsize': 18,
    'xtick.labelsize': 24,
    'ytick.labelsize': 24
})

structure_groups = {
    'Basal Ganglia': ['Caudate', 'Putamen', 'Pallidum'],
    'Limbic System': ['Hippocampus', 'Amygdala'],
    'Relay Centers': ['Thalamus', 'Brainstem']
}

region_colors = {
    'Caudate':     '#1f77b4',
    'Putamen':     '#ff7f0e',
    'Pallidum':    '#2ca02c',
    'Hippocampus': '#9467bd',
    'Amygdala':    '#17becf',
    'Thalamus':    '#d62728',
    'Brainstem':   '#8c564b'
}

metrics = ['FA', 'MD', 'T1', 'T2', 'T2s']
region_exclude = ['Accumbens']

temp_map = {
    'FA': 'temp_DTI',
    'MD': 'temp_DTI',
    'T1': 'temp_T1',
    'T2': 'temp_T2',
    'T2s': 'temp_T2s'
}

temp_df = pd.read_excel(temp_file)

all_data = []

case_folders = glob(os.path.join(base_dir, '*'))
print(f"Found {len(case_folders)} case folders.")

for case_folder in case_folders:
    case_name = os.path.basename(case_folder)
    file_main = os.path.join(case_folder, "00_OUTPUT", f"{case_name}_output.csv")
    file_t1   = os.path.join(case_folder, "00_OUTPUT", f"{case_name}_output_correctT1.csv")

    print(f"\nProcessing case: {case_name}")
    if not os.path.exists(file_main):
        print("Skipped: Main file not found.")
        continue

    df_main = pd.read_csv(file_main)
    df_main['value'] = pd.to_numeric(df_main['value'], errors='coerce')

    df_t1 = pd.read_csv(file_t1) if os.path.exists(file_t1) else pd.DataFrame()
    if not df_t1.empty:
        df_t1['value'] = pd.to_numeric(df_t1['value'], errors='coerce')

    df_main = df_main[~df_main['region'].isin(region_exclude)]
    df_main = df_main.groupby(['case', 'metric', 'region']).first().reset_index()

    if not df_t1.empty:
        df_t1 = df_t1[~df_t1['region'].isin(region_exclude)]
        df_t1 = df_t1[df_t1['metric'] == 'T1'].groupby(['case', 'metric', 'region']).first().reset_index()
        df_main = df_main[df_main['metric'] != 'T1']
        df_main = pd.concat([df_main, df_t1], ignore_index=True)
    else:
        print(f"No corrected T1 file found for: {case_name}")

    temp_row = temp_df[temp_df['case'] == case_name]
    if temp_row.empty:
        print(f"Skipped: No matching temperature data for {case_name}")
        continue

    for metric in metrics:
        subset = df_main[df_main['metric'] == metric].copy()
        temp_col = temp_map[metric]
        temp_value = temp_row[temp_col].values
        if len(temp_value) == 0:
            continue
        subset['temperature'] = temp_value[0]
        all_data.append(subset)

if not all_data:
    raise ValueError("No valid data found across cases. Please check file paths and temperature mapping.")

data = pd.concat(all_data, ignore_index=True)

summary = []

def format_sci(val, precision=2):
    return f"{val:.{precision}e}"

metric_labels = {
    'FA': r'$\mathrm{FA}$',
    'MD': r'$\mathrm{MD}\ [\mathrm{mm}^2/\mathrm{s}]$',
    'T1': r'$\mathrm{T}_1\ [\mathrm{ms}]$',
    'T2': r'$\mathrm{T}_2\ [\mathrm{ms}]$',
    'T2s': r'$\mathrm{T}_2^*\ [\mathrm{ms}]$'
}

for metric in metrics:
    for group_name, regions in structure_groups.items():
        plt.figure(figsize=(12, 8))
        added_regions = 0
        legend_entries = []

        for region in regions:
            df = data[(data['metric'] == metric) & (data['region'] == region)]
            if len(df) < 2:
                continue

            x = df['temperature']
            y = df['value']

            if x.isnull().any() or y.isnull().any() or not np.isfinite(y).all() or y.nunique() < 2:
                print(f"Skipping {region} ({metric}) due to NaN, non-finite or insufficient unique values.")
                continue

            r, p = pearsonr(x, y)
            slope, intercept, r_val, p_val, stderr_slope = linregress(x, y)
            r_squared = r_val ** 2

            n = len(x)
            dof = n - 2
            x_mean = np.mean(x)
            se_y = np.sqrt(np.sum((y - (slope * x + intercept)) ** 2) / dof)
            s_xx = np.sum((x - x_mean) ** 2)
            se_slope = se_y / np.sqrt(s_xx)
            se_intercept = se_y * np.sqrt(1 / n + (x_mean ** 2 / s_xx))

            t_val = t.ppf(0.975, dof)
            slope_ci = t_val * se_slope
            intercept_ci = t_val * se_intercept

            summary.append({
                'DGM Region': region,
                'MRI Parameter': metric,
                'Pearson r': format_sci(r, precision=4),
                'p-value': format_sci(p, precision=2),
                'Slope a': f"{format_sci(slope, 2)} ± {format_sci(slope_ci, 2)}",
                'Intercept b': f"{format_sci(intercept, 2)} ± {format_sci(intercept_ci, 2)}",
                'R_square': format_sci(r_squared, precision=4)
            })

            color = region_colors.get(region, None)

            plt.scatter(x, y, color=color)

            sns.regplot(x=x, y=y, ci=95, color=color, scatter=False,
                        line_kws={"lw":2, "alpha":1.0})

            if x.min() > 4:
                x_left = np.linspace(4, x.min(), 50)
                y_left = slope * x_left + intercept
                plt.plot(x_left, y_left, linestyle='--', color=color, lw=2)

            if x.max() < 37:
                x_right = np.linspace(x.max(), 37, 50)
                y_right = slope * x_right + intercept
                plt.plot(x_right, y_right, linestyle='--', color=color, lw=2)

            if p < 0.001:
                p_text = "p < 0.001"
            else:
                p_text = f"p = {p:.3f}"

            legend_entries.append((p_text, color, p < 0.05))
            added_regions += 1

        plt.xlabel("Forehead temperature [°C]")
        plt.ylabel(metric_labels.get(metric, metric))

        if added_regions > 0:
            legend_handles = []
            legend_labels = []
            for txt, col, is_bold in legend_entries:
                handle = Line2D([], [], linestyle='None')
                legend_handles.append(handle)
                legend_labels.append(txt)

            leg = plt.legend(
                handles=legend_handles,
                labels=legend_labels,
                loc='upper right',
                frameon=True,
                fontsize=18
            )

            frame = leg.get_frame()
            frame.set_facecolor('white')
            frame.set_alpha(0.9)

            for text, (_, col, is_bold) in zip(leg.get_texts(), legend_entries):
                text.set_color(col)
                if is_bold:
                    text.set_fontweight('bold')

            plt.tight_layout()
            filename_png = f"{metric}_{group_name.replace(' ', '_')}_vs_temp.png"
            plt.savefig(os.path.join(output_plot_dir, filename_png))
            filename_svg = f"{metric}_{group_name.replace(' ', '_')}_vs_temp.svg"
            plt.savefig(os.path.join(output_plot_dir, filename_svg))
        else:
            print(f"No valid data to plot for {metric} in {group_name}")

        plt.close()

summary_df = pd.DataFrame(summary)
summary_df.to_csv(output_csv, index=False, encoding='utf-8-sig')
print(f"Analysis complete. Summary saved to {output_csv}")

legend_handles = []
for region, color in region_colors.items():
    patch = mpatches.Patch(color=color, label=region)
    legend_handles.append(patch)

plt.figure(figsize=(10, 6))
plt.legend(handles=legend_handles, loc='center', frameon=False, ncol=2)
plt.axis('off')
plt.tight_layout()
plt.savefig(os.path.join(output_plot_dir, 'legend_only.png'))
plt.close()

