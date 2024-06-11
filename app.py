from flask import Flask, request, jsonify
import psycopg2
import os
from dotenv import load_dotenv

load_dotenv()  # Cargar las variables de entorno desde el archivo .env

app = Flask(__name__)

# Configuración de la base de datos
DB_HOST = os.getenv("DB_HOST")
DB_PORT = os.getenv("DB_PORT")
DB_NAME = os.getenv("DB_NAME")
DB_USER = os.getenv("DB_USER")
DB_PASSWORD = os.getenv("DB_PASSWORD")

def check_db_connection():
    try:
        conn = psycopg2.connect(
            host=DB_HOST,
            port=DB_PORT,
            database=DB_NAME,
            user=DB_USER,
            password=DB_PASSWORD
        )
        conn.close()
        print("Conexión a la base de datos exitosa!")
        return True
    except psycopg2.Error as e:
        print("Error connecting to PostgreSQL:", e)
        return False

@app.route('/')
def index():
    return jsonify({"message": "Hello, World!"})

if __name__ == '__main__':
    app.run(debug=True)
