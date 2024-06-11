from flask import Flask, request, jsonify
import psycopg2
import os

app = Flask(__name__)

# Configuración de la base de datos
DB_HOST = os.getenv("DB_HOST")
DB_PORT = os.getenv("DB_PORT")
DB_USER = os.getenv("DB_USER")
DB_PASSWORD = os.getenv("DB_PASSWORD")
DB_NAME = os.getenv("DB_NAME")

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
    if check_db_connection():
        return jsonify({"message": "Conexión exitosa a la base de datos!"})
    else:
        return jsonify({"message": "Error al conectar a la base de datos"})

if __name__ == '__main__':
    app.run(debug=True)
