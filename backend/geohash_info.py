from geopy.geocoders import Nominatim
from geopy.point import Point

def get_location_info(lat, lon):
    geolocator = Nominatim(user_agent="geocrypt")
    location = geolocator.reverse(Point(lat, lon))
    return {
        "address": location.address,
        "latitude": lat,
        "longitude": lon
    }

if __name__ == "__main__":
    # Coordenadas del centro de San Rafael, Mendoza
    lat = -34.6175  # Latitud sur
    lon = -68.3333  # Longitud oeste
    
    info = get_location_info(lat, lon)
    print(f"Ubicación: {info['address']}")
    print(f"Latitud: {info['latitude']}° S")
    print(f"Longitud: {info['longitude']}° W") 