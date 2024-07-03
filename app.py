from flask import Flask, render_template, request
import pyodbc
import pandas as pd
from datetime import datetime

app = Flask(__name__)

def connect_to_db():
    server = '26.146.244.52'
    database = 'Kiosco'
    username = 'sa'
    password = 'nomeacuerdo.86'
    connection_string = f'DRIVER={{ODBC Driver 17 for SQL Server}};SERVER={server};DATABASE={database};UID={username};PWD={password}'
    return pyodbc.connect(connection_string)

def get_sold_products_count(product_id, start_date, end_date):
    conn = connect_to_db()

    query = """
    SELECT SUM(DF.Cantidad) AS Total_Vendido
    FROM Detalle_Factura DF
    JOIN Facturas F ON DF.Id_Venta = F.Id_Factura
    JOIN Productos P ON DF.Id = P.Id
    WHERE (P.Id_Producto = ? OR P.Id_Producto1 = ? OR P.Id_Producto2 = ? OR P.Id_Producto3 = ?)
    AND CONVERT(date, F.Fecha, 103) BETWEEN CONVERT(date, ?, 103) AND CONVERT(date, ?, 103)
    """

    params = (product_id, product_id, product_id, product_id, start_date, end_date)
    df = pd.read_sql_query(query, conn, params=params)

    conn.close()

    if df.empty or df.iloc[0]['Total_Vendido'] is None:
        return 0
    else:
        return df.iloc[0]['Total_Vendido']

@app.route('/', methods=['GET', 'POST'])
def index():
    total_vendido = None
    error = None
    if request.method == 'POST':
        product_id = request.form['product_id']
        start_date = request.form['start_date']
        end_date = request.form['end_date']

        # Convertir fechas de 'yyyy-mm-dd' a 'dd/mm/yyyy'
        try:
            start_date = datetime.strptime(start_date, '%Y-%m-%d').strftime('%d/%m/%Y')
            end_date = datetime.strptime(end_date, '%Y-%m-%d').strftime('%d/%m/%Y')
        except ValueError:
            error = "Formato de fecha inválido. Use el selector de fecha para seleccionar las fechas."

        if not error:
            total_vendido = get_sold_products_count(product_id, start_date, end_date)
    
    return render_template('index.html', total_vendido=total_vendido, error=error)

if __name__ == '__main__':
    app.run(debug=True)
