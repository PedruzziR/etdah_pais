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
    # Fallback caso o nome ainda não tenha sido digitado
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

# TABELAS NORMATIVAS (OMITIDAS AQUI PARA BREVIDADE, MAS DEVEM SER MANTIDAS NO SEU CÓDIGO)
# ... [Mantenha aqui seu dicionário tabelas_normativas completo] ...

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

# Estilização do botão
st.markdown("""
    <style>
    div[data-testid="stFormSubmitButton"] > button {
        background-color: #0047AB !important; color: white !important;
        border: none !important; padding: 0.6rem 2.5rem !important;
        border-radius: 8px !important; font-weight: bold !important; font-size: 16px !important;
    }
    </style>
""", unsafe_allow_html=True)

# ================= VALIDAÇÃO E CAPTURA DE PARÂMETROS =================
parametros = st.query_params
token_url = parametros.get("token", None)
nome_na_url = parametros.get("nome", "")

if not token_url:
    st.warning("⚠️ Link de acesso inválido.")
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

# ================= INTERFACE PRINCIPAL =================
st.markdown("<h1 style='text-align: center;'>Clínica de Psicologia e Psicanálise Bruna Ligoski</h1>", unsafe_allow_html=True)

if st.session_state.get("avaliacao_concluida", False):
    st.success("Avaliação enviada com sucesso!")
    st.stop()

# IDENTIFICAÇÃO (FORA DO FORM PARA MARCA D'ÁGUA DINÂMICA)
st.subheader("Dados do(a) Paciente")
nome_paciente = st.text_input("Nome completo do(a) paciente *", value=nome_na_url)
data_nascimento = st.date_input("Data de nascimento *", format="DD/MM/YYYY", min_value=datetime.date(1900, 1, 1), max_value=datetime.date.today(), value=None)
sexo_paciente = st.selectbox("Sexo *", ["Selecione", "Masculino", "Feminino"])

st.subheader("Dados do(a) Respondente")
nome_resp = st.text_input("Nome completo do(a) respondente *")
parentesco = st.text_input("Vínculo / Parentesco *")

# CHAMADA DA MARCA D'ÁGUA (IMEDIATAMENTE APÓS OS INPUTS)
inject_watermark(nome_paciente, token_url)

st.divider()

perguntas = [
    # ... [Mantenha sua lista de 58 perguntas aqui] ...
]

with st.form("form_etdah_pais"):
    respostas_usuario = {}
    for index, texto_pergunta in enumerate(perguntas):
        num_q = index + 1
        st.write(f"**{num_q}. {texto_pergunta}**")
        respostas_usuario[num_q] = st.radio(f"q_{num_q}", list(opcoes_respostas.keys()), index=None, label_visibility="collapsed")
        st.divider()

    if st.form_submit_button("Enviar Avaliação"):
        # Lógica de cálculo e envio (Mantenha a que já tínhamos)
        hoje = datetime.date.today()
        if not nome_paciente or not nome_resp or sexo_paciente == "Selecione" or data_nascimento is None:
            st.error("Preencha todos os campos de identificação.")
        else:
            idade = hoje.year - data_nascimento.year - ((hoje.month, hoje.day) < (data_nascimento.month, data_nascimento.day))
            faixa_etaria = obter_faixa_etaria(idade)
            
            if faixa_etaria is None:
                st.error(f"Paciente com {idade} anos. Escala válida de 2 a 17 anos.")
            else:
                # [Cálculo dos escores e envio de e-mail]
                # ...
                st.success("Processando...")
