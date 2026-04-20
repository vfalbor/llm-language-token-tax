import tiktoken

SAMPLES = {
    "english":    "How do I connect to a PostgreSQL database from Python using psycopg2? I need connection pooling, retry on transient errors, and clean shutdown.",
    "spanish":    "¿Cómo me conecto a una base de datos PostgreSQL desde Python usando psycopg2? Necesito pooling de conexiones, reintentos ante errores transitorios y apagado limpio.",
    "french":     "Comment me connecter à une base de données PostgreSQL depuis Python avec psycopg2 ? Il me faut un pool de connexions, des retries et un arrêt propre.",
    "german":     "Wie verbinde ich mich mit einer PostgreSQL-Datenbank aus Python mit psycopg2? Ich brauche Connection-Pooling, Retries und sauberes Herunterfahren.",
    "portuguese": "Como me conecto a um banco PostgreSQL em Python usando psycopg2? Preciso de pool de conexões, retries e shutdown limpo.",
    "japanese":   "psycopg2 を使って Python から PostgreSQL に接続するには？ コネクションプール、一時的エラーの再試行、正常なシャットダウンが必要です。",
    "chinese":    "如何使用 psycopg2 从 Python 连接 PostgreSQL？我需要连接池、瞬时错误重试和干净关闭。",
    "arabic":     "كيف أتصل بقاعدة بيانات PostgreSQL من Python باستخدام psycopg2؟ أحتاج إلى تجمع اتصالات، وإعادة المحاولة، وإغلاق نظيف.",
}

for enc_name in ("cl100k_base", "o200k_base"):
    enc = tiktoken.get_encoding(enc_name)
    print(f"\n{enc_name}")
    baseline = None
    for lang, text in SAMPLES.items():
        n = len(enc.encode(text))
        baseline = baseline or n
        print(f"  {lang:<11} {n:4d} tokens  ({n/baseline:.2f}x vs EN)")
