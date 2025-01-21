import os
import asyncpg
import smtplib
from email.mime.text import MIMEText
from email.mime.multipart import MIMEMultipart
from datetime import datetime

async def fetch_items_by_date(fecha):
    dsn = os.getenv("DB_DSN")
    query = """
    SELECT * FROM buscar_items_multi_criterio(
        NULL,
        NULL,
        NULL,
        $1,
        $1
    );
    """
    try:
        conn = await asyncpg.connect(dsn)
        rows = await conn.fetch(query, fecha)
        await conn.close()
        return rows
    except Exception as e:
        print(f"Error fetching data: {e}")
        return []

def send_email(subject, body, recipients):
    sender_email = os.getenv("EMAIL_USER")
    sender_password = os.getenv("EMAIL_PASSWORD")
    
    smtp_server = "smtp.gmail.com"  # Cambia esto a tu servidor SMTP
    smtp_port = 587  # Cambia esto al puerto SMTP adecuado

    msg = MIMEMultipart()
    msg['From'] = sender_email
    msg['To'] = ", ".join(recipients)
    msg['Subject'] = subject
    msg.attach(MIMEText(body, 'plain'))

    try:
        with smtplib.SMTP(smtp_server, smtp_port) as server:
            server.starttls()
            server.login(sender_email, sender_password)
            server.sendmail(sender_email, recipients, msg.as_string())
            print("Correo enviado exitosamente.")
    except Exception as e:
        print(f"Error enviando correo: {e}")

async def main():
    fecha_actual = datetime.strptime('2025-01-17', '%Y-%m-%d').date()  # Fecha fija #fecha_actual = datetime.now().strftime('%Y-%m-%d')
    items = await fetch_items_by_date(fecha_actual)

    if items:
        body = "Resultados de la consulta:\n\n"
        for item in items:
            body += f"Comprador: {item['comprador']}, Item: {item['item']}, Fecha: {item['fecha_ingreso']}\n"
        send_email(
            subject=f"Contrataciones del {fecha_actual}",
            body=body,
            recipients=["frentz233@gmail.com"]
        )
    else:
        print("No se encontraron resultados para la fecha indicada.")

if __name__ == "__main__":
    import asyncio
    asyncio.run(main())
