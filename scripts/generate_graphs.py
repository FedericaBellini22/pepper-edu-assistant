# -*- coding: utf-8 -*-
import pandas as pd
import matplotlib.pyplot as plt
import seaborn as sns
import os

LOG_FILE_PATH = 'benchmark_log.csv' 
OUTPUT_DIR = 'benchmark_graphs'

if not os.path.exists(LOG_FILE_PATH):
    print("ERRORE: File not found in '{}'".format(LOG_FILE_PATH))
    exit()

if not os.path.exists(OUTPUT_DIR):
    os.makedirs(OUTPUT_DIR)

df = pd.read_csv(LOG_FILE_PATH)

if df.empty:
    print("WARNING: The log file '{}' is empty. Unable to generate graphs.".format(LOG_FILE_PATH))
    exit()

sns.set_style("whitegrid")

# --- GRAPH 1: FOCUS vs SUCCESS ---
plt.figure(figsize=(12, 7))
ax = sns.barplot(x='TopicName', y='AttentionScore', data=df, color='lightblue', label='Attention Score (%)')

# Overlay a dot chart to indicate success (right/wrong)
sns.stripplot(x='TopicName', y=[5 if correct else 5 for correct in df['IsCorrect']], 
              hue=df['IsCorrect'].map({1: 'Correct Answer', 0: 'Incorrect Answer'}),
              palette={'Correct Answer': 'green', 'Incorrect Answer': 'red'},
              data=df, s=15, jitter=False, ax=ax, linewidth=1, edgecolor='black')

plt.title('Attention Score and Answer Correctness per Topic', fontsize=16)
plt.xlabel('Topic', fontsize=12)
plt.ylabel('Attention Score (%)', fontsize=12)
plt.xticks(rotation=25, ha='right')
plt.ylim(0, 110)
plt.legend(title='Outcome')
plt.tight_layout()
plt.savefig(os.path.join(OUTPUT_DIR, 'attention_vs_success.png'))
print("Graph 'attention_vs_success.png' saved in '{}'".format(OUTPUT_DIR))


# --- GRAPH 2: TREND OF ATTENTION OVER TIME ---
plt.figure(figsize=(12, 6))
plt.plot(df['TopicName'], df['AttentionScore'], marker='o', linestyle='-', color='purple')
plt.title('Attention Trend Throughout the Lesson', fontsize=16)
plt.xlabel('Topic Sequence', fontsize=12)
plt.ylabel('Attention Score (%)', fontsize=12)
plt.xticks(rotation=25, ha='right')
plt.ylim(0, 105)
plt.grid(True)
plt.tight_layout()
plt.savefig(os.path.join(OUTPUT_DIR, 'attention_trend.png'))
print("Grafico 'attention_trend.png' salvato in '{}'".format(OUTPUT_DIR))


# --- GRAPH 3: GENERAL SUMMARY (PIE) ---
correct_count = df['IsCorrect'].sum()
incorrect_count = len(df) - correct_count

if correct_count > 0 or incorrect_count > 0:
    plt.figure(figsize=(8, 8))
    plt.pie([correct_count, incorrect_count], labels=['Correct Answers', 'Incorrect Answers'], 
            autopct='%1.1f%%', startangle=90, colors=['#4CAF50', '#F44336'])
    plt.title('Overall Quiz Performance', fontsize=16)
    plt.savefig(os.path.join(OUTPUT_DIR, 'overall_performance.png'))
    print("Graph 'overall_performance.png' saved in '{}'".format(OUTPUT_DIR))
else:
    print("No data to generate the graph 'overall_performance.png'.")

try:
    plt.show()
except Exception as e:
    print("\nUnable to show graphs on screen (it may be an environment without a graphical user interface). The files have been saved.")
    print("Error: {}".format(e))