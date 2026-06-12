import psycopg

try:
    # O Psycopg 3 conecta e gerencia o encoding automaticamente
    conn = psycopg.connect(
        host="127.0.0.1",
        port=5433,
        user="prospect",
        password="prospect123",
        dbname="prospect"
    )

    print("✅ Conectado com sucesso usando Psycopg 3!")
    
    # Fecha a conexão de forma limpa
    conn.close()

except Exception as erro:
    print(f"❌ Erro ao conectar: {erro}")