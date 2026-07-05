from engine_final import LocaFindEngine
from datetime import datetime

class ItineraryGenerator:
    def __init__(self):
        # Memanggil engine utama kita
        self.engine = LocaFindEngine()

    def generate_itinerary(self, query_list, start_lat, start_lon, total_budget):
        """
        query_list: list berisi string aktivitas (contoh: ["wisata alam", "cafe cozy"])
        start_lat/lon: lokasi awal user
        total_budget: budget total untuk seharian
        """
        itinerary = []
        current_lat, current_lon = start_lat, start_lon
        
        # Membagi budget per slot aktivitas
        budget_per_slot = total_budget // len(query_list)
        
        print(f"\n✨ MEMBUAT RUTE ITINERARY OTOMATIS ✨")
        print(f"Start Point: Lat {start_lat}, Lon {start_lon}")
        
        for i, activity in enumerate(query_list):
            # Memanggil pipeline dari engine_final.py
            # Kita set top_n=1 karena kita hanya butuh 1 destinasi terbaik per slot
            hasil = self.engine.run_pipeline(activity, budget_per_slot, current_lat, current_lon, top_n=1)
            
            if not hasil.empty:
                dest = hasil.iloc[0]
                itinerary.append(dest)
                
                # UPDATE LOKASI: Destinasi sekarang menjadi titik awal slot berikutnya
                current_lat, current_lon = dest['Lat'], dest['Long']
                
                print(f"\n[Slot {i+1}] Aktivitas: {activity}")
                print(f"Destinasi: {dest['Place_Name']}")
                print(f"Jarak dari titik sebelumnya: {dest['Jarak']:.2f} Km")
            else:
                print(f"\n[Slot {i+1}] Aktivitas: {activity} (Tidak ditemukan tempat yang cocok)")
                
        return itinerary

if __name__ == "__main__":
    # Inisialisasi generator
    generator = ItineraryGenerator()
    
    # Kueri yang berurutan dari pagi sampai malam
    my_queries = [
        "wisata alam keluarga piknik", 
        "cafe cozy instagramable", 
        "makan siang legendaris enak", 
        "wisata alam santai sore", 
        "wisata malam lampu kota", 
        "cafe santai malam"
    ]
    
    # Contoh lokasi awal user (Surabaya)
    my_plan = generator.generate_itinerary(my_queries, -7.2662, 112.7836, 500000)