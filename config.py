# config.py
class RedditConfig:
    # Credenciales de la API de Reddit
    CLIENT_ID = "TU_CLIENT_ID"
    CLIENT_SECRET = "TU_CLIENT_SECRET"
    USERNAME = "TU_USERNAME"
    PASSWORD = "TU_PASSWORD"
    USER_AGENT = "RedditBot/1.0"

    # Configuración de comportamiento
    SUBREDDIT_LIMIT = 10          # Número máximo de subreddits a analizar
    POST_SCORE_THRESHOLD = 10     # Puntuación mínima para republicar
    WAIT_TIME = 1800             # Tiempo de espera entre ciclos (30 minutos)
    POST_DELAY = 60              # Tiempo entre posts (1 minuto)
    
    # Configuración de almacenamiento
    BASE_FOLDER = "reddit_downloads"  # Carpeta para guardar contenido
    
    # Filtros de contenido
    ALLOWED_EXTENSIONS = ('.jpg', '.png', '.gif')  # Extensiones permitidas
    MAX_TITLE_LENGTH = 50        # Longitud máxima del título

