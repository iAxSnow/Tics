from flask import Flask, jsonify
import psycopg2
import os

app = Flask(__name__)

# Configuración de la base de datos
DB_HOST = os.getenv("DB_HOST")
DB_NAME = os.getenv("DB_NAME")
DB_USER = os.getenv("DB_USER")
DB_PASSWORD = os.getenv("DB_PASSWORD")

def check_db_connection():
    try:
        conn = psycopg2.connect(
            host=DB_HOST,
            database=DB_NAME,
            user=DB_USER,
            password=DB_PASSWORD
        )
        conn.close()
        return True
    except psycopg2.Error as e:
        print("Error connecting to PostgreSQL:", e)
        return False

@app.route('/check_connection', methods=['GET'])
def check_connection():
    if check_db_connection():
        return jsonify({"message": "Successfully connected to the database"})
    else:
        return jsonify({"message": "Failed to connect to the database"}), 500

if __name__ == '__main__':
    app.run(debug=True)
