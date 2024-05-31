import requests
import urllib.parse

route_url = "https://graphhopper.com/api/1/route?"
key = "3afb24aa-4c7b-4fec-8e4b-89f8d63b1d63"  # Reemplaza esto con tu clave API

def geocoding(location, key):
    geocode_url = "https://graphhopper.com/api/1/geocode?"
    url = geocode_url + urllib.parse.urlencode({"q": location, "limit": "1", "key": key})
   
    try:
        replydata = requests.get(url)
        replydata.raise_for_status()  # Verificar si la solicitud fue exitosa
        json_data = replydata.json()

        if 'hits' in json_data and len(json_data['hits']) > 0:
            lat = json_data["hits"][0]["point"]["lat"]
            lng = json_data["hits"][0]["point"]["lng"]
            return 200, lat, lng
        else:
            print(f"No se encontraron resultados para {location}.")
            return 404, None, None
    except requests.exceptions.RequestException as e:
        print(f"Error en la solicitud HTTP: {e}")
        return replydata.status_code if 'replydata' in locals() else 500, None, None

def calcular_distancia_duracion_indicaciones(origen, destino, key):
    # Geocodificar origen y destino
    orig_status, orig_lat, orig_lng = geocoding(origen, key)
    dest_status, dest_lat, dest_lng = geocoding(destino, key)

    if orig_status != 200 or dest_status != 200:
        print("Error en la geocodificación. No se puede calcular la distancia y duración.")
        return None, None, None

    # Construir la URL de la ruta entre origen y destino
    route_params = {
        "point": [f"{orig_lat},{orig_lng}", f"{dest_lat},{dest_lng}"],
        "vehicle": "car",  # Modo de transporte: coche
        "key": key,
        "instructions": "true",  # Incluir instrucciones detalladas
        "locale": "es"  # Instrucciones en español
    }
   
    try:
        route_response = requests.get(route_url, params=route_params)
        route_response.raise_for_status()
        route_data = route_response.json()

        if 'paths' not in route_data or len(route_data['paths']) == 0:
            print("No se encontró una ruta válida entre los puntos.")
            return None, None, None

        # Extraer la distancia y duración de la ruta
        distance_meters = route_data['paths'][0]['distance']
        duration_seconds = route_data['paths'][0]['time'] / 1000  # Convertir de milisegundos a segundos
        instrucciones = route_data['paths'][0]['instructions']  # Instrucciones de la ruta
       
        distance_km = distance_meters / 1000  # Convertir a kilómetros
        duration_hms = convertir_duracion(duration_seconds)
       
        return distance_km, duration_hms, instrucciones
    except requests.exceptions.RequestException as e:
        print(f"Error en la solicitud HTTP para la ruta: {e}")
        return None, None, None

def convertir_duracion(segundos):
    horas = int(segundos // 3600)
    minutos = int((segundos % 3600) // 60)
    segundos = int(segundos % 60)
    return f"{horas:02}:{minutos:02}:{segundos:02}"

def calcular_combustible(distancia, eficiencia):
    return distancia / eficiencia

def generar_narrativa(origen, destino, distancia, duracion, combustible, instrucciones):
    narrativa = (f"El viaje desde {origen} hasta {destino} cubre una distancia de aproximadamente {distancia:.2f} kilómetros. "
                 f"La duración estimada del viaje es de {duracion} (horas:minutos:segundos). "
                 f"Se requiere aproximadamente {combustible:.2f} litros de combustible para el viaje. "
                 "Aquí están las indicaciones detalladas:\n")
    for instruccion in instrucciones:
        distancia_instruccion = instruccion['distance'] / 1000  # Convertir a kilómetros
        narrativa += f"{instruccion['text']} durante {distancia_instruccion:.2f} kilómetros.\n"
    return narrativa

# Bucle principal para solicitar origen y destino hasta que el usuario escriba "q"
while True:
    print("\nMenú de opciones:")
    print("1. Medir distancia entre dos ciudades")
    print("2. Mostrar duración del viaje")
    print("3. Mostrar combustible requerido para el viaje")
    print("4. Imprimir narrativa del viaje")
    print("q. Salir")
    
    choice = input("Seleccione una opción: ").strip().lower()
    
    if choice == 'q':
        break
    elif choice in {'1', '2', '3', '4'}:
        origen = input("Ingrese el origen (o escriba 'q' para terminar): ")
        if origen.lower() == "q":
            break
        destino = input("Ingrese el destino (o escriba 'q' para terminar): ")
        if destino.lower() == "q":
            break

        # Calcular la distancia, duración y obtener las indicaciones entre el origen y el destino proporcionados por el usuario
        distancia, duracion, instrucciones = calcular_distancia_duracion_indicaciones(origen, destino, key)

        if distancia is not None and duracion is not None and instrucciones is not None:
            if choice == '3':
                try:
                    eficiencia = float(input("Ingrese cuántos kilómetros hace su vehículo por litro de combustible: "))
                except ValueError:
                    print("Valor no válido para la eficiencia de combustible. Intente de nuevo.")
                    continue
                combustible = calcular_combustible(distancia, eficiencia)
                print("---------------------------------------------------------------")
                print(f"Combustible requerido para el viaje: {combustible:.2f} litros")
                print("---------------------------------------------------------------")
            elif choice == '1':
                print("---------------------------------------------------------------")
                print(f"Distancia entre {origen} y {destino}: {distancia:.2f} km")
                print("---------------------------------------------------------------")
            elif choice == '2':
                print("---------------------------------------------------------------")
                print(f"Duración del viaje: {duracion}")
                print("---------------------------------------------------------------")
            elif choice == '4':
                try:
                    eficiencia = float(input("Ingrese cuántos kilómetros hace su vehículo por litro de combustible (usado para la narrativa): "))
                except ValueError:
                    print("Valor no válido para la eficiencia de combustible. Intente de nuevo.")
                    continue
                combustible = calcular_combustible(distancia, eficiencia)
                narrativa = generar_narrativa(origen, destino, distancia, duracion, combustible, instrucciones)
                print("---------------------------------------------------------------")
                print(narrativa)
                print("---------------------------------------------------------------")
        else:
            print("Error en el cálculo de la ruta. Por favor, inténtelo de nuevo.")
    else:
        print("Opción no válida. Por favor, seleccione una opción del menú.")
