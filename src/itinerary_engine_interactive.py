from engine_final import LocaFindEngine

def run_interactive_itinerary():
    engine = LocaFindEngine()
    
    print("\n" + "="*50)
    print("   SELAMAT DATANG DI LOCAFIND ITINERARY BUILDER")
    print("="*50)
    
    # 1. Input Data Pengguna
    print("Masukkan lokasi awal Anda (Contoh: -7.2662, 112.7836)")
    coord = input("Lat, Lon : ").split(',')
    lat, lon = float(coord[0].strip()), float(coord[1].strip())
    
    budget = int(input("Masukkan total budget liburan Anda: "))
    
    print("\nMasukkan rencana perjalanan Anda (pisahkan dengan koma)")
    print("Contoh: wisata alam pagi, cafe estetik siang, makan legend, wisata malam")
    query_raw = input("Rencana: ")
    query_list = [q.strip() for q in query_raw.split(',')]
    
    # 2. Proses Itinerary (Sesuai logika Greedy kita)
    itinerary = []
    current_lat, current_lon = lat, lon
    budget_per_slot = budget // len(query_list)
    
    print("\n⏳ Sedang menyusun rute terbaik untuk Anda...")
    
    for i, activity in enumerate(query_list):
        hasil = engine.run_pipeline(activity, budget_per_slot, current_lat, current_lon, top_n=1)
        
        if not hasil.empty:
            dest = hasil.iloc[0]
            itinerary.append(dest)
            current_lat, current_lon = dest['Lat'], dest['Long']
            
            print(f"\n[Slot {i+1}] {activity.upper()}")
            print(f"Destinasi : {dest['Place_Name']}")
            print(f"Harga     : Rp{dest['Price']:,.0f}")
            print(f"Jarak     : {dest['Jarak']:.2f} Km")
        else:
            print(f"\n[Slot {i+1}] {activity.upper()} -> Tidak ditemukan destinasi yang cocok.")

    print("\n" + "="*50)
    print("✨ Itinerary selesai disusun!")
    print("="*50)

if __name__ == "__main__":
    run_interactive_itinerary()