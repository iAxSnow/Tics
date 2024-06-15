from flask import Flask, request, jsonify
import psycopg2
import os
from dotenv import load_dotenv
from decimal import Decimal
from datetime import datetime

load_dotenv()  # Cargar las variables de entorno desde el archivo .env

app = Flask(__name__)

# Configuración de la base de datos
DB_HOST = os.getenv("DB_HOST")
DB_PORT = os.getenv("DB_PORT")
DB_NAME = os.getenv("DB_NAME")
DB_USER = os.getenv("DB_USER")
DB_PASSWORD = os.getenv("DB_PASSWORD")

def get_db_connection():
    try:
        conn = psycopg2.connect(
            host=DB_HOST,
            port=DB_PORT,
            database=DB_NAME,
            user=DB_USER,
            password=DB_PASSWORD
        )
        print("Conexión a la base de datos exitosa!")
        return conn
    except psycopg2.Error as e:
        print("Error connecting to PostgreSQL:", e)
        return None

def convert_decimal_to_float(data):
    if isinstance(data, list):
        return [convert_decimal_to_float(i) for i in data]
    elif isinstance(data, tuple):
        return tuple(convert_decimal_to_float(i) for i in data)
    elif isinstance(data, dict):
        return {key: convert_decimal_to_float(value) for key, value in data.items()}
    elif isinstance(data, Decimal):
        return float(data)
    else:
        return data

@app.route('/datausuarios', methods=['GET'])
def get_datausuarios():
    conn = get_db_connection()
    if conn:
        cur = conn.cursor()
        cur.execute('SELECT * FROM usuarios')
        rows = cur.fetchall()
        cur.close()
        conn.close()
        converted_rows = convert_decimal_to_float(rows)
        return jsonify(converted_rows)
    else:
        return jsonify({"error": "No se pudo conectar a la base de datos"})

@app.route('/datalecturas', methods=['GET'])
def get_datalecturas():
    conn = get_db_connection()
    if conn:
        cur = conn.cursor()
        cur.execute('SELECT * FROM lecturas_sensor')
        rows = cur.fetchall()
        cur.close()
        conn.close()
        converted_rows = convert_decimal_to_float(rows)
        return jsonify(converted_rows)
    else:
        return jsonify({"error": "No se pudo conectar a la base de datos"})

def create_partition_if_not_exists(conn, month, year):
    try:
        cur = conn.cursor()
        table_name = f"part_{year}_{month:02d}"
        # Verificar si la partición ya existe
        cur.execute("SELECT EXISTS (SELECT FROM pg_tables WHERE schemaname = 'public' AND tablename = %s)", (table_name,))
        partition_exists = cur.fetchone()[0]
        if not partition_exists:
            start_date = f'{year}-{month:02d}-01 00:00:00'
            end_date = f'{year}-{(month % 12) + 1:02d}-01 00:00:00'
            
            # Crear tabla intermedia temporal
            cur.execute("CREATE TEMP TABLE temp_lecturas AS TABLE lecturas_sensor_default WITH NO DATA")

            # Mover datos que cumplen con las restricciones de la nueva partición a la tabla temporal
            cur.execute(f"""
                INSERT INTO temp_lecturas (id, id_sensor, fecha_hora, ph, humedad, temperatura, usuario_rut)
                SELECT id, id_sensor, fecha_hora, ph, humedad, temperatura, usuario_rut
                FROM lecturas_sensor_default
                WHERE fecha_hora >= %s AND fecha_hora < %s
            """, (start_date, end_date))

            # Eliminar los datos movidos de la partición por defecto
            cur.execute(f"""
                DELETE FROM lecturas_sensor_default
                WHERE fecha_hora >= %s AND fecha_hora < %s
            """, (start_date, end_date))
            
            # Crear la nueva partición
            cur.execute(f"""
                CREATE TABLE {table_name} PARTITION OF lecturas_sensor
                FOR VALUES FROM (%s) TO (%s)
            """, (start_date, end_date))

            # Volver a insertar los datos desde la tabla temporal a la tabla particionada
            cur.execute(f"""
                INSERT INTO lecturas_sensor
                SELECT * FROM temp_lecturas
            """)
            
            conn.commit()
        cur.close()
    except Exception as e:
        print("Error al crear la partición:", e)
        conn.rollback()

@app.route('/postdata', methods=['POST'])
def post_data():
    data = request.json
    if not data:
        return jsonify({"error": "No se proporcionaron datos"}), 400
    
    conn = get_db_connection()
    if conn:
        try:
            # Crear la partición si no existe
            current_date_time = datetime.now()
            current_month = current_date_time.month
            current_year = current_date_time.year
            create_partition_if_not_exists(conn, current_month, current_year)
            
            cur = conn.cursor()
            for item in data:
                id_sensor = item.get('id_sensor')
                ph = item.get('ph')
                humedad = item.get('humedad')
                temperatura = item.get('temperatura')
                usuario_rut = item.get('usuario_rut')
                
                cur.execute('INSERT INTO lecturas_sensor (id_sensor, fecha_hora, ph, humedad, temperatura, usuario_rut) VALUES (%s, CURRENT_TIMESTAMP, %s, %s, %s, %s)',
                            (id_sensor, ph, humedad, temperatura, usuario_rut))
                
            conn.commit()
            return jsonify({"message": "Datos insertados correctamente"}), 200
        except Exception as e:
            print("Error al insertar datos en la base de datos:", e)
            conn.rollback()
            return jsonify({"error": "No se pudieron insertar los datos"}), 500
        finally:
            cur.close()
            conn.close()
    else:
        return jsonify({"error": "No se pudo conectar a la base de datos"}), 500





@app.route('/login', methods=['POST'])
def authenticate():
    data = request.json
    if not data or 'rut' not in data or 'password' not in data:
        return jsonify({"error": "RUT o contraseña no proporcionados"}), 400
    
    conn = get_db_connection()
    if conn:
        try:
            cur = conn.cursor()
            cur.execute('SELECT rut, usuario, email, contraseña FROM usuarios WHERE rut = %s', (data['rut'],))
            user = cur.fetchone()
            if user:
                stored_password = user[3]  # La contraseña encriptada almacenada en la base de datos
                # Verificar la contraseña usando la función crypt de PostgreSQL
                cur.execute("SELECT crypt(%s, %s) = %s", (data['password'], stored_password, stored_password))
                is_valid = cur.fetchone()[0]
                if is_valid:
                    return jsonify({
                        "message": "Inicio de sesión exitoso",
                        "user": {
                            "rut": user[0],
                            "usuario": user[1],
                            "email": user[2]
                        }
                    }), 200
                else:
                    return jsonify({"error": "RUT o contraseña incorrectos"}), 401
            else:
                return jsonify({"error": "Usuario no encontrado"}), 404
        except Exception as e:
            print("Error al autenticar:", e)
            return jsonify({"error": "Error al autenticar"}), 500
        finally:
            cur.close()
            conn.close()
    else:
        return jsonify({"error": "No se pudo conectar a la base de datos"}), 500

    
    


@app.route('/')
def index():
    return jsonify({"message": "Hello, World!"})

if __name__ == '__main__':
    app.run(debug=True)
