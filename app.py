from flask import Flask, render_template, request # 'request' es nuevo, para leer los filtros del usuario
import pandas as pd
import os

app = Flask(__name__)

# --- Función para cargar y preparar los datos ---
def cargar_y_preparar_datos():
    directorio_actual = os.path.dirname(__file__)
    ruta_csv = os.path.join(directorio_actual, 'books_toscrape_data.csv')
    try:
        df = pd.read_csv(ruta_csv)
        # LIMPIEZA DE PRECIOS: Convertir la columna 'price' a números
        # 1. Quitar el símbolo '£'
        # 2. Convertir a tipo float (número decimal)
        if 'price' in df.columns:
            df['price_numeric'] = df['price'].str.replace('£', '', regex=False).astype(float)
        else:
            # Si no hay columna 'price', creamos una numérica con ceros para evitar errores más adelante
            df['price_numeric'] = 0.0 
            
        return df
    except FileNotFoundError:
        return None
    except Exception as e:
        print(f"Error cargando o preparando datos: {e}") # Imprime el error en la consola de Flask
        return None

# --- Ruta principal de la aplicación ---
@app.route('/')
def mostrar_libros():
    df_libros_original = cargar_y_preparar_datos()

    if df_libros_original is None:
        return "Error: El archivo 'books_toscrape_data.csv' no fue encontrado o hubo un error al cargarlo. Asegúrate de ejecutar primero el script de scraping."

    # Copiamos el DataFrame para no modificar el original con cada filtro/orden
    df_libros_filtrados = df_libros_original.copy()

    # --- Obtener categorías únicas para el dropdown de filtro ---
    # Usamos 'N/A' si la columna no existe o está vacía para evitar errores
    categorias_unicas = sorted(df_libros_original['category'].dropna().unique().tolist()) if 'category' in df_libros_original.columns else []


    # --- Aplicar filtro por categoría ---
    categoria_seleccionada = request.args.get('category_filter') # Obtiene el valor del filtro del URL
    if categoria_seleccionada and categoria_seleccionada != "": # Si se seleccionó una categoría y no está vacía
        df_libros_filtrados = df_libros_filtrados[df_libros_filtrados['category'] == categoria_seleccionada]

    # --- Aplicar ordenamiento ---
    ordenar_por = request.args.get('sort_by') # Obtiene el valor del parámetro de orden del URL
    if ordenar_por == 'price_asc':
        df_libros_filtrados = df_libros_filtrados.sort_values(by='price_numeric', ascending=True)
    elif ordenar_por == 'price_desc':
        df_libros_filtrados = df_libros_filtrados.sort_values(by='price_numeric', ascending=False)
    # Puedes añadir más opciones de ordenamiento aquí (ej. por título)

    # Convierte el DataFrame (posiblemente filtrado y ordenado) a lista de diccionarios
    lista_de_libros = df_libros_filtrados.to_dict(orient='records')
    
    return render_template('index.html', 
                           libros=lista_de_libros, 
                           categorias=categorias_unicas,
                           categoria_actual=categoria_seleccionada) # Pasamos la categoría seleccionada para el dropdown

if __name__ == '__main__':
    app.run(debug=True)