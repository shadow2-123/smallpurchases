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
        self.smtp: smtplib.SMTP_SSL | None = None

    def connect(self):
        self.smtp = smtplib.SMTP_SSL(self.host, self.port)
        self.smtp.login(self.user, self.password)

    def close(self) -> None:
        if self.smtp is None:
            return
        try:
            self.smtp.quit()
        except smtplib.SMTPException:
            log.exception("не закрыл SMTP")
        self.smtp = None

    def __enter__(self) -> "MailClient":
        self.connect()
        return self

    def __exit__(self, *args) -> None:
        self.close()

    def send(self, to: str, subject: str, html: str, plain: str, attachments: list[tuple[str, bytes]] | None = None) -> None:
        if self.smtp is None:
            raise RuntimeError("сначала connect()")

        msg = EmailMessage()
        msg["From"] = self.from_addr
        msg["To"] = to
        msg["Subject"] = subject
        msg.set_content(plain)
        msg.add_alternative(html, subtype="html")
        for filename, data in attachments or []:
            msg.add_attachment(
                data,
                maintype="application",
                subtype="octet-stream",
                filename=filename,
            )

        try:
            self.smtp.send_message(msg)
        except smtplib.SMTPAuthenticationError:
            log.exception("неверный логин или пароль почты")
            raise
        except smtplib.SMTPException:
            log.exception("сессия SMTP умерла, переподключаюсь")
            self.close()
            self.connect()
            try:
                self.smtp.send_message(msg)
            except smtplib.SMTPException:
                log.exception("не отправилось на %s", to)