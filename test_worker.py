import requests

# Un ID único para el buzón (en el proyecto real esto sería un hash)
url = "http://localhost:8787/buzon/mi_id_secreto_123"
datos_cifrados = b"Este es un mensaje super secreto que se autodestruye"

print("=== PRUEBA DEL BUZÓN MUERTO ===\n")

# 1. Guardar en el buzón (PUT)
print("1. Guardando mensaje en el buzón...")
r = requests.put(url, data=datos_cifrados)
print(f"   Status: {r.status_code} - {r.text}\n")

# 2. Leer el buzón (GET) - Primera vez
print("2. Leyendo el buzón (primera vez)...")
r = requests.get(url)
print(f"   Status: {r.status_code}")
print(f"   Contenido: {r.content}\n")

# 3. Intentar leer de nuevo (GET) - Segunda vez
print("3. Intentando leer de nuevo (debe dar 404 porque se borró)...")
r = requests.get(url)
print(f"   Status: {r.status_code} - {r.text}\n")