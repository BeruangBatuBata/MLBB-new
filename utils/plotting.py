# beruangbatubata/mlbb-new/MLBB-new-44d3b1513eb1b302f1f96286fcccc3d4374561ec/utils/plotting.py
import streamlit as st
import matplotlib.pyplot as plt
import seaborn as sns
import numpy as np
import base64

# REMOVED: render_strictly_sticky_table - Use st.dataframe() instead.
# REMOVED: render_paired_tables - Use st.columns() and st.dataframe() instead.

def offer_csv_download(df, filename="data.csv", label="Download CSV"):
    """
    Generates a Streamlit download button for a DataFrame.
    """
    csv = df.to_csv(index=False).encode('utf-8')
    st.download_button(
        label=label,
        data=csv,
        file_name=filename,
        mime='text/csv',
    )

def plot_synergy_bar(df, title, focus_hero=None):
    """
    Generates and returns a matplotlib bar chart for synergy stats.
    """
    if df.empty:
        return None
    
    fig, ax = plt.subplots(figsize=(8, 0.32 * len(df) + 1.1))
    
    if focus_hero and focus_hero != "(Show All)":
        desc = [h2 if h1 == focus_hero else h1 for h1, h2 in zip(df["Hero 1"], df["Hero 2"])]
    else:
        desc = [f"{h1} + {h2}" for h1, h2 in zip(df["Hero 1"], df["Hero 2"])]
        
    colors = ['#43a047' if x >= 55 else '#e53935' if x <= 45 else '#ffb300' for x in df["Win Rate (%)"]]
    
    ax.barh(desc, df["Win Rate (%)"], color=colors)
    
    for i, value in enumerate(df["Win Rate (%)"]):
        ax.text(value + 0.5, i, f'{value:.1f}%', va='center', fontsize=10, fontweight='bold')
        
    ax.set_xlabel("Win Rate (%)", fontsize=11, fontweight='bold')
    ax.set_title(title, fontsize=15, fontweight='bold', pad=11)
    ax.xaxis.grid(True, linestyle=':', alpha=0.45)
    ax.set_axisbelow(True)
    ax.set_facecolor('#f7fbfc')
    sns.despine(left=True, bottom=True)
    ax.tick_params(axis='y', labelsize=11)
    
    try:
        fig.tight_layout()
    except Exception:
        pass
        
    plt.subplots_adjust(left=0.26, right=0.98, bottom=0.13, top=0.93)
    return fig

def plot_counter_heatmap(df, title, max_heroes=10):
    """
    Generates and returns a matplotlib heatmap for counter stats.
    """
    if df.empty:
        return None
        
    mat = df.pivot(index="Ally Hero", columns="Enemy Hero", values="Win Rate (%)")
    n_rows, n_cols = mat.shape
    if n_rows <= 1 or n_cols <= 1:
        return None

    if n_rows > max_heroes:
        idx = mat.sum(axis=1).sort_values(ascending=False).index[:max_heroes]
        mat = mat.loc[idx]
    if n_cols > max_heroes:
        cols = mat.sum(axis=0).sort_values(ascending=False).index[:max_heroes]
        mat = mat[cols]
        
    n_rows, n_cols = mat.shape
    font_size = 13 if n_rows <= 10 else 10 if n_rows <= 18 else 8
    height = min(0.6 * n_rows + 1.5, 8)
    width  = min(0.56 * n_cols + 2.5, 12)

    fig, ax = plt.subplots(figsize=(width, height))
    cmap = sns.color_palette("crest", as_cmap=True)
    
    sns.heatmap(
        mat, annot=False, fmt='.1f', cmap=cmap, linewidths=0.6, ax=ax,
        cbar_kws={'label': 'Win Rate (%)', 'shrink': 0.87}
    )
    
    for y in range(mat.shape[0]):
        for x in range(mat.shape[1]):
            value = mat.values[y, x]
            if np.isnan(value):
                continue
            color = "white" if value < 47 or value > 53 else "black"
            ax.text(
                x + 0.5, y + 0.5, f"{value:.1f}",
                ha='center', va='center',
                fontsize=font_size, fontweight='bold', color=color
            )
            
    ax.set_title(title, fontsize=15, fontweight='bold', pad=13)
    ax.set_xlabel("Enemy Hero", fontsize=font_size+1, fontweight='bold', labelpad=8)
    ax.set_ylabel("Ally Hero", fontsize=font_size+1, fontweight='bold', labelpad=8)
    ax.set_xticklabels(ax.get_xticklabels(), rotation=35, ha='right', fontsize=font_size, fontweight='bold')
    ax.set_yticklabels(ax.get_yticklabels(), fontsize=font_size, fontweight='bold')
    
    fig.tight_layout()
    return fig
