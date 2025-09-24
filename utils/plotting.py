import streamlit as st
import matplotlib.pyplot as plt
import seaborn as sns
import numpy as np

def plot_synergy_bar_chart(df, title, focus_hero=None):
    """Generates a styled horizontal bar chart for synergy/anti-synergy."""
    if df.empty:
        st.warning("No data to plot.")
        return

    fig, ax = plt.subplots(figsize=(8, 0.35 * len(df) + 1.2))

    if focus_hero:
        # Show only the partner hero in the label if a focus hero is selected
        y_labels = [h2 if h1 == focus_hero else h1 for h1, h2 in zip(df["Hero 1"], df["Hero 2"])]
    else:
        y_labels = [f"{h1} + {h2}" for h1, h2 in zip(df["Hero 1"], df["Hero 2"])]
    
    win_rates = df["Win Rate (%)"]
    colors = ['#43a047' if x >= 55 else '#e53935' if x <= 45 else '#ffb300' for x in win_rates]

    ax.barh(y_labels, win_rates, color=colors)

    # Add annotations
    for i, value in enumerate(win_rates):
        ax.text(value + 0.5, i, f'{value:.1f}%', va='center', fontsize=10, fontweight='bold')

    ax.set_xlabel("Win Rate (%)", fontsize=11, fontweight='bold')
    ax.set_title(title, fontsize=15, fontweight='bold', pad=12)
    ax.xaxis.grid(True, linestyle=':', alpha=0.5)
    ax.set_facecolor('#f7f7f7') # Light gray background for contrast
    sns.despine(left=True, bottom=True)
    ax.tick_params(axis='y', labelsize=11)
    
    # Invert y-axis to show the highest value at the top
    ax.invert_yaxis()
    
    plt.tight_layout()
    st.pyplot(fig)


def plot_counter_heatmap(df, title):
    """Generates a styled heatmap for counter matchups."""
    if df.empty or len(df) < 2:
        st.warning("Not enough data to generate a meaningful heatmap.")
        return

    pivot_df = df.pivot(index="Ally Hero", columns="Enemy Hero", values="Win Rate (%)")
    
    # Limit heatmap size for readability
    max_heroes = 15
    if pivot_df.shape[0] > max_heroes:
        top_allies = pivot_df.sum(axis=1).nlargest(max_heroes).index
        pivot_df = pivot_df.loc[top_allies]
    if pivot_df.shape[1] > max_heroes:
        top_enemies = pivot_df.sum(axis=0).nlargest(max_heroes).index
        pivot_df = pivot_df[top_enemies]

    height = min(0.6 * pivot_df.shape[0] + 1.5, 12)
    width = min(0.6 * pivot_df.shape[1] + 2.5, 15)
    
    fig, ax = plt.subplots(figsize=(width, height))
    
    sns.heatmap(
        pivot_df,
        annot=True,
        fmt=".1f",
        cmap="coolwarm",
        linewidths=0.5,
        ax=ax,
        cbar_kws={'label': 'Win Rate (%)'}
    )
    
    ax.set_title(title, fontsize=15, fontweight='bold', pad=13)
    ax.set_xlabel("Enemy Hero", fontsize=12, fontweight='bold')
    ax.set_ylabel("Ally Hero", fontsize=12, fontweight='bold')
    plt.xticks(rotation=45, ha='right')
    
    st.pyplot(fig)
