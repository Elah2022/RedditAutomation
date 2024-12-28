import praw
import time
import requests
import os
import random
import re
from collections import defaultdict
from datetime import datetime, timedelta
from collections import Counter
from config import RedditConfig


def inicializar_recursos():
    #iniciando recursos necesarios
    try:
        import nltk
        recursos_necesarios = [
            'punkt',
            'stopwords',
            'averaged_perceptron_tagger'
        ]
        
        for recurso in recursos_necesarios:
            try:
                nltk.download(recurso, quiet=True)
            except Exception as e:
                print(f"No se pudo descargar {recurso}: {e}")
        
        return True
    except Exception as e:
        print(f"Error al inicializar recursos: {e}")
        return False

class PostDatabase:
    def __init__(self, base_folder):
        
        #Inicializa la base de datos de posts usando el sistema de archivos
        #base_folder : Carpeta base donde se almacenan los posts
        
        self.base_folder = base_folder
        self.posts_cache = set()
        self._load_existing_posts()
    
    def _load_existing_posts(self):
        #Carga los nombres de todas las carpetas existentes como si fueran posts publicados
        try:
            if os.path.exists(self.base_folder):
                for item in os.listdir(self.base_folder):
                    if os.path.isdir(os.path.join(self.base_folder, item)):
                        self.posts_cache.add(item)
            print(f"Base de datos cargada: {len(self.posts_cache)} posts encontrados")
        except Exception as e:
            print(f"Error al cargar la base de datos: {e}")
    
    def post_exists(self, post_title):
        #Se verifica si una publicación ya existe en la base de datos
        sanitized_title = sanitize_filename(post_title)
        return sanitized_title in self.posts_cache
    
    def add_post(self, post_title):
        #Añade una nueva publicacion a la base de datos
        sanitized_title = sanitize_filename(post_title)
        self.posts_cache.add(sanitized_title)
        folder_path = os.path.join(self.base_folder, sanitized_title)
        if not os.path.exists(folder_path):
            os.makedirs(folder_path)

def analizar_palabras_clave(textos):
    #Palabras clave más comunes que no es necesario que aparezcan en el analisis
    try:
        texto_completo = ' '.join(textos).lower()
        
        stop_words = set([
            'the', 'be', 'to', 'of', 'and', 'a', 'in', 'that', 'have', 'i',
            'it', 'for', 'not', 'on', 'with', 'he', 'as', 'you', 'do', 'at',
            'this', 'but', 'his', 'by', 'from', 'el', 'la', 'los', 'las', 'de',
            'en', 'y', 'a', 'que', 'del', 'se', 'un', 'una', 'unos', 'unas'
        ])
        
        palabras = re.findall(r'\b\w+\b', texto_completo)
        palabras_significativas = [
            palabra for palabra in palabras 
            if (len(palabra) > 3 and 
                palabra not in stop_words and 
                not palabra.isdigit())
        ]
        
        contador = Counter(palabras_significativas)
        return contador.most_common(10)
    
    except Exception as e:
        print(f"Error en análisis de palabras clave: {e}")
        return []

def sanitize_filename(filename):
    #Convierte el título en un nombre de archivo válido
    filename = re.sub(r'[<>:"/\\|?*]', '', filename)
    filename = filename.strip()
    if len(filename) > 50:
        filename = filename[:47] + "..."
    return filename

def create_folder(folder_name):
    #Crea una carpeta si no existe
    if not os.path.exists(folder_name):
        os.makedirs(folder_name)
    return folder_name

def obtener_mis_subreddits(reddit):
    #Obtiene la lista de subreddits a los que estás suscrito
    mis_subreddits = []
    try:
        for subreddit in reddit.user.subreddits(limit=None):
            mis_subreddits.append(subreddit.display_name)
        print(f"Subreddits encontrados: {len(mis_subreddits)}")
        return mis_subreddits
    except Exception as e:
        print(f"Error al obtener subreddits: {e}")
        return []

def analizar_actividad_por_hora(timestamps):
    #Analiza las horas con mayor actividad
    horas_actividad = defaultdict(int)
    for ts in timestamps:
        hora = datetime.fromtimestamp(ts).hour
        horas_actividad[hora] += 1
    
    horas_ordenadas = sorted(horas_actividad.items(), key=lambda x: x[1], reverse=True)
    return horas_ordenadas

def obtener_estadisticas_subreddit(reddit, subreddit_name):
    # estadísticas de un subreddit
    try:
        subreddit = reddit.subreddit(subreddit_name)
        stats = {
            'nombre': subreddit_name,
            'suscriptores': subreddit.subscribers,
            'activos': subreddit.active_user_count,
            'creacion': datetime.fromtimestamp(subreddit.created_utc),
            'posts_24h': [],
            'posts_semana': [],
            'timestamps': [],
            'titulos': [],
            'karma_total': 0,
            'comentarios_total': 0
        }

        tiempo_actual = datetime.now()
        for submission in subreddit.new(limit=1000):
            tiempo_post = datetime.fromtimestamp(submission.created_utc)
            tiempo_diff = tiempo_actual - tiempo_post
            
            stats['timestamps'].append(submission.created_utc)
            stats['titulos'].append(submission.title)
            stats['karma_total'] += submission.score
            stats['comentarios_total'] += submission.num_comments

            if tiempo_diff <= timedelta(days=1):
                stats['posts_24h'].append(submission)
            if tiempo_diff <= timedelta(days=7):
                stats['posts_semana'].append(submission)

        return stats
    except Exception as e:
        print(f"Error al obtener estadísticas de r/{subreddit_name}: {e}")
        return None

def analizar_tendencias(reddit):
    #Analiza las tendencias en todas las comunidades suscritas
    tendencias = defaultdict(dict)
    mis_subreddits = obtener_mis_subreddits(reddit)
    
    print("\nAnalizando tendencias en todas las comunidades...")
    for subreddit_name in mis_subreddits:
        try:
            stats = obtener_estadisticas_subreddit(reddit, subreddit_name)
            if not stats:
                continue

            posts_por_dia = len(stats['posts_24h'])
            posts_por_semana = len(stats['posts_semana'])
            horas_activas = analizar_actividad_por_hora(stats['timestamps'])
            palabras_clave = analizar_palabras_clave(stats['titulos'])

            tendencias[subreddit_name] = {
                'estadisticas_basicas': {
                    'suscriptores': stats['suscriptores'],
                    'usuarios_activos': stats['activos'],
                    'edad_comunidad': (datetime.now() - stats['creacion']).days,
                    'karma_promedio': stats['karma_total'] / len(stats['timestamps']) if stats['timestamps'] else 0,
                    'comentarios_promedio': stats['comentarios_total'] / len(stats['timestamps']) if stats['timestamps'] else 0
                },
                'actividad': {
                    'posts_24h': posts_por_dia,
                    'posts_semana': posts_por_semana,
                    'posts_por_dia': posts_por_semana / 7 if posts_por_semana > 0 else 0,
                    'horas_mas_activas': horas_activas[:5]
                },
                'contenido': {
                    'palabras_clave': palabras_clave,
                    'posts_populares': sorted(
                        stats['posts_24h'], 
                        key=lambda x: x.score, 
                        reverse=True
                    )[:5] if stats['posts_24h'] else []
                }
            }

            print(f"\n=== Estadísticas para r/{subreddit_name} ===")
            print(f"Suscriptores: {stats['suscriptores']:,}")
            print(f"Usuarios activos: {stats['activos']:,}")
            print(f"Posts en últimas 24h: {posts_por_dia}")
            print(f"Promedio posts por día: {tendencias[subreddit_name]['actividad']['posts_por_dia']:.2f}")
            print("\nPalabras clave más comunes:")
            for palabra, freq in palabras_clave[:5]:
                print(f"- {palabra}: {freq} menciones")
            print("\nHoras más activas:")
            for hora, cantidad in horas_activas[:3]:
                print(f"- {hora}:00 hrs: {cantidad} posts")
            
            if stats['posts_24h']:
                print("\nPosts más populares (24h):")
                for post in tendencias[subreddit_name]['contenido']['posts_populares'][:3]:
                    print(f"- {post.title} (Score: {post.score})")

        except Exception as e:
            print(f"Error al analizar r/{subreddit_name}: {e}")
            continue
        
        time.sleep(2)
    
    return tendencias

def dar_likes_y_aprobar(reddit):
    #Función para dar likes a posts recientes y aprobar posts propios
    liked_posts = set()
    
    try:
        print("\nAprobando posts propios...")
        for submission in reddit.user.me().submissions.new(limit=None):
            try:
                submission.mod.approve()
                print(f"Post aprobado: {submission.title}")
                time.sleep(2)
            except Exception as e:
                print(f"Error al aprobar post: {e}")

        print("\nDando likes a posts recientes...")
        for subreddit in reddit.user.subreddits(limit=None):
            try:
                for submission in subreddit.new(limit=10):
                    if submission.id not in liked_posts:
                        submission.upvote()
                        liked_posts.add(submission.id)
                        print(f"Like dado a: {submission.title}")
                        time.sleep(2)
            except Exception as e:
                print(f"Error en subreddit {subreddit.display_name}: {e}")

    except Exception as e:
        print(f"Error en la función de likes y aprobación: {e}")

def republicar_contenido(reddit, submission, post_db):
    #Función para republicar un post
    try:
        if post_db.post_exists(submission.title):
            print(f"Post ya existente, omitiendo: {submission.title}")
            return False
            
        folder_name = sanitize_filename(submission.title)
        folder_path = os.path.join(post_db.base_folder, folder_name)
        
        if not os.path.exists(folder_path):
            os.makedirs(folder_path)

        if submission.url.endswith(('.jpg', '.png', '.gif')):
            filename = sanitize_filename(submission.title) + os.path.splitext(submission.url)[1]
            filepath = os.path.join(folder_path, filename)
            
            response = requests.get(submission.url)
            if response.status_code == 200:
                with open(filepath, 'wb') as f:
                    f.write(response.content)
                
                new_post = reddit.subreddit("u_" + reddit.user.me().name).submit_image(
                    title=submission.title,
                    image_path=filepath
                )
                new_post.mod.approve()
                print(f"Imagen guardada y republicada: {filepath}")
        else:
            new_post = reddit.subreddit("u_" + reddit.user.me().name).submit(
                title=submission.title,
                url=submission.url
            )
            new_post.mod.approve()
        
        post_db.add_post(submission.title)
        print(f"Republicado y aprobado: {submission.title}")
        return True

    except Exception as e:
        print(f"Error al republicar {submission.title}: {e}")
        return False

def main():
    print("Iniciando script de análisis de Reddit...")
    
    if not inicializar_recursos():
        print("Advertencia: Algunos recursos no pudieron inicializarse")
        print("El script continuará con funcionalidad limitada")

    reddit = praw.Reddit(
        client_id=RedditConfig.CLIENT_ID,
        client_secret=RedditConfig.CLIENT_SECRET,
        username=RedditConfig.USERNAME,
        password=RedditConfig.PASSWORD,
        user_agent=RedditConfig.USER_AGENT
    )

    try:
        print(f"Autenticado como: {reddit.user.me()}")
    except Exception as e:
        print(f"Error de autenticación: {e}")
        return

    base_folder = "reddit_downloads"
    post_db = PostDatabase(base_folder)

    while True:
        try:
            tendencias = analizar_tendencias(reddit)
            dar_likes_y_aprobar(reddit)
            
            print("\nIniciando proceso de republicación...")
            mis_subreddits = obtener_mis_subreddits(reddit)
            
            for subreddit_name in mis_subreddits:
                try:
                    subreddit = reddit.subreddit(subreddit_name)
                    posts_elegibles = []
                    
                    for submission in subreddit.hot(limit=10):
                        if (not post_db.post_exists(submission.title) and 
                            submission.score > 10 and 
                            not submission.stickied):
                            posts_elegibles.append(submission)
                    
                    if posts_elegibles:
                        submission = random.choice(posts_elegibles)
                        republicar_contenido(reddit, submission, post_db)
                
                except Exception as e:
                    print(f"Error al procesar r/{subreddit_name}: {e}")
                
                time.sleep(60)  # Esperar 1 minuto entre comunidades
            
            print("\nEsperando 30 minutos antes del siguiente ciclo...")
            time.sleep(1800)  # 30 minutos entre ciclos completos

        except Exception as e:
            print(f"Error general en el ciclo principal: {e}")
            time.sleep(60)

if __name__ == "__main__":
    main()