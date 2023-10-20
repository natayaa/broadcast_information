import smtplib
from email.mime.text import MIMEText
from email.mime.multipart import MIMEMultipart
from decouple import config

server1 = config("SMTP_SERVER_1")
server1Port = config("SMTP_SERVER_PORT_1")
server2 = config("SMTP_SERVER_2")
server2Port = config("SMTP_SERVER_PORT_2")

def ping_server(smtp_server, smtp_port):
    try:
        with smtplib.SMTP(smtp_server, smtp_port) as srv:
            srv.ehlo()
        return True
    except Exception as E:
        error_msg = {"errorMsg": str(E)}
        print(error_msg)
        return False


def send_mail_notif(payload, sender_email, sender_pw, server_name):
    choosed_server = {}
    if server_name == "relay.sharp.co.jp":
        feedback_server = ping_server(smtp_server=server1, smtp_port=server1Port)
        if feedback_server:
            choosed_server.update({"servername": server1, "portnum": server1Port, "server_response": "Connection Successful"})
        else:
            choosed_server.update({"server_response": "Connection is being refused, check the connection"})
    elif server_name == "smtp.office365.com":
        feed_serv = ping_server(smtp_server=server2, smtp_port=server2Port)
        if feed_serv:
            choosed_server.update({"servername": server2, "portnum": server2Port, "server_response": "Connection Successful"})
        else:
            choosed_server.update({"server_response": "Connection is being refused, check the connection or change the gateway"})

    if choosed_server.get("servername"):
        try:
            with smtplib.SMTP(choosed_server.get("servername"), choosed_server.get("portnum")) as smtp_server:
                smtp_server.starttls()
                smtp_server.login(sender_email, sender_pw)

                construct_mail = MIMEMultipart()
                construct_mail['From'] = sender_email
                construct_mail['To'] = ";".join(payload.get("direct_mail"))
                if payload.get("carbon_copy_mail"):
                    construct_mail['Cc'] = ";".join(payload.get("carbon_copy_mail"))
                construct_mail['Subject'] = "[Remainder]" + payload.get("mail_subject")
                construct_mail.attach(MIMEText(payload.get("document_content"), "plain"))

                # broadcast the mail
                recipients = payload.get("direct_mail") + (payload.get("carbon_copy_mail") or []) 
                smtp_server.sendmail(sender_email, recipients, construct_mail.as_string())
            choosed_server.update({"info": "Message delivered"})
        except Exception as E:
            returnMessage = {"eMsg": str(E)}
            print(returnMessage)
            choosed_server.update({"info": returnMessage})
    
    return choosed_server