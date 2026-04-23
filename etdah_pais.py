import streamlit as st
import smtplib
from email.mime.text import MIMEText
from email.mime.multipart import MIMEMultipart
import json
import gspread
from google.oauth2.service_account import Credentials
import datetime

# ================= BLOCO 1: DEFINIÇÃO DA MARCA D'ÁGUA =================
def inject_watermark(nome_paciente, id_sessao):
    paciente_display = nome_paciente if nome_paciente else "PACIENTE NÃO IDENTIFICADO"
    
    watermark_style = f"""
    <style>
    .watermark {{
        position: fixed;
        top: 0; left: 0; width: 100%; height: 100%;
        z-index: 9999;
        pointer-events: none;
        display: flex;
        flex-wrap: wrap;
        justify-content: space-around;
        align-content: space-around;
        opacity: 0.12;
        user-select: none;
    }}
    .watermark-text {{
        transform: rotate(-45deg);
        font-size: 22px;
        font-weight: bold;
        color: grey;
        white-space: nowrap;
        text-align: center;
        margin: 40px;
    }}
    </style>
    <div class="watermark">
        {f"<div class='watermark-text'>INSTRUMENTO SIGILOSO<br>{paciente_display}<br>{id_sessao}</div>" * 20}
    </div>
    """
    st.markdown(watermark_style, unsafe_allow_html=True)

# ================= CONFIGURAÇÕES DE E-MAIL =================
SEU_EMAIL = st.secrets["EMAIL_USUARIO"]
SENHA_DO_EMAIL = st.secrets["SENHA_USUARIO"]

# ================= CONEXÃO COM GOOGLE SHEETS =================
@st.cache_resource
def conectar_planilha():
    creds_dict = json.loads(st.secrets["GOOGLE_CREDENTIALS_JSON"])
    escopos = [
        "https://www.googleapis.com/auth/spreadsheets",
        "https://www.googleapis.com/auth/drive"
    ]
    creds = Credentials.from_service_account_info(creds_dict, scopes=escopos)
    client = gspread.authorize(creds)
    return client.open("Controle_Tokens").sheet1 

try:
    planilha = conectar_planilha()
except Exception as e:
    st.error(f"Erro de conexão com a planilha de controle: {e}")
    st.stop()

def enviar_email_resultados(nome, token, data_nasc, idade, sexo, nome_resp, parentesco, resultados_processados):
    assunto = f"Resultados ETDAH-Pais - Paciente: {nome}"
    corpo = f"Avaliação ETDAH-Pais concluída.\n\n"
    corpo += f"=== DADOS DO(A) PACIENTE ===\nNome: {nome}\nData de Nascimento: {data_nasc}\nIdade Calculada: {idade} anos\nSexo: {sexo}\nToken de Validação: {token}\n\n"
    corpo += f"=== DADOS DO(A) RESPONDENTE ===\nNome: {nome_resp}\nVínculo: {parentesco}\n\n"
    corpo += "================ RESULTADOS ================\n\n"

    for fator, dados in resultados_processados.items():
        corpo += f"{fator}:\n  - Escore Bruto: {dados['bruto']}\n  - Percentil: {dados['percentil']}\n  - Classificação: {dados['classificacao']}\n\n"

    msg = MIMEMultipart()
    msg['From'] = SEU_EMAIL
    msg['To'] = "psicologabrunaligoski@gmail.com"
    msg['Subject'] = assunto
    msg.attach(MIMEText(corpo, 'plain'))

    try:
        server = smtplib.SMTP('smtp.gmail.com', 587)
        server.starttls()
        server.login(SEU_EMAIL, SENHA_DO_EMAIL)
        server.send_message(msg)
        server.quit()
        return True
    except:
        return False

# TABELAS NORMATIVAS (MANTIDAS)
tabelas_normativas = {
    'Feminino': {
        '10_13': {
            'Comportamento Adaptativo': [(15.0, 1), (16.65, 5), (26.1, 10), (30.25, 15), (33.2, 20), (35.5, 25), (38.9, 30), (42.7, 35), (43.4, 40), (44.0, 45), (46.5, 50), (49.0, 55), (49.6, 60), (53.0, 65), (53.7, 70), (55.5, 75), (57.0, 80), (58.7, 85), (60.0, 90), (70.35, 95)],
            'Desatenção': [(12.0, 1), (12.0, 5), (13.2, 10), (16.95, 15), (19.4, 20), (21.0, 25), (21.0, 30), (21.85, 35), (23.4, 40), (24.95, 45), (25.0, 50), (26.2, 55), (32.4, 60), (34.15, 65), (35.0, 70), (37.0, 75), (38.6, 80), (46.4, 85), (52.6, 90), (59.6, 95)],
            'Escore Geral': [(80.0, 1), (88.6, 5), (97.4, 10), (101.0, 15), (106.0, 20), (116.5, 25), (122.8, 30), (128.7, 35), (134.8, 40), (139.0, 45), (142.5, 50), (145.4, 55), (156.0, 60), (159.45, 65), (176.0, 70), (190.0, 75), (194.6, 80), (198.75, 85), (208.3, 90), (238.65, 95)],
            'Hiperatividade/Impulsividade': [(14.0, 1), (16.2, 5), (18.2, 10), (20.0, 15), (20.2, 20), (21.75, 25), (22.6, 30), (24.85, 35), (25.0, 40), (25.0, 45), (26.0, 50), (27.05, 55), (28.6, 60), (29.15, 65), (30.0, 70), (32.0, 75), (38.2, 80), (44.05, 85), (46.9, 90), (57.7, 95)],
            'Regulação Emocional': [(20.0, 1), (22.2, 5), (27.2, 10), (29.0, 15), (30.0, 20), (30.0, 25), (36.3, 30), (38.7, 35), (39.0, 40), (40.9, 45), (41.0, 50), (43.2, 55), (48.2, 60), (49.0, 65), (51.1, 70), (52.75, 75), (55.8, 80), (65.5, 85), (76.5, 90), (83.7, 95)]
        },
        '14_17': {
            'Comportamento Adaptativo': [(18.0, 1), (18.0, 5), (18.7, 10), (21.75, 15), (24.4, 20), (27.5, 25), (35.1, 30), (35.95, 35), (36.0, 40), (36.65, 45), (37.5, 50), (38.7, 55), (40.2, 60), (41.05, 65), (41.9, 70), (45.0, 75), (46.6, 80), (49.25, 85), (54.7, 90)],
            'Desatenção': [(12.0, 1), (12.0, 5), (12.0, 10), (13.1, 15), (14.0, 20), (14.75, 25), (17.0, 30), (17.0, 35), (21.0, 40), (22.0, 45), (23.0, 50), (24.0, 55), (24.4, 60), (26.15, 65), (28.7, 70), (30.5, 75), (33.4, 80), (35.9, 85), (38.2, 90)],
            'Escore Geral': [(72.0, 1), (72.0, 5), (78.3, 10), (87.05, 15), (95.2, 20), (102.25, 25), (109.2, 30), (110.9, 35), (111.8, 40), (115.25, 45), (117.0, 50), (118.05, 55), (122.0, 60), (130.8, 65), (144.4, 70), (147.5, 75), (149.2, 80), (157.2, 85), (169.6, 90)],
            'Hiperatividade/Impulsividade': [(16.0, 1), (16.0, 5), (16.0, 10), (16.55, 15), (18.6, 20), (21.0, 25), (21.1, 30), (21.95, 35), (23.6, 40), (24.0, 45), (24.0, 50), (25.75, 55), (29.0, 60), (29.1, 65), (30.8, 70), (32.5, 75), (33.6, 80), (35.35, 85), (37.9, 90)],
            'Regulação Emocional': [(25.0, 1), (25.0, 5), (25.0, 10), (25.55, 15), (26.4, 20), (27.5, 25), (29.4, 30), (32.8, 35), (33.0, 40), (33.65, 45), (35.0, 50), (36.0, 55), (36.2, 60), (37.0, 65), (37.0, 70), (37.75, 75), (39.2, 80), (40.0, 85), (46.3, 90)]
        },
        '2_5': {
            'Comportamento Adaptativo': [(20.0, 1), (20.7, 5), (29.0, 10), (37.0, 15), (37.0, 20), (38.0, 25), (40.2, 30), (44.5, 35), (46.0, 40), (46.0, 45), (47.0, 50), (48.1, 55), (51.0, 60), (59.0, 65), (59.8, 70), (61.0, 75), (63.4, 80), (66.4, 85), (71.8, 90), (78.4, 95)],
            'Desatenção': [(13.0, 1), (13.0, 5), (13.4, 10), (15.9, 15), (18.8, 20), (20.0, 25), (20.6, 30), (21.0, 35), (23.4, 40), (24.0, 45), (25.0, 50), (26.2, 55), (28.2, 60), (29.3, 65), (30.0, 70), (31.0, 75), (35.6, 80), (48.5, 85), (53.0, 90), (53.0, 95)],
            'Escore Geral': [(106.0, 1), (107.0, 5), (116.0, 10), (119.3, 15), (127.4, 20), (130.5, 25), (133.6, 30), (136.8, 35), (139.6, 40), (151.7, 45), (155.0, 50), (160.4, 55), (173.8, 60), (180.3, 65), (191.2, 70), (196.5, 75), (209.0, 80), (217.0, 85), (244.2, 90), (252.8, 95)],
            'Hiperatividade/Impulsividade': [(21.0, 1), (21.0, 5), (21.6, 10), (24.3, 15), (25.4, 20), (27.5, 25), (29.0, 30), (29.7, 35), (30.8, 40), (32.8, 45), (34.0, 50), (34.1, 55), (35.2, 60), (37.8, 65), (42.0, 70), (53.5, 75), (67.4, 80), (72.5, 85), (74.0, 90), (74.0, 95)],
            'Regulação Emocional': [(23.0, 1), (23.9, 5), (32.6, 10), (35.3, 15), (36.0, 20), (36.5, 25), (38.8, 30), (40.7, 35), (41.8, 40), (44.7, 45), (47.0, 50), (49.4, 55), (53.0, 60), (53.0, 65), (53.0, 70), (53.5, 75), (57.6, 80), (62.1, 85), (65.4, 90), (76.8, 95)]
        },
        '6_9': {
            'Comportamento Adaptativo': [(21.0, 1), (22.35, 5), (26.7, 10), (28.35, 15), (29.0, 20), (34.5, 25), (40.2, 30), (43.45, 35), (47.2, 40), (49.0, 45), (50.5, 50), (54.85, 55), (55.8, 60), (57.0, 65), (57.0, 70), (58.5, 75), (60.2, 80), (61.0, 85), (65.3, 90), (71.3, 95)],
            'Desatenção': [(15.0, 1), (16.35, 5), (18.0, 10), (22.0, 15), (22.8, 20), (24.0, 25), (24.0, 30), (26.0, 35), (26.0, 40), (26.05, 45), (27.0, 50), (27.0, 55), (29.6, 60), (32.0, 65), (32.3, 70), (33.0, 75), (35.0, 80), (35.0, 85), (37.2, 90), (43.4, 95)],
            'Escore Geral': [(88.0, 1), (95.65, 5), (107.7, 10), (112.8, 15), (124.4, 20), (128.0, 25), (134.5, 30), (137.2, 35), (144.0, 40), (145.55, 45), (162.0, 50), (169.9, 55), (176.0, 60), (185.0, 65), (187.0, 70), (190.75, 75), (192.8, 80), (196.0, 85), (210.6, 90), (227.55, 95)],
            'Hiperatividade/Impulsividade': [(18.0, 1), (18.45, 5), (19.9, 10), (23.7, 15), (25.0, 20), (27.0, 25), (27.0, 30), (27.15, 35), (29.2, 40), (30.0, 45), (30.5, 50), (32.9, 55), (34.0, 60), (34.0, 65), (43.0, 70), (46.75, 75), (50.6, 80), (53.0, 85), (53.3, 90), (58.75, 95)],
            'Regulação Emocional': [(23.0, 1), (24.8, 5), (29.7, 10), (32.05, 15), (34.8, 20), (36.75, 25), (42.5, 30), (44.15, 35), (45.0, 40), (45.0, 45), (45.5, 50), (46.95, 55), (49.4, 60), (54.7, 65), (55.0, 70), (57.25, 75), (61.0, 80), (65.0, 85), (65.6, 90), (77.05, 95)]
        }
    },
    'Masculino': {
        '10_13': {
            'Comportamento Adaptativo': [(27.0, 1), (32.0, 5), (37.8, 10), (41.0, 15), (44.4, 20), (46.0, 25), (49.0, 30), (51.0, 35), (51.4, 40), (52.7, 45), (53.0, 50), (54.0, 55), (54.6, 60), (57.7, 65), (59.2, 70), (60.0, 75), (60.0, 80), (64.0, 85), (65.4, 90), (70.0, 95)],
            'Desatenção': [(15.0, 1), (16.3, 5), (19.6, 10), (21.0, 15), (22.6, 20), (27.5, 25), (28.0, 30), (29.1, 35), (30.0, 40), (31.0, 45), (36.0, 50), (36.0, 55), (37.2, 60), (39.9, 65), (42.0, 70), (42.5, 75), (43.0, 80), (49.0, 85), (50.4, 90), (62.2, 95)],
            'Escore Geral': [(104.0, 1), (104.9, 5), (120.6, 10), (127.3, 15), (134.2, 20), (148.0, 25), (149.8, 30), (153.1, 35), (155.6, 40), (163.1, 45), (165.0, 50), (168.5, 55), (175.6, 60), (186.3, 65), (195.0, 70), (207.0, 75), (222.8, 80), (235.0, 85), (247.8, 90), (258.1, 95)],
            'Hiperatividade/Impulsividade': [(15.0, 1), (21.0, 5), (24.8, 10), (26.9, 15), (28.0, 20), (28.5, 25), (30.0, 30), (32.0, 35), (35.0, 40), (35.0, 45), (36.0, 50), (39.3, 55), (40.0, 60), (41.0, 65), (41.2, 70), (43.5, 75), (51.2, 80), (56.3, 85), (66.4, 90), (68.4, 95)],
            'Regulação Emocional': [(25.0, 1), (25.0, 5), (26.3, 10), (29.2, 15), (30.9, 20), (32.2, 25), (34.0, 30), (34.8, 35), (36.1, 40), (39.2, 45), (42.0, 50), (43.0, 55), (47.6, 60), (50.0, 65), (51.0, 70), (55.2, 75), (60.0, 80), (61.0, 85), (69.0, 90), (78.0, 95)]
        },
        '14_17': {
            'Comportamento Adaptativo': [(20.0, 1), (20.6, 5), (32.2, 10), (34.0, 15), (34.0, 20), (35.25, 25), (39.3, 30), (41.05, 35), (43.0, 40), (43.0, 45), (46.5, 50), (51.1, 55), (52.6, 60), (53.0, 65), (53.0, 70), (53.0, 75), (53.8, 80), (59.1, 85), (60.9, 90), (65.75, 95)],
            'Desatenção': [(15.0, 1), (15.05, 5), (16.1, 10), (17.0, 15), (17.4, 20), (19.75, 25), (22.0, 30), (23.4, 35), (26.0, 40), (26.0, 45), (27.0, 50), (29.1, 55), (31.8, 60), (33.65, 65), (34.0, 70), (34.0, 75), (36.4, 80), (38.7, 85), (40.8, 90), (41.0, 95)],
            'Escore Geral': [(84.0, 1), (84.45, 5), (94.6, 10), (109.15, 15), (112.4, 20), (124.0, 25), (130.3, 30), (131.0, 35), (132.2, 40), (136.7, 45), (141.5, 50), (143.0, 55), (143.0, 60), (145.6, 65), (162.4, 70), (173.5, 75), (188.6, 80), (192.0, 85), (192.0, 90), (235.7, 95)],
            'Hiperatividade/Impulsividade': [(16.0, 1), (16.1, 5), (18.2, 10), (20.15, 15), (21.2, 20), (23.0, 25), (26.3, 30), (27.35, 35), (28.0, 40), (28.0, 45), (29.5, 50), (32.65, 55), (35.2, 60), (36.0, 65), (36.7, 70), (37.0, 75), (38.6, 80), (39.85, 85), (41.8, 90), (42.0, 95)],
            'Regulação Emocional': [(20.0, 1), (20.0, 5), (20.5, 10), (25.0, 15), (25.8, 20), (29.25, 25), (30.3, 30), (31.35, 35), (32.4, 40), (33.0, 45), (33.0, 50), (36.3, 55), (39.6, 60), (44.55, 65), (49.8, 70), (52.5, 75), (55.4, 80), (56.0, 85), (71.3, 90), (108.15, 95)]
        },
        '2_5': {
            'Comportamento Adaptativo': [(38.0, 1), (38.0, 5), (38.0, 10), (44.3, 15), (47.0, 20), (47.5, 25), (48.8, 30), (50.6, 35), (52.4, 40), (54.1, 45), (55.0, 50), (55.0, 55), (55.8, 60), (56.7, 65), (57.6, 70), (59.0, 75), (61.6, 80), (64.9, 85), (67.4, 90)],
            'Desatenção': [(19.0, 1), (19.0, 5), (20.6, 10), (21.0, 15), (21.0, 20), (22.5, 25), (24.4, 30), (25.0, 35), (25.2, 40), (26.1, 45), (27.0, 50), (29.7, 55), (31.6, 60), (32.7, 65), (33.6, 70), (34.5, 75), (35.4, 80), (36.3, 85), (37.2, 90)],
            'Escore Geral': [(115.0, 1), (115.0, 5), (115.0, 10), (136.7, 15), (151.4, 20), (156.5, 25), (159.2, 30), (161.3, 35), (162.6, 40), (165.1, 45), (166.0, 50), (167.8, 55), (168.0, 60), (169.4, 65), (171.2, 70), (174.5, 75), (183.0, 80), (196.5, 85), (211.2, 90)],
            'Hiperatividade/Impulsividade': [(23.0, 1), (23.0, 5), (24.6, 10), (25.0, 15), (25.6, 20), (26.0, 25), (28.0, 30), (32.5, 35), (36.6, 40), (39.1, 45), (40.0, 50), (40.9, 55), (45.0, 60), (46.7, 65), (47.6, 70), (50.0, 75), (52.8, 80), (54.6, 85), (58.6, 90)],
            'Regulação Emocional': [(30.0, 1), (30.0, 5), (30.8, 10), (31.0, 15), (33.4, 20), (37.0, 25), (39.0, 30), (39.3, 35), (40.0, 40), (40.3, 45), (43.0, 50), (46.6, 55), (47.0, 60), (48.4, 65), (49.6, 70), (50.5, 75), (52.6, 80), (55.6, 85), (57.2, 90)]
        },
        '6_9': {
            'Comportamento Adaptativo': [(34.0, 1), (34.35, 5), (35.0, 10), (37.0, 15), (38.6, 20), (41.75, 25), (44.1, 30), (46.35, 35), (48.0, 40), (48.15, 45), (49.0, 50), (49.0, 55), (51.0, 60), (52.65, 65), (54.0, 70), (57.0, 75), (60.0, 80), (66.75, 85), (67.3, 90), (71.25, 95)],
            'Desatenção': [(15.0, 1), (15.7, 5), (17.0, 10), (18.1, 15), (20.0, 20), (21.5, 25), (23.7, 30), (30.45, 35), (31.0, 40), (31.3, 45), (33.5, 50), (34.0, 55), (34.4, 60), (37.65, 65), (39.9, 70), (41.0, 75), (44.0, 80), (45.9, 85), (46.6, 90), (48.0, 95)],
            'Escore Geral': [(102.0, 1), (106.2, 5), (114.7, 10), (117.6, 15), (129.0, 20), (132.75, 25), (136.7, 30), (143.0, 35), (145.4, 40), (151.15, 45), (152.5, 50), (153.85, 55), (165.2, 60), (172.05, 65), (178.8, 70), (203.25, 75), (214.8, 80), (218.85, 85), (219.9, 90), (253.85, 95)],
            'Hiperatividade/Impulsividade': [(21.0, 1), (21.7, 5), (23.0, 10), (24.1, 15), (26.0, 20), (28.25, 25), (29.1, 30), (30.0, 35), (30.0, 40), (32.3, 45), (34.0, 50), (34.0, 55), (35.4, 60), (37.55, 65), (42.5, 70), (44.25, 75), (46.8, 80), (50.85, 85), (61.0, 90), (62.95, 95)],
            'Regulação Emocional': [(22.0, 1), (23.75, 5), (28.4, 10), (30.0, 15), (30.0, 20), (30.75, 25), (33.3, 30), (36.45, 35), (37.0, 40), (37.0, 45), (41.0, 50), (45.0, 55), (45.0, 60), (47.75, 65), (50.9, 70), (54.0, 75), (61.8, 80), (64.9, 85), (69.0, 90), (85.9, 95)]
        }
    }
}

def obter_faixa_etaria(idade):
    if 2 <= idade <= 5: return "2_5"
    elif 6 <= idade <= 9: return "6_9"
    elif 10 <= idade <= 13: return "10_13"
    elif 14 <= idade <= 17: return "14_17"
    return None

def obter_classificacao(percentil):
    if percentil <= 20: return "Inferior"
    elif percentil <= 40: return "Média Inferior"
    elif percentil <= 60: return "Média"
    elif percentil <= 80: return "Média Superior"
    else: return "Superior"

def cruzar_dados_normativos(fator, pontuacao_bruta, sexo, faixa_etaria):
    tabela = tabelas_normativas[sexo][faixa_etaria][fator]
    percentil_encontrado = tabela[0][1]
    for score_tabela, perc in tabela:
        if pontuacao_bruta >= score_tabela:
            percentil_encontrado = perc
        else: break
    return percentil_encontrado, obter_classificacao(percentil_encontrado)

opcoes_respostas = {
    "1 - Nunca": 1, "2 - Muito pouco": 2, "3 - Pouco": 3,
    "4 - Geralmente": 4, "5 - Frequentemente": 5, "6 - Muito frequentemente": 6
}

st.set_page_config(page_title="Avaliação ETDAH-Pais", layout="centered")

st.markdown("""
    <style>
    div[data-testid="stFormSubmitButton"] > button {
        background-color: #0047AB !important; color: white !important;
        border: none !important; padding: 0.6rem 2.5rem !important;
        border-radius: 8px !important; font-weight: bold !important; font-size: 16px !important;
    }
    div[data-testid="stFormSubmitButton"] > button:hover {
        background-color: #003380 !important; color: white !important;
    }
    </style>
""", unsafe_allow_html=True)

if "avaliacao_concluida" not in st.session_state:
    st.session_state.avaliacao_concluida = False

# Título Centralizado
st.markdown("<h1 style='text-align: center;'>Clínica de Psicologia e Psicanálise Bruna Ligoski</h1>", unsafe_allow_html=True)

if st.session_state.avaliacao_concluida:
    st.success("Avaliação concluída e enviada com sucesso! Muito obrigado(a) pela sua colaboração.")
    st.stop()

# ================= VALIDAÇÃO E CAPTURA DE PARÂMETROS =================
parametros = st.query_params
token_url = parametros.get("token", None)
nome_na_url = parametros.get("nome", "")

if not token_url:
    st.warning("⚠️ Link de acesso inválido. Solicite um novo link à profissional.")
    st.stop()

try:
    registros = planilha.get_all_records()
    dados_token = None
    linha_alvo = 2 
    for i, reg in enumerate(registros):
        if str(reg.get("Token")) == token_url:
            dados_token = reg
            linha_alvo += i
            break
            
    if not dados_token or dados_token.get("Status") != "Aberto":
        st.error("⚠️ Este link é inválido ou já foi utilizado.")
        st.stop()
except Exception:
    st.error("Erro técnico na validação do link.")
    st.stop()

# ================= QUESTIONÁRIO ETDAH-PAIS =================
linha_fina = "<hr style='margin-top: 8px; margin-bottom: 8px;'/>"
st.markdown(linha_fina, unsafe_allow_html=True)
st.markdown("<h3 style='text-align: center;'>Escala ETDAH-Pais</h3>", unsafe_allow_html=True)
st.markdown(linha_fina, unsafe_allow_html=True)

# IDENTIFICAÇÃO (FORA DO FORM PARA ATUALIZAÇÃO DINÂMICA)
st.subheader("Dados do(a) Paciente")
nome_paciente = st.text_input("Nome completo do(a) paciente *", value=nome_na_url)
data_nascimento = st.date_input("Data de nascimento *", format="DD/MM/YYYY", min_value=datetime.date(1900, 1, 1), max_value=datetime.date.today(), value=None)
sexo_paciente = st.selectbox("Sexo *", ["Selecione", "Masculino", "Feminino"])

st.subheader("Dados do(a) Respondente")
nome_resp = st.text_input("Nome completo do(a) respondente *")
parentesco = st.text_input("Vínculo / Parentesco (Mãe, Pai, Avó, etc.) *")

# Chamada da Marca d'água
inject_watermark(nome_paciente, token_url)

st.divider()
st.write("Abaixo estão alguns itens que descrevem comportamentos que o(a) paciente pode apresentar. Considere a frequência atual e nos últimos seis meses.")
st.markdown(linha_fina, unsafe_allow_html=True)

perguntas = [
    "Faz amizade, mas não consegue mantê-la", "Implica com tudo", "Tem fortes reações emocionais (explosões de raiva)", "É irritadiço(a) (tudo o incomoda)", "Muda facilmente de humor", "Explode com facilidade (é do tipo “pavio curto”)", "Dá a impressão de estar sempre insatisfeito(a) (nada o(a) agrada)", "É rebelde (não aceita nada)", "É agressivo(a)", "Sente-se infeliz", "Faz birra quando quer algo", "Mostra-se tenso(a) e rígido(a)", "Implica com os irmãos", "As atividades e reuniões são desagradáveis", "Todos têm que fazer o que ele(a) quer", "A hora de acordar e das refeições é desagradável", "Exige mais tempo e atenção dos responsáveis do que outros familiares", "Tem dificuldades para se adaptar às mudanças", "É sensível",
    "Movimenta-se muito (parece estar ligado(a) com um motor ou a todo vapor)", "É inquieto(a) e agitado(a)", "Mexe-se e contorce-se durante as refeições e para realizar as tarefas de casa", "Tem sempre muita pressa", "Age sem pensar (é impulsivo/a)", "É inconsequente (não considera os perigos da situação)", "Intromete-se em assuntos que não lhe dizem respeito", "Responde antes de ouvir a pergunta inteira", "É imprudente", "Irrita os outros com suas palhaçadas", "Tende a discordar com as regras e normas de jogos", "É persistente e insiste diante de uma ideia", "Faz os deveres escolares rápido demais",
    "Aceita facilmente regras, normas e limites", "Parece ser uma pessoa tranquila e sossegada", "É tolerante, quando preciso", "Respeita normas e regras", "É obediente", "Obedece aos pais/responsáveis e as normas da casa", "Sabe aguardar sua vez (é paciente)", "Faz suas tarefas e almoça com bastante tranquilidade", "Faz as coisas com muito cuidado, prevendo os riscos de suas ações", "Seu comportamento é adequado socialmente", "Fala pouco", "O(a) paciente permite que o ambiente familiar seja tranquilo e harmonioso", "Consegue expressar claramente os seus pensamentos", "É atento(a) quando conversa com alguém",
    "É independente para realizar as suas tarefas de casa", "É distraído(a) com quase tudo", "Evita atividades que exigem esforço mental constante (deveres escolares, jogos)", "Esquece rápido o que acabou de ser dito", "Inicia uma atividade com entusiasmo e dificilmente chega ao final", "Tem dificuldade para realizar as coisas importantes (lição, por exemplo)", "Não termina o que começa", "Parece sonhar acordado(a) (estar no mundo da lua)", "Mostra-se concentrado(a) apenas em atividades de seu interesse", "Dá a impressão de que não ouve bem (só escuta o que quer)", "Dificilmente observa detalhes", "Ocorrem discussões entre os responsáveis e o(a) paciente em função da falta de responsabilidade"
]

with st.form("form_etdah_pais"):
    respostas_usuario = {}
    for index, texto_pergunta in enumerate(perguntas):
        num_q = index + 1
        st.write(f"**{num_q}. {texto_pergunta}**")
        respostas_usuario[num_q] = st.radio(f"q_{num_q}", list(opcoes_respostas.keys()), index=None, label_visibility="collapsed")
        st.divider()

    if st.form_submit_button("Enviar Avaliação"):
        hoje = datetime.date.today()
        questoes_em_branco = [q for q, r in respostas_usuario.items() if r is None]

        if not nome_paciente or not nome_resp or not parentesco or sexo_paciente == "Selecione" or data_nascimento is None:
            st.error("Por favor, preencha todos os campos de identificação.")
        elif questoes_em_branco:
            st.error(f"Por favor, responda todas as perguntas. Faltam {len(questoes_em_branco)} questão(ões).")
        else:
            idade = hoje.year - data_nascimento.year - ((hoje.month, hoje.day) < (data_nascimento.month, data_nascimento.day))
            faixa_etaria = obter_faixa_etaria(idade)

            if faixa_etaria is None:
                st.error(f"O(a) paciente possui {idade} anos. Escala válida de 2 a 17 anos.")
            else:
                f1_qs = range(1, 20); f2_qs = range(20, 33); f3_qs = range(33, 47); f4_qs = range(47, 59)
                escores = {"Regulação Emocional": 0, "Hiperatividade/Impulsividade": 0, "Comportamento Adaptativo": 0, "Desatenção": 0, "Escore Geral": 0}

                for n, r in respostas_usuario.items():
                    val = opcoes_respostas[r]
                    ponto = (7 - val) if (n in f3_qs or n == 47) else val
                    if n in f1_qs: escores["Regulação Emocional"] += ponto
                    elif n in f2_qs: escores["Hiperatividade/Impulsividade"] += ponto
                    elif n in f3_qs: escores["Comportamento Adaptativo"] += ponto
                    elif n in f4_qs: escores["Desatenção"] += ponto
                    escores["Escore Geral"] += ponto

                resultados_completos = {f: cruzar_dados_normativos(f, v, sexo_paciente, faixa_etaria) for f, v in escores.items()}
                res_dict = {f: {"bruto": escores[f], "percentil": resultados_completos[f][0], "classificacao": resultados_completos[f][1]} for f in escores}

                with st.spinner('Enviando resultados...'):
                    if enviar_email_resultados(nome_paciente, token_url, data_nascimento.strftime("%d/%m/%Y"), idade, sexo_paciente, nome_resp, parentesco, res_dict):
                        try:
                            planilha.update_cell(linha_alvo, 5, "Respondido")
                            st.session_state.avaliacao_concluida = True
                            st.rerun()
                        except:
                            st.session_state.avaliacao_concluida = True
                            st.rerun()
                    else:
                        st.error("Erro ao enviar. Tente novamente.")
