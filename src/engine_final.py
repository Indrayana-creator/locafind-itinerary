import pandas as pd
import pickle
import math
import warnings
from sentence_transformers import SentenceTransformer
from sklearn.metrics.pairwise import cosine_similarity

warnings.filterwarnings('ignore')

class LocaFindEngine:
    def __init__(self):
        with open("models/dataset.pkl", "rb") as f: self.df = pickle.load(f)
        with open("models/embeddings.pkl", "rb") as f: self.embeddings = pickle.load(f)
        self.model = SentenceTransformer("models/locafind_sbert_model")
        
        self.df['Lat'] = pd.to_numeric(self.df['Lat'].astype(str).str.replace(',', '.'), errors='coerce')
        self.df['Long'] = pd.to_numeric(self.df['Long'].astype(str).str.replace(',', '.'), errors='coerce')
        self.df = self.df.dropna(subset=['Lat', 'Long'])

    def hitung_jarak(self, lat1, lon1, lat2, lon2):
        R = 6371.0
        dlat, dlon = math.radians(lat2-lat1), math.radians(lon2-lon1)
        a = math.sin(dlat/2)**2 + math.cos(math.radians(lat1)) * math.cos(math.radians(lat2)) * math.sin(dlon/2)**2
        return R * 2 * math.atan2(math.sqrt(a), math.sqrt(1-a))

    def run_pipeline(self, query, budget, user_lat, user_lon, top_n=5):

        # ==========================================================
        # 1. HARD FILTER : Budget
        # ==========================================================

        df_res = self.df[self.df["Price"] <= budget].copy()

        if df_res.empty:
            return df_res

        # ==========================================================
        # 2. SEMANTIC SEARCH
        # ==========================================================

        q_emb = self.model.encode([query])

        df_res["Skor_AI"] = cosine_similarity(
            q_emb,
            self.embeddings[df_res.index]
        ).flatten()

        # ==========================================================
        # 3. CATEGORY BOOST
        # ==========================================================

        df_res["Bonus"] = 0.0

        query_lower = query.lower()

        mask = df_res["Category"].str.lower().str.contains(
            query_lower,
            na=False
        )

        # bonus diperkecil agar tidak mendominasi
        df_res.loc[mask, "Bonus"] = 0.35

        # ==========================================================
        # 4. HITUNG JARAK
        # ==========================================================

        df_res["Jarak"] = df_res.apply(
            lambda r: self.hitung_jarak(
                user_lat,
                user_lon,
                r["Lat"],
                r["Long"]
            ),
            axis=1
        )
        # ==========================================================
        # 5. NORMALISASI RATING
        # ==========================================================

        try:
            df_res["Rating"] = (
                df_res["Rating"]
                .astype(str)
                .str.replace(",", ".")
                .astype(float)
            )

        except:

            df_res["Rating"] = 4.0

        df_res["Rating_Norm"] = (
            df_res["Rating"] / 5
        )

        # ==========================================================
        # 6. NORMALISASI REVIEW
        # ==========================================================

        max_review = df_res["Review_count"].max()

        if max_review == 0:
            max_review = 1

        df_res["Review_Norm"] = (
            df_res["Review_count"] /
            max_review
        )
        # ==========================================================
        # 7. NORMALISASI JARAK
        # ==========================================================

        max_distance = df_res["Jarak"].max()

        if max_distance == 0:
            max_distance = 1

        df_res["Distance_Norm"] = 1 - (
            df_res["Jarak"] /
            max_distance
        )
        # ==========================================================
        # 8. FINAL RE-RANKING
        # ==========================================================

        df_res["Final_Score"] = (

            0.55 * df_res["Skor_AI"]

            +

            0.20 * df_res["Rating_Norm"]

            +

            0.15 * df_res["Review_Norm"]

            +

            0.10 * df_res["Distance_Norm"]

            +

            df_res["Bonus"]

        )
        # ==========================================================
        # 9. SORTING
        # ==========================================================

        df_res = df_res.sort_values(
            by="Final_Score",
            ascending=False
        )

        return df_res.head(top_n)