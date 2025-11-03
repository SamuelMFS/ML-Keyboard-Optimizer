#!/usr/bin/env python3
"""
Script to analyze corpus character frequencies and generate bar charts.

Can be run standalone or imported as a module.
"""

from __future__ import annotations
import argparse
import sys
import os
from collections import Counter
from typing import Dict, List, Tuple
import matplotlib.pyplot as plt
import numpy as np


def count_corpus_characters(corpus_path: str, out_path: str) -> None:
	"""Count all character occurrences in the corpus and write to file sorted by frequency."""
	with open(corpus_path, "r", encoding="utf-8", errors="ignore") as f:
		text = f.read()
	
	char_counts = Counter(text)
	
	# Sort by frequency (descending), then by character for ties
	sorted_chars = sorted(char_counts.items(), key=lambda x: (-x[1], x[0]))
	
	with open(out_path, "w", encoding="utf-8") as f:
		f.write("Character Frequency Count\n")
		f.write("=" * 50 + "\n")
		f.write(f"Total unique characters: {len(sorted_chars)}\n")
		f.write(f"Total characters: {sum(char_counts.values())}\n")
		f.write("=" * 50 + "\n\n")
		
		for char, count in sorted_chars:
			# Escape special characters for display
			if char == '\n':
				display = "\\n"
			elif char == '\t':
				display = "\\t"
			elif char == '\r':
				display = "\\r"
			elif char == ' ':
				display = "' ' (space)"
			elif ord(char) < 32 or ord(char) == 127:
				display = f"\\x{ord(char):02x}"
			else:
				display = char
			f.write(f"{display:20s} : {count:10d}\n")
	
	print(f"Estatísticas de frequência de caracteres escritas em {out_path}")


def _escape_char_for_display(char: str) -> str:
	"""Escape special characters for display."""
	if char == '\n':
		return "\\n"
	elif char == '\t':
		return "\\t"
	elif char == '\r':
		return "\\r"
	elif char == ' ':
		return "' ' (space)"
	elif ord(char) < 32 or ord(char) == 127:
		return f"\\x{ord(char):02x}"
	else:
		return char


def plot_character_frequencies(corpus_path: str, out_path: str, top_n: int = 50) -> None:
	"""Generate bar chart of character frequencies."""
	with open(corpus_path, "r", encoding="utf-8", errors="ignore") as f:
		text = f.read()
	
	char_counts = Counter(text)
	sorted_chars = sorted(char_counts.items(), key=lambda x: (-x[1], x[0]))
	
	# Take top N characters
	top_chars = sorted_chars[:top_n]
	
	if not top_chars:
		print("Aviso: Nenhum caractere encontrado no corpus")
		return
	
	labels = [_escape_char_for_display(char) for char, _ in top_chars]
	counts = [count for _, count in top_chars]
	
	# Create figure
	fig, ax = plt.subplots(figsize=(14, max(8, len(top_chars) * 0.15)))
	
	# Horizontal bar chart
	y_pos = np.arange(len(labels))
	colors = plt.cm.viridis(np.linspace(0, 1, len(labels)))
	bars = ax.barh(y_pos, counts, color=colors, alpha=0.7)
	
	# Labels
	ax.set_yticks(y_pos)
	ax.set_yticklabels(labels, fontsize=9)
	ax.set_xlabel('Frequência', fontsize=12, fontweight='bold')
	ax.set_title(f'Frequência de Caracteres no Corpus (Top {len(top_chars)})', 
	             fontsize=14, fontweight='bold', pad=20)
	
	# Add value labels on bars
	max_count = max(counts)
	for i, (bar, count) in enumerate(zip(bars, counts)):
		width = bar.get_width()
		ax.text(width + max_count * 0.01, bar.get_y() + bar.get_height()/2,
		        f'{count:,}', ha='left', va='center', fontsize=8)
	
	# Grid
	ax.grid(axis='x', alpha=0.3, linestyle='--')
	ax.set_axisbelow(True)
	
	# Add total count annotation
	total = sum(char_counts.values())
	ax.text(0.02, 0.98, f'Total de caracteres: {total:,}',
	        transform=ax.transAxes, fontsize=10, verticalalignment='top',
	        bbox=dict(boxstyle='round', facecolor='wheat', alpha=0.5))
	
	plt.tight_layout()
	os.makedirs(os.path.dirname(out_path), exist_ok=True)
	plt.savefig(out_path, dpi=150, bbox_inches='tight')
	plt.close()
	print(f"Gráfico de barras salvo em: {out_path}")


def plot_bigram_frequencies(corpus_path: str, out_path: str, top_n: int = 50) -> None:
	"""Generate bar chart of bigram frequencies in the corpus."""
	with open(corpus_path, "r", encoding="utf-8", errors="ignore") as f:
		text = f.read()
	
	# Count bigrams
	bigrams = [text[i:i+2] for i in range(len(text)-1)]
	bigram_counts = Counter(bigrams)
	sorted_bigrams = sorted(bigram_counts.items(), key=lambda x: (-x[1], x[0]))
	
	# Take top N bigrams
	top_bigrams = sorted_bigrams[:top_n]
	
	if not top_bigrams:
		print("Aviso: Nenhum bigrama encontrado no corpus")
		return
	
	labels = [f"{bg[0]}{bg[1]}" for bg, _ in top_bigrams]
	counts = [count for _, count in top_bigrams]
	
	# Create figure
	fig, ax = plt.subplots(figsize=(14, max(8, len(top_bigrams) * 0.15)))
	
	# Horizontal bar chart
	y_pos = np.arange(len(labels))
	colors = plt.cm.plasma(np.linspace(0, 1, len(labels)))
	bars = ax.barh(y_pos, counts, color=colors, alpha=0.7)
	
	# Labels
	ax.set_yticks(y_pos)
	ax.set_yticklabels(labels, fontsize=9, fontfamily='monospace')
	ax.set_xlabel('Frequência', fontsize=12, fontweight='bold')
	ax.set_title(f'Frequência de Bigramas no Corpus (Top {len(top_bigrams)})', 
	             fontsize=14, fontweight='bold', pad=20)
	
	# Add value labels on bars
	max_count = max(counts)
	for i, (bar, count) in enumerate(zip(bars, counts)):
		width = bar.get_width()
		ax.text(width + max_count * 0.01, bar.get_y() + bar.get_height()/2,
		        f'{count:,}', ha='left', va='center', fontsize=8)
	
	# Grid
	ax.grid(axis='x', alpha=0.3, linestyle='--')
	ax.set_axisbelow(True)
	
	# Add total count annotation
	total_bigrams = sum(bigram_counts.values())
	ax.text(0.02, 0.98, f'Total de bigramas: {total_bigrams:,}',
	        transform=ax.transAxes, fontsize=10, verticalalignment='top',
	        bbox=dict(boxstyle='round', facecolor='wheat', alpha=0.5))
	
	plt.tight_layout()
	os.makedirs(os.path.dirname(out_path), exist_ok=True)
	plt.savefig(out_path, dpi=150, bbox_inches='tight')
	plt.close()
	print(f"Gráfico de barras de bigramas salvo em: {out_path}")


def parse_args() -> argparse.Namespace:
	p = argparse.ArgumentParser(description="Analyze corpus character and bigram frequencies and generate visualizations")
	p.add_argument("--corpus", required=True, help="Path to corpus text file")
	p.add_argument("--out-txt", default=None, help="Output path for text statistics (default: corpus_character_frequencies.txt in corpus directory)")
	p.add_argument("--out-png-chars", default=None, help="Output path for character frequency bar chart PNG")
	p.add_argument("--out-png-bigrams", default=None, help="Output path for bigram frequency bar chart PNG")
	p.add_argument("--top-n", type=int, default=50, help="Number of top items to show in charts (default: 50)")
	p.add_argument("--chars-only", action="store_true", help="Only generate character frequency chart")
	p.add_argument("--bigrams-only", action="store_true", help="Only generate bigram frequency chart")
	return p.parse_args()


def main() -> None:
	args = parse_args()
	
	# Default output paths
	corpus_dir = os.path.dirname(args.corpus) or "."
	corpus_basename = os.path.splitext(os.path.basename(args.corpus))[0]
	
	txt_path = args.out_txt or os.path.join(corpus_dir, f"{corpus_basename}_character_frequencies.txt")
	chars_png = args.out_png_chars or os.path.join(corpus_dir, f"{corpus_basename}_character_frequencies.png")
	bigrams_png = args.out_png_bigrams or os.path.join(corpus_dir, f"{corpus_basename}_bigram_frequencies.png")
	
	print(f"Analisando corpus: {args.corpus}")
	
	# Generate text statistics (only if not bigrams-only)
	if not args.bigrams_only:
		count_corpus_characters(args.corpus, txt_path)
	
	# Generate character frequency chart
	if not args.bigrams_only:
		print(f"Gerando gráfico de frequência de caracteres...")
		plot_character_frequencies(args.corpus, chars_png, top_n=args.top_n)
	
	# Generate bigram frequency chart
	if not args.chars_only:
		print(f"Gerando gráfico de frequência de bigramas...")
		plot_bigram_frequencies(args.corpus, bigrams_png, top_n=args.top_n)
	
	print(f"\nAnálise completa!")
	if not args.bigrams_only:
		print(f"  Estatísticas em texto: {txt_path}")
		print(f"  Gráfico de caracteres: {chars_png}")
	if not args.chars_only:
		print(f"  Gráfico de bigramas: {bigrams_png}")


if __name__ == "__main__":
	main()

