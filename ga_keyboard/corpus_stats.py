from __future__ import annotations
from collections import Counter
from typing import Dict


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

