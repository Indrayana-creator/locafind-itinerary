import pandas as pd
import pickle
import os
import warnings
from sentence_transformers import SentenceTransformer

warnings.filterwarnings('ignore')
os.makedirs("models", exist_ok=True)

print("Memuat dan membersihkan dataset...")
# MENGGUNAKAN read_csv KARENA FILENYA .csv
df = pd.read_csv("data/Dataset LocaFind - surabaya_tourism.csv") 
df.columns = df.columns.str.strip()

def fix_price(val):
    val_str = str(val).strip()
    if '-' in val_str: return float(val_str.split('-')[1].strip())
    try: return float(val_str)
    except: return 0.0

df['Price'] = df['Price'].apply(fix_price)

# ==========================================
# FEATURE ENGINEERING: DATA ENRICHMENT
# ==========================================
print("Melakukan pengayaan data semantik (Data Enrichment)...")

# Mengecek apakah ada kolom Tags di file, lalu membersihkan komanya
if 'Tags' in df.columns:
    df['Tags_Clean'] = df['Tags'].fillna('').astype(str).str.replace(',', ' ')
else:
    df['Tags_Clean'] = ''

def enrich_text(row):
    base_text = str(row.get('Category', '')) + " " + str(row.get('Description', ''))
    base_text_lower = base_text.lower()
    
    hidden_keywords = ""
    
    # Suntikan kata gaul khusus untuk tempat kuliner/nongkrong
    if any(word in base_text_lower for word in ['kuliner', 'kafe', 'cafe', 'kopi', 'restoran', 'makan', 'warung']):
        hidden_keywords += " tempat nongkrong anak muda santai ngopi hangout malam "
        
    # Gabungkan: Nama + Kategori + Deskripsi + Tags Asli + Keyword Tambahan
    return str(row.get('Place_Name', '')) + " " + base_text + " " + str(row['Tags_Clean']) + " " + hidden_keywords

df['Content'] = df.apply(enrich_text, axis=1)
# ==========================================

print("Generating embeddings menggunakan SBERT (Tunggu sebentar)...")
model = SentenceTransformer('paraphrase-multilingual-MiniLM-L12-v2')
embeddings = model.encode(df['Content'].tolist())

with open("models/dataset.pkl", "wb") as f:
    pickle.dump(df, f)
with open("models/embeddings.pkl", "wb") as f:
    pickle.dump(embeddings, f)
model.save("models/locafind_sbert_model")

print("✅ File model .pkl dengan Data Enrichment berhasil diperbarui!")