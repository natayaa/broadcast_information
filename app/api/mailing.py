import smtplib

from email.mime.text import MIMEText
from email.mime.multipart import MIMEMultipart
from decouple import config


def ping_server(smtp_server, smtp_port):
    try:
        srv = smtplib.SMTP(smtp_server, smtp_port)
        srv.ehlo()
        srv.quit()
        return True
    except Exception as E:
        error_msg = {"errorMsg": str(E)}
        print(error_msg)
        return False
    
def send_mail_notif(payload):
    server_informations = list({"server": config("SMTP_SERVER_1"), "port": config("SMTP_SERVER_PORT_1"),
                                "server": config("SMTP_SERVER_2"), "port": config("SMTP_SERVER_PORT_2")})
    
    for server_mail in server_informations:
        if ping_server(server_mail['server'], server_mail['port']):
            try:
                smtp_server = smtplib.SMTP(server_mail['server'], server_mail['port'])
                smtp_server.starttls()
                account_notifier = {"sender_username": config("SMTP_SENDER"), "sender_password": config("SMTP_SENDER_PW")}
                smtp_server.login(account_notifier.get("sender_username", account_notifier.get("sender_password")))

                construct_mail = MIMEMultipart()
                construct_mail['From'] = account_notifier.get("sender_username")
                construct_mail['To'] = ";".join(payload.recipient_mail)
                if payload.carbon_copy:
                    construct_mail['Cc'] = ";".join(payload.carbon_copy)
                construct_mail['Subject'] = "[Remainder]" + payload.subject
                construct_mail.attach(MIMEText(payload.message, "plain"))

                # broadcast the mail
                recipients = payload.recipient_email + (payload.carbon_copy or []) 
                smtp_server.sendmail(account_notifier.get("sender_username"), account_notifier.get("sender_password"), recipients, construct_mail.as_string())
                smtp_server.quit()
                return True
            except Exception as E:
                returnMessage = {"eMsg": str(E)}
                return False
        else:
            pass
