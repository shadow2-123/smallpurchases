import smtplib
from email.message import EmailMessage
import logging

log = logging.getLogger(__name__)

class MailClient:
    def __init__(self,host: str,port: int, user: str, password: str, from_addr: str) -> None:
        self.host = host
        self.port = port
        self.user = user
        self.password = password
        self.from_addr = from_addr

    def send(self, to: str, subject: str, html: str, plain: str) -> None:
        msg = EmailMessage()
        msg["From"] = self.from_addr
        msg["To"] = to
        msg["Subject"] = subject
        msg.set_content(plain)
        msg.add_alternative(html, subtype="html")

        try:
            with smtplib.SMTP_SSL(self.host, self.port) as smtp:
                smtp.login(self.user, self.password)
                smtp.send_message(msg)
        except smtplib.SMTPAuthenticationError:
            log.exception("неверный логин или пароль почты")
            raise
        except smtplib.SMTPException:
            log.exception("не отправилось на %s", to)
            raise