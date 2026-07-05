import geocoder
import folium
from src.engine_final import LocaFindEngine

def get_current_location():
    try:
        g = geocoder.ip('me')
        return g.latlng if g.latlng else [-7.2662, 112.7836]
    except:
        return [-7.2662, 112.7836]

def extract_intents(narration):
    categories = ["wisata alam", "cafe", "makan", "wisata malam", "sejarah", "nongkrong", "wisata"]
    found = []
    segments = narration.replace('.', ',').split(',')
    for segment in segments:
        for cat in categories:
            if cat in segment.lower():
                found.append(cat)
                break 
    return found

def buat_peta(itinerary, lat_awal, lon_awal):
    m = folium.Map(location=[lat_awal, lon_awal], zoom_start=14)
    rute_points = [[lat_awal, lon_awal]]
    folium.Marker([lat_awal, lon_awal], icon=folium.Icon(color='blue'), popup='Start').add_to(m)
    
    for i, dest in enumerate(itinerary):
        rute_points.append([dest['Lat'], dest['Long']])
        folium.Marker([dest['Lat'], dest['Long']], icon=folium.Icon(color='red'), popup=f"{i+1}: {dest['Place_Name']}").add_to(m)
    
    folium.PolyLine(rute_points, color="blue", weight=3, opacity=0.8).add_to(m)
    m.save("peta_liburan.html")
    print("\n✅ Peta (peta_liburan.html) berhasil diperbarui.")

def run_smart_itinerary():
    engine = LocaFindEngine()
    lat, lon = get_current_location()
    
    print(f"\n📍 Lokasi terdeteksi: {lat}, {lon}")
    narration = input("\nCeritakan rencana liburanmu: ")
    budget = int(input("Total budget liburan hari ini (Rp): "))
    
    query_list = extract_intents(narration)
    budget_per_slot = budget // len(query_list) if query_list else 0
    
    print(f"\n🚀 Menyusun rute (Budget/slot: Rp{budget_per_slot:,})...")
    
    current_lat, current_lon = lat, lon
    visited = []
    hasil_itinerary = []
    total_jarak = 0
    
    for i, activity in enumerate(query_list):
        hasil = engine.run_pipeline(activity, budget_per_slot, current_lat, current_lon)
        # Menghapus hasil yang sudah dikunjungi
        hasil = hasil[~hasil['Place_Name'].isin(visited)]
        
        if not hasil.empty:
            dest = hasil.iloc[0]
            visited.append(dest['Place_Name'])
            hasil_itinerary.append(dest)
            
            print(f"\n[Slot {i+1}] {activity.upper()}")
            print(f"➤ Destinasi: {dest['Place_Name']} | Harga: Rp{dest['Price']:,.0f}")
            print(f"➤ Jarak: {dest['Jarak']:.1f} km")
            
            current_lat, current_lon = dest['Lat'], dest['Long']
            total_jarak += dest['Jarak']
        else:
            print(f"\n[Slot {i+1}] {activity.upper()} -> Tidak ditemukan destinasi yang sesuai.")

    if hasil_itinerary:
        buat_peta(hasil_itinerary, lat, lon)
        
    print(f"\n" + "="*50)
    print(f"✅ Itinerary Selesai. Total estimasi jarak: {total_jarak:.1f} km")
    print("="*50)

if __name__ == "__main__":
    run_smart_itinerary()