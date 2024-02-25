import smtplib
from email.mime.multipart import MIMEMultipart
from email.mime.text import MIMEText

def mail(state, email, message):
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



    if state=='ano':
        msg['Subject'] = 'Potvrzení lekce'
        body = f"Dobrý den, vaše žádost o lektora byla přijata, \n {message} "
    else:
        msg['Subject'] = 'Zamítnutí lekce'
        body = "Dobrý den, je nám líto, ale vaše žádost o lekci byla zamítnuta"

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