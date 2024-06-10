from flask import Flask, request, jsonify
import psycopg2
import os

app = Flask(__name__)

# Configuración de la base de datos
DB_HOST = os.getenv("http://tics.cpuae6qmuvit.us-east-2.rds.amazonaws.com/")
DB_NAME = os.getenv("tics")
DB_USER = os.getenv("postgres")
DB_PASSWORD = os.getenv("postgresql")

def get_db_connection():
    conn = psycopg2.connect(
        host=DB_HOST,
        database=DB_NAME,
        user=DB_USER,
        password=DB_PASSWORD
    )
    return conn

@app.route('/data', methods=['GET'])
def get_data():
    param = request.args.get('param', 'ph')
    period = request.args.get('period', 'daily')

    conn = get_db_connection()
    cursor = conn.cursor()
    
    query = "SELECT timestamp, {} FROM sensor_data WHERE period = %s ORDER BY timestamp".format(param)
    cursor.execute(query, (period,))
    data = cursor.fetchall()

    cursor.close()
    conn.close()

    return jsonify(data)

if __name__ == '__main__':
    app.run(debug=True)
