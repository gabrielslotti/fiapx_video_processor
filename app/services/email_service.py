import smtplib
from email.mime.multipart import MIMEMultipart
from email.mime.text import MIMEText
from app.core.config import settings

class EmailService:
    @staticmethod
    def send_email(to_email: str, subject: str, html_content: str):
        """
        Envia um email genérico via SMTP Gmail.
        """
        msg = MIMEMultipart()
        msg["From"] = settings.SMTP_SENDER
        msg["To"] = to_email
        msg["Subject"] = subject
        msg.attach(MIMEText(html_content, "html"))

        with smtplib.SMTP(settings.SMTP_SERVER, settings.SMTP_PORT) as server:
            server.ehlo()
            server.starttls()
            server.login(settings.SMTP_USER, settings.SMTP_PASSWORD)
            server.send_message(msg)

    @staticmethod
    def send_error_notification(user_email: str, video_name: str, error_message: str):
        subject = f"Erro no processamento do vídeo: {video_name}"
        html = f"""
        <html>
          <body>
            <h2>Erro no Processamento de Vídeo</h2>
            <p>Olá,</p>
            <p>Ocorreu um erro ao processar o vídeo <strong>{video_name}</strong>.</p>
            <p>Detalhes do erro:</p>
            <pre>{error_message}</pre>
            <p>Estamos verificando e retornaremos em breve.</p>
            

            <p>Atenciosamente,</p>
            <p>Equipe de Processamento de Vídeo</p>
          </body>
        </html>
        """
        EmailService.send_email(user_email, subject, html)

    @staticmethod
    def send_success_notification(user_email: str, video_name: str, download_url: str):
        subject = f"Vídeo processado com sucesso: {video_name}"
        html = f"""
        <html>
          <body>
            <h2>Vídeo Processado com Sucesso</h2>
            <p>Olá,</p>
            <p>Seu vídeo <strong>{video_name}</strong> foi processado com sucesso!</p>
            <p>Faça o download dos frames neste link:</p>
            <p><a href="{download_url}">Download dos Frames</a></p>
            

            <p>Atenciosamente,</p>
            <p>Equipe de Processamento de Vídeo</p>
          </body>
        </html>
        """
        EmailService.send_email(user_email, subject, html)