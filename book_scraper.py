import requests
from bs4 import BeautifulSoup
import pandas as pd
import time
from urllib.parse import urljoin # Para construir URLs absolutas correctamente

def scrape_books_toscrape():
    """
    Realiza web scraping del sitio http://books.toscrape.com/ para extraer
    información de los libros (título, precio, disponibilidad, categoría)
    y la guarda en un archivo CSV.
    """
    
    base_url = "http://books.toscrape.com/"
    catalogue_start_url = urljoin(base_url, "catalogue/page-1.html") # URL de inicio del catálogo
    
    all_books_data = []
    current_page_url = catalogue_start_url
    page_number = 1

    print("Iniciando el scraping de books.toscrape.com...")

    while current_page_url:
        print(f"Procesando página: {current_page_url}")
        
        try:
            response = requests.get(current_page_url)
            response.raise_for_status()  # Lanza una excepción para códigos de error HTTP (4xx o 5xx)
        except requests.exceptions.RequestException as e:
            print(f"Error al obtener la página {current_page_url}: {e}")
            break # Termina el bucle si no se puede acceder a la página

        soup = BeautifulSoup(response.content, 'html.parser')
        
        # Encontrar todos los artículos de libros en la página actual
        books_on_page = soup.find_all('article', class_='product_pod')
        
        if not books_on_page:
            if page_number == 1: # Si no hay libros en la primera página, algo está muy mal
                print("No se encontraron libros en la primera página. Verifique la estructura del sitio o la URL.")
            else: # Probablemente llegamos al final si no es la primera página
                print("No se encontraron más libros en esta página.")
            break 

        for book_tag in books_on_page:
            book_data = {}
            
            # 1. Título del libro
            title_tag = book_tag.find('h3').find('a')
            book_data['title'] = title_tag['title'].strip() if title_tag and 'title' in title_tag.attrs else 'N/A'
            
            # 2. URL relativa del libro y construcción de URL absoluta para detalles
            relative_book_url = title_tag['href'].strip() if title_tag and 'href' in title_tag.attrs else None
            
            if not relative_book_url:
                print(f"  Advertencia: No se pudo encontrar la URL para el libro: {book_data['title']}")
                book_detail_url = None
            else:
                # Las URLs relativas de los libros son relativas a la página actual del catálogo
                book_detail_url = urljoin(current_page_url, relative_book_url)
            
            book_data['url'] = book_detail_url

            # 3. Precio del libro
            price_tag = book_tag.find('p', class_='price_color')
            book_data['price'] = price_tag.text.strip() if price_tag else 'N/A'
            
            # 4. Disponibilidad del libro
            availability_tag = book_tag.find('p', class_='instock availability')
            book_data['availability'] = availability_tag.text.strip() if availability_tag else 'N/A'
            
            # 5. Categoría del libro (obtenida de la página de detalles del libro)
            book_data['category'] = 'N/A' # Valor por defecto
            if book_detail_url:
                try:
                    print(f"  Obteniendo detalles de: {book_data['title'][:50]}...") # Acortar título largo para log
                    book_response = requests.get(book_detail_url)
                    book_response.raise_for_status()
                    book_soup = BeautifulSoup(book_response.content, 'html.parser')
                    
                    # La categoría está en el breadcrumb (usualmente el segundo enlace <a>)
                    # Ejemplo: Home > Poetry > A Light in the Attic
                    breadcrumb_ul = book_soup.find('ul', class_='breadcrumb')
                    if breadcrumb_ul:
                        breadcrumb_lis = breadcrumb_ul.find_all('li')
                        # El breadcrumb es Home > CategoryName > BookTitle(active)
                        # Así que el elemento en el índice 1 (el segundo <li>) contiene el enlace a la categoría
                        if len(breadcrumb_lis) >= 3 and breadcrumb_lis[1].find('a'):
                            book_data['category'] = breadcrumb_lis[1].find('a').text.strip()
                        else:
                            print(f"    Advertencia: Estructura de breadcrumb inesperada para {book_data['title']}")
                            book_data['category'] = 'N/A (estructura breadcrumb)'
                    else:
                        print(f"    Advertencia: No se encontró breadcrumb para {book_data['title']}")
                        book_data['category'] = 'N/A (sin breadcrumb)'
                    
                    time.sleep(0.1) # Pequeña pausa para ser cortés con el servidor
                except requests.exceptions.RequestException as e_detail:
                    print(f"    Error al obtener detalles para {book_data['title']}: {e_detail}")
                    book_data['category'] = 'Error al obtener categoría'
                except AttributeError as e_attr: # Si find() devuelve None y se intenta acceder a un atributo
                    print(f"    Error al parsear categoría (AttributeError) para {book_data['title']}: {e_attr}")
                    book_data['category'] = 'Error al parsear categoría'
            
            all_books_data.append(book_data)
            # print(f"    Extraído: Título='{book_data['title']}', Precio='{book_data['price']}', Disp='{book_data['availability']}', Cat='{book_data['category']}'")

        # Buscar el enlace a la siguiente página
        next_page_tag = soup.find('li', class_='next')
        if next_page_tag and next_page_tag.find('a'):
            next_page_relative_url = next_page_tag.find('a')['href']
            current_page_url = urljoin(current_page_url, next_page_relative_url) # Construir URL absoluta para la siguiente página
            page_number += 1
        else:
            print("No se encontró enlace a la siguiente página. Fin del scraping de páginas.")
            current_page_url = None # Detener el bucle
        
        time.sleep(0.5) # Pausa entre el procesamiento de cada página principal

    print(f"\nScraping finalizado. Total de libros extraídos: {len(all_books_data)}")

    if not all_books_data:
        print("No se extrajeron datos. El script terminará.")
        return

    # Convertir los datos a un DataFrame de Pandas
    df_books = pd.DataFrame(all_books_data)
    
    # Mostrar una muestra de los datos y la información del DataFrame
    print("\n--- Muestra de los datos extraídos ---")
    print(df_books.head())
    
    print("\n--- Información del DataFrame ---")
    df_books.info()
    
    # Guardar los datos en un archivo CSV
    csv_filename = "books_toscrape_data.csv"
    try:
        df_books.to_csv(csv_filename, index=False, encoding='utf-8')
        print(f"\nLos datos han sido guardados exitosamente en el archivo: {csv_filename}")
    except IOError:
        print(f"\nError: No se pudo guardar el archivo CSV en {csv_filename}. Verifique los permisos.")
    except Exception as e:
        print(f"\nOcurrió un error inesperado al guardar el CSV: {e}")

if __name__ == '__main__':
    scrape_books_toscrape()