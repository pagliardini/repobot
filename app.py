from flask import Flask, render_template, request
import pyodbc
import pandas as pd
from datetime import datetime, timedelta

app = Flask(__name__)

def connect_to_db():
    server = '26.146.244.52'
    database = 'Kiosco'
    username = 'sa'
    password = 'nomeacuerdo.86'
    connection_string = f'DRIVER={{ODBC Driver 17 for SQL Server}};SERVER={server};DATABASE={database};UID={username};PWD={password}'
    return pyodbc.connect(connection_string)

def get_sold_products_count(product_id, start_date, end_date): # cantidad de productos vendidos entre fechas
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

def get_top_sold_products(start_date, end_date): # top productos vendidos entre fechas
    conn = connect_to_db()

    query = """
    SELECT TOP 10 P.Descripcion, SUM(DF.Cantidad) AS Total_Vendido
    FROM Detalle_Factura DF
    JOIN Facturas F ON DF.Id_Venta = F.Id_Factura
    JOIN Productos P ON DF.Id = P.Id
    WHERE CONVERT(date, F.Fecha, 103) BETWEEN CONVERT(date, ?, 103) AND CONVERT(date, ?, 103)
    GROUP BY P.Descripcion
    ORDER BY Total_Vendido DESC
    """

    params = (start_date, end_date)
    df = pd.read_sql_query(query, conn, params=params)

    conn.close()

    return df

def get_products_no_movements(days):
    conn = connect_to_db()

    date_threshold = (datetime.now() - timedelta(days=days)).strftime('%d/%m/%Y')

    query = """
    SELECT P.Descripcion
    FROM Productos P
    LEFT JOIN (
        SELECT DISTINCT DF.Id
        FROM Detalle_Factura DF
        JOIN Facturas F ON DF.Id_Venta = F.Id_Factura
        WHERE CONVERT(date, F.Fecha, 103) > CONVERT(date, ?, 103)
    ) AS RecentSales ON P.Id = RecentSales.Id
    WHERE RecentSales.Id IS NULL
    """

    params = (date_threshold,)
    df = pd.read_sql_query(query, conn, params=params)

    conn.close()

    return df

@app.route('/', methods=['GET', 'POST'])
def index():
    total_vendido = None
    top_products = None
    no_movement_products = None
    error = None
    if request.method == 'POST':
        if 'product_id' in request.form and 'start_date' in request.form and 'end_date' in request.form:
            product_id = request.form['product_id']
            start_date = request.form['start_date']
            end_date = request.form['end_date']

            try:
                start_date = datetime.strptime(start_date, '%Y-%m-%d').strftime('%d/%m/%Y')
                end_date = datetime.strptime(end_date, '%Y-%m-%d').strftime('%d/%m/%Y')
            except ValueError:
                error = "Formato de fecha inválido. Use el selector de fecha para seleccionar las fechas."

            if not error:
                total_vendido = get_sold_products_count(product_id, start_date, end_date)
        
        elif 'top_products' in request.form and 'start_date' in request.form and 'end_date' in request.form:
            start_date = request.form['start_date']
            end_date = request.form['end_date']

            try:
                start_date = datetime.strptime(start_date, '%Y-%m-%d').strftime('%d/%m/%Y')
                end_date = datetime.strptime(end_date, '%Y-%m-%d').strftime('%d/%m/%Y')
            except ValueError:
                error = "Formato de fecha inválido. Use el selector de fecha para seleccionar las fechas."

            if not error:
                top_products = get_top_sold_products(start_date, end_date)
        
        elif 'no_movement_products' in request.form and 'days_no_movement' in request.form:
            days = int(request.form['days_no_movement'])
            no_movement_products = get_products_no_movements(days)

    return render_template('index.html', total_vendido=total_vendido, top_products=top_products, no_movement_products=no_movement_products, error=error)

if __name__ == '__main__':
    app.run(debug=True)
