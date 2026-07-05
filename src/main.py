import pickle
import pandas as pd
from sentence_transformers import SentenceTransformer
from sklearn.metrics.pairwise import cosine_similarity
import os

class LocaFindEngine:
    def __init__(self):
        print("Loading LocaFind Brain...")
        
        # Path file berdasarkan struktur folder yang baru
        dataset_path = "models/processed_dataset.pkl"
        embeddings_path = "models/embeddings.pkl"
        
        # Memastikan file ada
        if not os.path.exists(dataset_path) or not os.path.exists(embeddings_path):
            raise FileNotFoundError("File model/data tidak ditemukan di folder models/")

        with open(dataset_path, "rb") as f:
            self.df = pickle.load(f)
        with open(embeddings_path, "rb") as f:
            self.embeddings = pickle.load(f)
        
        # Inisialisasi model pre-trained
        self.model = SentenceTransformer("LazarusNLP/all-indobert-base-v4")
        print("Engine Ready!")

    def cari(self, query, budget, category):
        # 1. Filtering Awal (Data Engineering)
        # Pastikan kolom sesuai dengan yang ada di pkl temanmu
        candidate = self.df[
            (self.df["Category"].str.lower() == category.lower()) & 
            (self.df["price_value"] <= budget)
        ].copy()

        if candidate.empty: 
            return "Tidak ada tempat yang sesuai dengan budget/kategori."

        # 2. Semantic Search (Modeling)
        query_emb = self.model.encode([query])
        # Ambil embedding berdasarkan row_id dari dataset
        cand_emb = self.embeddings[candidate["row_id"].values]
        
        # Hitung kemiripan
        sim_scores = cosine_similarity(query_emb, cand_emb).flatten()
        candidate["similarity"] = sim_scores

        # 3. Hybrid Scoring (Intelligence Layer)
        # Memberi bobot 0.7 untuk kemiripan, 0.3 untuk rating
        candidate["final_score"] = (
            0.7 * candidate["similarity"] + 
            0.3 * (candidate["Rating"] / 5.0)
        )
        
        # 4. Hapus Duplikat & Urutkan
        # Membersihkan hasil jika ada data yang terpecah hari
        candidate = candidate.drop_duplicates(subset=['Place_Name'])
        
        return candidate.sort_values("final_score", ascending=False).head(5)

if __name__ == "__main__":
    # Inisialisasi Engine
    engine = LocaFindEngine()
    
    # Simulasi kueri untuk demo presentasi
    print("\n--- HASIL REKOMENDASI ---")
    hasil = engine.cari("wisata sejarah", 50000, "Wisata")
    
    if isinstance(hasil, str):
        print(hasil)
    else:
        print(hasil[["Place_Name", "similarity", "final_score"]])