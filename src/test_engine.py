import pandas as pd
import pickle
import math
import warnings
from sentence_transformers import SentenceTransformer
from sklearn.metrics.pairwise import cosine_similarity

warnings.filterwarnings('ignore')

class LocaFindEngine:
    def __init__(self):
        print("Menyiapkan Engine LocaFind (Hybrid & Spatial)...")
        with open("models/dataset.pkl", "rb") as f:
            self.df = pickle.load(f)
        with open("models/embeddings.pkl", "rb") as f:
            self.embeddings = pickle.load(f)
            
        self.model = SentenceTransformer("models/locafind_sbert_model")
        
        # [PENTING] Bersihkan koordinat jika formatnya menggunakan koma (misal: "-7,255" jadi "-7.255")
        if 'Lat' in self.df.columns and 'Long' in self.df.columns:
            self.df['Lat'] = pd.to_numeric(self.df['Lat'].astype(str).str.replace(',', '.'), errors='coerce')
            self.df['Long'] = pd.to_numeric(self.df['Long'].astype(str).str.replace(',', '.'), errors='coerce')

        print("✅ Engine Siap!\n")

    # Fungsi Haversine untuk menghitung jarak bumi (dalam Kilometer)
    def hitung_jarak(self, lat1, lon1, lat2, lon2):
        if pd.isna(lat1) or pd.isna(lon1) or pd.isna(lat2) or pd.isna(lon2):
            return 999.0 # Jika tidak ada kordinat, anggap sangat jauh
        
        R = 6371.0 # Radius Bumi dalam Km
        dlat = math.radians(lat2 - lat1)
        dlon = math.radians(lon2 - lon1)
        
        a = math.sin(dlat / 2)**2 + math.cos(math.radians(lat1)) * math.cos(math.radians(lat2)) * math.sin(dlon / 2)**2
        c = 2 * math.atan2(math.sqrt(a), math.sqrt(1 - a))
        return R * c

    def cari(self, preferensi, budget_maks, user_lat, user_lon, top_n=3):
        print("="*65)
        print(f"🔍 SKENARIO SPASIAL LOCAFIND")
        print(f"Preferensi : '{preferensi}'")
        print(f"Budget Max : Rp{budget_maks:,}")
        print(f"Lokasi User: Lat {user_lat}, Lon {user_lon}")
        print("="*65)

        # 1. HARD FILTER: Budget
        df_filtered = self.df[self.df['Price'] <= budget_maks].copy()
        if df_filtered.empty:
            print("Tidak ada destinasi yang sesuai budget.")
            return

        indeks_valid = df_filtered.index.tolist()

        # 2. SEMANTIC SEARCH (AI)
        query_emb = self.model.encode([preferensi])
        sim_scores = cosine_similarity(query_emb, self.embeddings).flatten()
        df_filtered['Skor_Semantik'] = sim_scores[indeks_valid]
        
        # 3. HEURISTIC BOOSTING (Kategori)
        pref_lower = preferensi.lower()
        if any(w in pref_lower for w in ['ngopi', 'kopi', 'nongkrong', 'cafe', 'kafe']):
            mask_cafe = df_filtered['Place_Name'].astype(str).str.contains('kopi|cafe|kafe|coffee|warkop|roastery', case=False, na=False)
            if 'Tags' in df_filtered.columns:
                mask_tags = df_filtered['Tags'].astype(str).str.contains('kopi|cafe|kafe|nongkrong', case=False, na=False)
                mask_cafe = mask_cafe | mask_tags
            df_filtered.loc[mask_cafe, 'Skor_Semantik'] += 0.35 
            
        if any(w in pref_lower for w in ['sejarah', 'museum', 'edukasi', 'belajar', 'budaya']):
            mask_sejarah = df_filtered['Category'].astype(str).str.contains('Wisata|Budaya', case=False, na=False)
            df_filtered.loc[mask_sejarah, 'Skor_Semantik'] += 0.15

        # 4. SPATIAL RANKING (Menghitung Jarak)
        # Terapkan fungsi Haversine ke setiap baris data
        df_filtered['Jarak_Km'] = df_filtered.apply(
            lambda row: self.hitung_jarak(user_lat, user_lon, row['Lat'], row['Long']), 
            axis=1
        )

        # 5. FINAL SORTING 
        # Urutkan berdasarkan Skor Semantik Tertinggi, lalu jika skornya sama/mirip, prioritaskan Jarak Terdekat (Ascending)
        hasil = df_filtered.sort_values(by=['Skor_Semantik', 'Jarak_Km'], ascending=[False, True]).head(top_n)

        # Tampilkan Hasil
        print("🏆 HASIL REKOMENDASI (SBERT + Heuristic + Spatial):")
        for i, row in hasil.iterrows():
            print(f"   - {row['Place_Name']}")
            print(f"     Skor AI    : {row['Skor_Semantik']:.4f}")
            print(f"     Jarak      : {row['Jarak_Km']:.2f} Km dari posisi Anda")
            print(f"     Harga      : Rp{row['Price']:,.0f}")
            print(f"     Kategori   : {row.get('Category', 'Umum')}\n")

if __name__ == "__main__":
    engine = LocaFindEngine()
    
    # Asumsi lokasi pengguna saat ini (Contoh: Area Universitas Airlangga / Kampus C)
    # Lat: -7.2662, Lon: 112.7836
    user_latitude = -7.2662
    user_longitude = 112.7836
    
    # Skenario:
    engine.cari("tempat nongkrong anak muda sambil ngopi", 150000, user_latitude, user_longitude, top_n=5)