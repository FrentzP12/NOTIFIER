import os
import asyncpg
import smtplib
from email.mime.text import MIMEText
from email.mime.multipart import MIMEMultipart
from datetime import datetime, timedelta

async def fetch_items_por_palabra_clave(fecha_inicio, fecha_fin, palabra_clave):
    """
    Realiza una consulta a la base de datos filtrando por una palabra clave específica.
    """
    dsn = os.getenv("DB_DSN")
    query = """
    SELECT * FROM buscar_items_multi_criterio(
        $1,
        NULL,
        NULL,
        $2,
        $3
    );
    """
    try:
        conn = await asyncpg.connect(dsn)
        rows = await conn.fetch(query, palabra_clave, fecha_inicio, fecha_fin)
        await conn.close()
        return rows
    except Exception as e:
        print(f"Error fetching data for '{palabra_clave}': {e}")
        return []

async def fetch_all_items(fecha_inicio, fecha_fin, palabras_clave):
    """
    Itera sobre las palabras clave y obtiene los resultados de cada una.
    """
    all_items = []
    for palabra_clave in palabras_clave:
        print(f"Buscando por palabra clave: {palabra_clave}")
        items = await fetch_items_por_palabra_clave(fecha_inicio, fecha_fin, palabra_clave)
        all_items.extend(items)  # Combina los resultados de todas las consultas
    return all_items

def format_date(fecha):
    """
    Formatea una fecha al formato DD/MM/YY.
    """
    return fecha.strftime('%d/%m/%y') if fecha else "N/A"

def generate_table_rows(items):
    """
    Genera filas en formato HTML para incluir en el correo.
    """
    table_rows = ""
    for item in items:
        fecha_formateada = format_date(item['fecha_ingreso'])
        table_rows += f"""
        <tr>
            <td>{item['comprador']}</td>
            <td>{item['nomenclatura']}</td>
            <td>{item['item']}</td>
            <td>{fecha_formateada}</td>
        </tr>
        """
    return table_rows

def send_email(subject, table_rows, recipients, fecha_inicio, fecha_fin, total_items):
    """
    Envía un correo electrónico con una tabla HTML de resultados.
    """
    sender_email = os.getenv("EMAIL_USER")
    sender_password = os.getenv("EMAIL_PASSWORD")
    
    smtp_server = "smtp.gmail.com"
    smtp_port = 587

    # Formatear las fechas del rango
    fecha_inicio_formateada = format_date(fecha_inicio)
    fecha_fin_formateada = format_date(fecha_fin)

    body = f"""
    <html>
    <head>
    <style>
        table {{
            font-family: Arial, sans-serif;
            border-collapse: collapse;
            width: 100%;
        }}
        th, td {{
            border: 1px solid #dddddd;
            text-align: left;
            padding: 8px;
        }}
        th {{
            background-color: #f2f2f2;
        }}
    </style>
    </head>
    <body>
    <p>A continuación se presentan las contrataciones realizadas entre el {fecha_inicio_formateada} y el {fecha_fin_formateada}.</p>
    <p>Total de filas encontradas: {total_items}</p>
    <br>
    <p>Para información más detallada, visitar: <a href="https://seacetlcom-production.up.railway.app">SEACE Contrataciones</a></p>
    <table>
        <tr>
            <th>Comprador</th>
            <th>Nomenclatura</th>
            <th>Item</th>
            <th>Fecha de Ingreso</th>
        </tr>
        {table_rows}
    </table>
    </body>
    </html>
    """

    msg = MIMEMultipart()
    msg['From'] = sender_email
    msg['To'] = ", ".join(recipients)
    msg['Subject'] = subject
    msg.attach(MIMEText(body, 'html'))

    try:
        with smtplib.SMTP(smtp_server, smtp_port) as server:
            server.starttls()
            server.login(sender_email, sender_password)
            server.sendmail(sender_email, recipients, msg.as_string())
            print("Correo enviado exitosamente.")
    except Exception as e:
        print(f"Error enviando correo: {e}")

async def main():
    """
    Función principal que coordina la consulta a la base de datos y el envío del correo.
    """
    # Define el rango de fechas de 15 días atrás a hoy
    fecha_fin = datetime.today().date()  # Fecha actual
    fecha_inicio = fecha_fin - timedelta(days=15)  # Hace 15 días
    
    # Define las palabras clave
    palabras_clave = [
        "antena", "satelital", "satélite", "DTH", "telecomunicaciones", "torres",
        "transmisores", "repetidores", "TVRO", "moduladores", "receptores",
        "DVB", "FM", "TV", "VHF", "agua"  # Incluye palabras clave adicionales
    ]

    # Realiza la consulta para todas las palabras clave
    items = await fetch_all_items(fecha_inicio, fecha_fin, palabras_clave)

    # Verifica si se encontraron resultados
    if items:
        table_rows = generate_table_rows(items)
        send_email(
            subject=f"Contrataciones relacionadas con tecnología y otros (últimos 15 días)",
            table_rows=table_rows,
            recipients=["frentz233@gmail.com"],
            fecha_inicio=fecha_inicio,
            fecha_fin=fecha_fin,
            total_items=len(items)
        )
    else:
        print("No se encontraron resultados para las palabras clave indicadas en el rango de los últimos 15 días.")

if __name__ == "__main__":
    import asyncio
    asyncio.run(main())
