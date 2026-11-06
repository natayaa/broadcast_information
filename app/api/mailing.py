import smtplib
from email.mime.text import MIMEText
from email.mime.multipart import MIMEMultipart
from decouple import config

server1 = config("SMTP_SERVER_1")
server1Port = config("SMTP_SERVER_PORT_1")
server2 = config("SMTP_SERVER_2")
server2Port = config("SMTP_SERVER_PORT_2")


def send_mail_notif(payload, sender_email, sender_pw, server_name):
    # Define server configurations and error messages
    server_config = {
        "relay.sharp.co.jp": {
            "server": server1,
            "port": server1Port,
            "refused_message": "Connection is being refused, check the connection",
        },
        "smtp.office365.com": {
            "server": server2,
            "port": server2Port,
            "refused_message": "Connection is being refused, check the connection or change the gateway",
        },
    }

    # Check if the server_name is valid
    if server_name not in server_config:
        return {"server_response": "Invalid server name"}

    # Get server configuration based on server_name
    chosen_server = server_config[server_name]

    # Create an email message
    try:
        with smtplib.SMTP(chosen_server["server"], chosen_server["port"]) as smtp_server:
            smtp_server.starttls()
            smtp_server.login(sender_email, sender_pw)

            construct_mail = MIMEMultipart()
            construct_mail['From'] = sender_email
            construct_mail['To'] = ";".join(payload.get("direct_mail"))
            
            carbon_copy_mail = payload.get("carbon_copy_mail")
            if carbon_copy_mail:
                construct_mail['Cc'] = ";".join(carbon_copy_mail)

            construct_mail['Subject'] = f"[Reminder] {payload.get('mail_subject')}"
            construct_mail.attach(MIMEText(payload.get("document_content"), "plain"))

            # Broadcast the mail
            recipients = payload.get("direct_mail") + (carbon_copy_mail or [])
            smtp_server.sendmail(sender_email, recipients, construct_mail.as_string())

        return {
            "server_response": "Connection Successful",
            "info": "Message delivered",
            "success": True
        }

    except Exception as e:
        return {
            "server_response": chosen_server["refused_message"],
            "info": {"eMsg": str(e)},
            "success": False
        }
