import math
import os
from flask import Flask, render_template, request
from datetime import datetime, timedelta
import re
from src.engine_final import LocaFindEngine

app = Flask(__name__)
engine = LocaFindEngine()

def get_image_filename(no):
    """
    Mencari file gambar berdasarkan nomor.
    Mendukung jpg, jpeg, png, webp.
    """

    folder = os.path.join(app.static_folder, "static_1")

    extensions = ["jpg", "jpeg", "png", "webp"]

    for ext in extensions:

        filename = f"{no}.{ext}"

        full_path = os.path.join(folder, filename)

        if os.path.exists(full_path):
            return f"static_1/{filename}"

    # jika gambar tidak ditemukan
    return "images/hero.jpg"
# ==========================
# FUNGSI NLP
# ==========================
def extract_budget(text):
    text = text.lower()

    match_ribu = re.search(r'\b(\d+)\s*(ribu|rb)\b', text)
    if match_ribu:
        return int(match_ribu.group(1)) * 1000

    match_angka = re.search(r'\b(\d{1,3}(?:\.\d{3})+|\d{4,})\b', text)
    if match_angka:
        return int(match_angka.group(1).replace('.', ''))

    return 100000


def generate_itinerary_sequence(narration, selected_categories):
    narration = narration.lower()

    is_terserah = any(word in narration for word in [
        'terserah',
        'bebas',
        'rekomendasi',
        'atur',
        'bingung',
        'random',
        'tergantung'
    ])

    sequence = []

    if is_terserah:

        pola_logis = []

        if 'wisata' in selected_categories:
            pola_logis.append('wisata')

        if 'kuliner' in selected_categories:
            pola_logis.append('kuliner')

        if 'pusat perbelanjaan' in selected_categories:
            pola_logis.append('pusat perbelanjaan')

        if 'cafe' in selected_categories:
            pola_logis.append('cafe')

        sequence = [cat for cat in pola_logis if cat in selected_categories]
        sequence = (sequence * 3)[:6]

    else:

        words = re.findall(r'\w+', narration)

        for word in words:

            if word in [
                'wisata',
                'rekreasi',
                'sejarah',
                'taman',
                'alam',
                'museum',
                'air'
            ] and 'wisata' in selected_categories:

                if not sequence or sequence[-1] != 'wisata':
                    sequence.append('wisata')

            elif word in [
                'makan',
                'kuliner',
                'restoran',
                'lapar',
                'sarapan',
                'siang',
                'bebek',
                'goreng'
            ] and 'kuliner' in selected_categories:

                if not sequence or sequence[-1] != 'kuliner':
                    sequence.append('kuliner')

            elif word in [
                'cafe',
                'kafe',
                'nongkrong',
                'ngopi',
                'kopi'
            ] and 'cafe' in selected_categories:

                if not sequence or sequence[-1] != 'cafe':
                    sequence.append('cafe')
            elif word in [
                'mall',
                'mal',
                'shopping',
                'belanja',
                'plaza',
                'tunjungan',
                'pakuwon'
            ] and 'pusat perbelanjaan' in selected_categories:
                if not sequence or sequence[-1] != 'pusat perbelanjaan':
                    sequence.append('pusat perbelanjaan')
        if not sequence:
            sequence = (selected_categories * 2)[:4]

    return sequence if sequence else ['wisata']


# ==========================
# ROUTING
# ==========================

@app.route('/')
def home():
    return render_template('index.html')


@app.route('/recommend', methods=['POST'])
def recommend():

    budget_input = request.form.get('budget', '').strip()
    narration = request.form.get('narration', '')
    start_time_str = request.form.get('start_time', '08:00')
    end_time_str = request.form.get('end_time', '20:00')
    kategori_terpilih = request.form.getlist('kategori')

    # ==========================
    # Setup Budget & Waktu
    # ==========================

    budget = int(budget_input) if budget_input else extract_budget(narration)

    fmt = "%H:%M"

    start_dt = datetime.strptime(start_time_str, fmt)
    end_dt = datetime.strptime(end_time_str, fmt)

    durasi_map = {
        'wisata':120,
        'kuliner':60,
        'cafe':90,
        'pusat perbelanjaan':180
    }

    query_list = generate_itinerary_sequence(
        narration,
        kategori_terpilih
    )

    # ==========================
    # Variabel Itinerary
    # ==========================

    # ==========================
    # Starting Location
    # ==========================
    # ==================================
    # Lokasi awal (sementara untuk testing)
    # ==================================

    current_lat = -7.265125403961542
    current_lon = 112.7847387956772

    print("=" * 50)
    print("Menggunakan lokasi default")
    print("LAT =", current_lat)
    print("LON =", current_lon)
    print("=" * 50)
    user_lat = current_lat
    user_lon = current_lon
    current_time = start_dt

    visited = []

    hasil_itinerary = []

    total_jarak = 0
    total_biaya = 0

    # ==========================
    # FITUR BARU
    # Remaining Budget
    # ==========================

    remaining_budget = budget

    # ==========================
    # Generate Itinerary
    # ==========================

    category_index = 0
    gagal_mencari = 0

    while current_time < end_dt:

        # budget habis
        if remaining_budget <= 0:
            break

        # semua kategori kosong
        if len(query_list) == 0:
            break

        # jika sudah terlalu banyak gagal mencari tempat
        if gagal_mencari >= 10:
            break

        # kategori dipilih bergantian
        category = query_list[
            category_index % len(query_list)
        ]

        category_index += 1

        durasi_lokasi = durasi_map.get(category, 60)

        # cek apakah masih cukup waktu
        if current_time + timedelta(minutes=durasi_lokasi) > end_dt:
            break

        hasil = engine.run_pipeline(
            f"{category} {narration}",
            remaining_budget,
            current_lat,
            current_lon,
            top_n=5
        )

        hasil = hasil[
            ~hasil['Place_Name'].isin(visited)
        ]

        if hasil.empty:
            gagal_mencari += 1
            continue

        # ==========================
        # SMART CANDIDATE SELECTION
        # (Greedy Nearest Neighbor)
        # ==========================

        best_candidate = None
        best_distance = float("inf")

        for _, kandidat in hasil.iterrows():

            # -----------------------
            # Budget
            # -----------------------

            harga = int(kandidat["Price"])

            if harga > remaining_budget:
                continue

            # -----------------------
            # Open Hour
            # -----------------------

            try:

                buka = datetime.strptime(
                    kandidat["Open_time"].strip(),
                    "%H:%M"
                ).time()

                tutup = datetime.strptime(
                    kandidat["Close_time"].strip(),
                    "%H:%M"
                ).time()

            except:
                continue

            arrival_time = current_time.time()

            if not (buka <= arrival_time <= tutup):
                continue

            # -----------------------
            # Remaining Time
            # -----------------------

            kecepatan = 40

            travel_minutes_candidate = max(
                1,
                math.ceil((kandidat["Jarak"] / kecepatan) * 60)
            )

            estimasi_selesai = current_time + timedelta(
                minutes=travel_minutes_candidate + durasi_lokasi
            )

            if estimasi_selesai > end_dt:
                continue

            # -----------------------
            # Route Optimization
            # -----------------------

            if kandidat["Jarak"] < best_distance:

                best_distance = kandidat["Jarak"]

                best_candidate = kandidat

                best_travel_minutes = travel_minutes_candidate

        if best_candidate is None:
            gagal_mencari += 1
            continue

        dest = best_candidate
        gagal_mencari = 0
        travel_minutes = best_travel_minutes
        visited.append(dest["Place_Name"])

        # ==========================
        # DETAIL TIMELINE
        # ==========================

        departure_before = current_time.strftime("%H:%M")

        # waktu perjalanan
        current_time += timedelta(minutes=travel_minutes)

        arrival = current_time.strftime("%H:%M")

        # waktu mulai aktivitas
        visit_start = arrival

        # waktu selesai aktivitas
        current_time += timedelta(minutes=durasi_lokasi)

        departure = current_time.strftime("%H:%M")

        visit_end = departure

        harga = int(dest["Price"])

        # Kurangi budget yang masih tersisa
        remaining_budget -= harga

        # Jaga agar tidak minus
        if remaining_budget < 0:
            remaining_budget = 0

        hasil_itinerary.append({

            'ID': int(dest['No']) if 'No' in dest else len(hasil_itinerary)+1,

            'Image': get_image_filename(int(dest['No']) if 'No' in dest else len(hasil_itinerary)+1),

            'Place_Name': dest['Place_Name'],

            'Category': dest['Category'],

            'Price': harga,

            'Lat': float(dest['Lat']),

            'Long': float(dest['Long']),

            'Jarak': round(dest['Jarak'], 1),

            'Time_Slot': f"{arrival} - {departure}",

            # ==========================
            # Timeline Detail
            # ==========================

            'Departure_From_Previous': departure_before,

            'Arrival_Time': arrival,

            'Visit_Start': visit_start,

            'Visit_End': visit_end,

            'Travel_Time': travel_minutes,

            'Visit_Time': durasi_lokasi,

            'Remaining_Budget': remaining_budget

        })

        # Update posisi user
        current_lat = dest["Lat"]
        current_lon = dest["Long"]

        total_jarak += dest["Jarak"]
        total_biaya += harga
    
    starting_point = {
        "Lat": user_lat,
        "Lon": user_lon
    }

    maps_url = (
        f"https://www.google.com/maps/dir/"
        f"{user_lat},{user_lon}/"
    )

    for item in hasil_itinerary:
        maps_url += f"{item['Lat']},{item['Long']}/"

    return render_template(

        "hasil.html",

        itinerary=hasil_itinerary,

        total_jarak=round(total_jarak,1),

        total_budget=total_biaya,

        budget_awal=budget,

        remaining_budget=remaining_budget,

        starting_point=starting_point,
        
        maps_url=maps_url

    )


if __name__ == "__main__":
    app.run(debug=True)
