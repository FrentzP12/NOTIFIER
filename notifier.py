import os
import asyncpg
import smtplib
from email.mime.text import MIMEText
from email.mime.multipart import MIMEMultipart
from datetime import datetime, timedelta

async def fetch_items_by_date(fecha_inicio, fecha_fin):
    dsn = os.getenv("DB_DSN")
    query = """
    SELECT * FROM buscar_items_multi_criterio(
        NULL,
        NULL,
        NULL,
        $1,
        $2
    );
    """
    try:
        conn = await asyncpg.connect(dsn)
        rows = await conn.fetch(query, fecha_inicio, fecha_fin)
        await conn.close()
        return rows
    except Exception as e:
        print(f"Error fetching data: {e}")
        return []

def generate_table_rows(items):
    table_rows = ""
    for item in items:
        table_rows += f"<tr><td>{item['comprador']}</td><td>{item['item']}</td><td>{item['fecha_ingreso']}</td></tr>"
    return table_rows

def send_email(subject, table_rows, recipients):
    sender_email = os.getenv("EMAIL_USER")
    sender_password = os.getenv("EMAIL_PASSWORD")
    
    smtp_server = "smtp.gmail.com"  # Cambia esto si usas otro proveedor
    smtp_port = 587  # Puerto SMTP estándar para TLS

    # Crear el cuerpo del correo con formato HTML
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
    <p>Nuevas entradas ingresadas para el día DD/MM/YY</p>
    <br>
    <p>Para información más precisa, revisar la página https://seacetlcom-production.up.railway.app <p>
    <table>
        <tr>
            <th>Comprador</th>
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
    fecha_inicio = datetime.strptime('2025-01-17', '%Y-%m-%d').date()
    fecha_fin = fecha_inicio + timedelta(days=1)  # Día siguiente para cubrir todo el día 17
    items = await fetch_items_by_date(fecha_inicio, fecha_fin)

    if items:
        table_rows = generate_table_rows(items)
        send_email(
            subject=f"Contrataciones del {fecha_inicio}",
            table_rows=table_rows,
            recipients=["frentz233@gmail.com"]
        )
    else:
        print("No se encontraron resultados para la fecha indicada.")

if __name__ == "__main__":
    import asyncio
    asyncio.run(main())