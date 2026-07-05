import pandas as pd
import numpy as np

# Simulasi kueri dan hasil untuk evaluasi
def evaluate_weights(similarity, rating, review_count, weight_sim, weight_rat, weight_rev):
    # Rumus hybrid score
    return (weight_sim * similarity) + (weight_rat * rating) + (weight_rev * review_count)

# Daftar bobot yang mau kita coba (kombinasi yang totalnya 1.0)
test_weights = [
    {"sim": 0.6, "rat": 0.2, "rev": 0.2},
    {"sim": 0.7, "rat": 0.2, "rev": 0.1},
    {"sim": 0.8, "rat": 0.1, "rev": 0.1}, # Fokus ke akurasi semantic
]

print("=== EVALUASI MODEL BOBOT ===")
for w in test_weights:
    print(f"Mencoba bobot: Sim={w['sim']}, Rating={w['rat']}, Review={w['rev']}")
    # Di sini nanti kamu bisa masukkan data hasil testingmu
    # Dan lihat rata-rata similarity-nya