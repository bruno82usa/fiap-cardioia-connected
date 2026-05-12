# CardioIA Conectada - Ir Além 1: E-mail Alerts
# FIAP - 2TIAO - Grupo 15 - Bruno Gambarini (RM561517)
# Sistema de alertas automáticos por e-mail para sinais vitais críticos

import smtplib
import os
from email.mime.text import MIMEText
from email.mime.multipart import MIMEMultipart
from datetime import datetime
from typing import Optional

# Configurações via variáveis de ambiente (NÃO commitar senhas)
SMTP_SERVER = os.getenv("SMTP_SERVER", "smtp.gmail.com")
SMTP_PORT = int(os.getenv("SMTP_PORT", "587"))
SMTP_USER = os.getenv("SMTP_USER", "cardioia.alerts@gmail.com")
SMTP_PASS = os.getenv("SMTP_PASS", "")
FROM_EMAIL = os.getenv("FROM_EMAIL", "cardioia.alerts@gmail.com")
TO_EMAIL = os.getenv("TO_EMAIL", "medico.responsavel@hospital.com")

def criar_email_html(tipo_alerta: str, valor: float, unidade: str, timestamp: datetime) -> str:
    """Cria template HTML profissional para alerta médico."""
    cores = {
        "bpm": ("Batimento Cardíaco Elevado", "#FF4500", "cardíaco"),
        "temperatura": ("Febre Detectada", "#DC143C", "térmico"),
        "desconexao": ("Conexão Perdida", "#FF8C00", "conectividade")
    }
    
    titulo, cor, icone = cores.get(tipo_alerta, ("Alerta do Sistema", "#FF0000", "sistema"))

    return f"""
    <!DOCTYPE html>
    <html>
    <head><meta charset="UTF-8"></head>
    <body style="font-family: Arial, sans-serif; max-width: 600px; margin: 0 auto;">
        <div style="background-color: {cor}; padding: 20px; border-radius: 10px 10px 0 0;">
            <h1 style="color: white; margin: 0; text-align: center;">
                ⚕️ ALERTA CardioIA — {titulo}
            </h1>
        </div>
        <div style="padding: 20px; border: 1px solid #ddd; border-top: none; border-radius: 0 0 10px 10px;">
            <table style="width: 100%; border-collapse: collapse;">
                <tr><td style="padding: 10px; font-weight: bold; color: #666;">Tipo de Evento:</td>
                    <td style="padding: 10px; color: {cor}; font-weight: bold;">{titulo}</td></tr>
                <tr style="background: #f9f9f9;"><td style="padding: 10px; font-weight: bold; color: #666;">Valor Detectado:</td>
                    <td style="padding: 10px; font-size: 24px; color: {cor};">{valor:.1f} {unidade}</td></tr>
                <tr><td style="padding: 10px; font-weight: bold; color: #666;">Data/Hora:</td>
                    <td style="padding: 10px;">{timestamp.strftime('%d/%m/%Y %H:%M:%S')}</td></tr>
                <tr style="background: #f9f9f9;"><td style="padding: 10px; font-weight: bold; color: #666;">Dispositivo:</td>
                    <td style="padding: 10px;">ESP32 CardioIA — Grupo 15</td></tr>
                <tr><td style="padding: 10px; font-weight: bold; color: #666;">Ação Recomendada:</td>
                    <td style="padding: 10px;">Verificar paciente imediatamente. Acessar dashboard para histórico.</td></tr>
            </table>
            <hr style="border: none; border-top: 1px solid #eee; margin: 20px 0;">
            <p style="color: #999; font-size: 12px; text-align: center;">
                CardioIA Conectada — Sistema de Monitoramento Cardíaco Inteligente<br>
                FIAP — 2TIAO — Grupo 15 — Este é um e-mail automático. Não responda.
            </p>
        </div>
    </body>
    </html>
    """

def enviar_alerta_email(tipo: str, valor: float, unidade: str, timestamp: Optional[datetime] = None) -> bool:
    """Envia alerta por e-mail para o médico responsável quando detectada anomalia."""
    if timestamp is None:
        timestamp = datetime.now()

    # Monta e-mail multipart (HTML + texto puro)
    msg = MIMEMultipart("alternative")
    msg["From"] = f"CardioIA Monitor <{FROM_EMAIL}>"
    msg["To"] = TO_EMAIL
    msg["Subject"] = f"[CardioIA] ALERTA: {tipo.upper()} — {valor:.1f} {unidade}"

    # Versão texto puro
    texto_puro = f"""
    ⚕️ ALERTA CardioIA
    ====================
    Tipo: {tipo}
    Valor: {valor:.1f} {unidade}
    Data/Hora: {timestamp.strftime('%d/%m/%Y %H:%M:%S')}
    Dispositivo: ESP32 CardioIA
    Ação: Verificar paciente imediatamente.
    """

    # Versão HTML
    html = criar_email_html(tipo, valor, unidade, timestamp)

    msg.attach(MIMEText(texto_puro, "plain"))
    msg.attach(MIMEText(html, "html"))

    try:
        with smtplib.SMTP(SMTP_SERVER, SMTP_PORT) as servidor:
            servidor.starttls()
            servidor.login(SMTP_USER, SMTP_PASS)
            servidor.send_message(msg)
            print(f"[EMAIL] Alerta enviado com sucesso: {tipo} = {valor:.1f} {unidade}")
            return True
    except smtplib.SMTPAuthenticationError:
        print("[EMAIL] ERRO: Autenticação falhou. Verifique SMTP_USER/SMTP_PASS.")
        return False
    except smtplib.SMTPException as e:
        print(f"[EMAIL] ERRO SMTP: {e}")
        return False
    except Exception as e:
        print(f"[EMAIL] ERRO inesperado: {e}")
        return False

# ============= TESTE =============
if __name__ == "__main__":
    print("=" * 50)
    print("  CardioIA — Sistema de Alertas por E-mail")
    print("  Grupo 15 — Bruno Gambarini RM561517")
    print("=" * 50)

    # Testa alerta de BPM elevado
    enviar_alerta_email("bpm", 135.0, "BPM", datetime(2026, 5, 12, 14, 30))

    # Testa alerta de febre
    enviar_alerta_email("temperatura", 39.2, "°C", datetime(2026, 5, 12, 15, 45))

    print("\n[TESTE] Alertas de e-mail testados. Verifique a caixa de entrada.")
    print("[CONFIG] Configure as variáveis SMTP_USER, SMTP_PASS, TO_EMAIL para produção.")
