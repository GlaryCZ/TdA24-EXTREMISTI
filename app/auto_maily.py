import smtplib
from email.mime.multipart import MIMEMultipart
from email.mime.text import MIMEText

def mail(state, email, message, name, time, oid):
    # Údaje pro přihlášení k SMTP serveru Gmail
    SMTP_SERVER = 'smtp.gmail.com'
    SMTP_PORT = 587  # 587 pro TLS

    # Údaje pro přihlášení k e-mailovému účtu
    EMAIL_ADDRESS = 'extremistitda@gmail.com'
    EMAIL_PASSWORD = 'rekr xcgy nugl aevy'  # Nahraďte svým heslem

    # Adresa odesílatele a příjemce
    SENDER_EMAIL = 'extremistitda@gmail.com'
    RECIPIENT_EMAIL =  email

    # Vytvoření zprávy
    msg = MIMEMultipart()
    msg['From'] = SENDER_EMAIL
    msg['To'] = RECIPIENT_EMAIL



    if state == 'ano':
        msg['Subject'] = f'Potvrzení lekce číslo {oid}'
        body = f"Dobrý den, vaše žádost o lekci s číslem {oid} od lektora {name} v {time} hodin byla přijata,\n  zpáva od vašeho mentora:{message} "
    elif state == 'ne':
        msg['Subject'] = f'Zamítnutí lekce {oid}'
        body = f"Dobrý den, je nám líto, ale vaše žádost o lekci s číslem {oid} od {name} v {time} hodin byla zamítnuta"
    elif state == 'preobjednat':
        body = f"Dobrý den, vaše objednávka lekce s číslem {oid} od lektora {name} byla přesunuta {time}"

    msg.attach(MIMEText(body, 'plain'))

    # Připojení k SMTP serveru
    server = smtplib.SMTP(SMTP_SERVER, SMTP_PORT)
    server.starttls()
    server.login(EMAIL_ADDRESS, EMAIL_PASSWORD)

    # Odeslání e-mailu
    text = msg.as_string()
    server.sendmail(SENDER_EMAIL, RECIPIENT_EMAIL, text)

    # Uzavření spojení
    server.quit()

    print('E-mail byl úspěšně odeslán.')

# mail('ano, 'jan.navratil04@gmail.com', "smrdis" )  