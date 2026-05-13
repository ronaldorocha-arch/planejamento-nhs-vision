import streamlit as st
import pandas as pd
import pytesseract
import cv2
import numpy as np
import re
from PIL import Image
import requests
from io import StringIO
import math
from datetime import datetime, timedelta

# Tenta configurar o caminho do tesseract caso esteja local (opcional)
# pytesseract.pytesseract.tesseract_cmd = r'/usr/bin/tesseract' 

# --- CONFIGURAÇÃO DA PÁGINA ---
st.set_page_config(page_title="NHS Vision - Automação", layout="wide")

ID_PLANILHA = "11-jv_ZFetz9xdbJY8JZwPFSc3gtB65duvtDlLEk4I2E"
URL_BASE = f"https://docs.google.com/spreadsheets/d/{ID_PLANILHA}/export?format=csv&gid=0"

MAPA_N_NATURAL = {
    "UPS - 1": 5, "UPS - 2": 3, "UPS - 3": 3, "UPS - 4": 3,
    "UPS - 6": 4, "UPS - 7": 4, "UPS - 8": 4, "ACS - 01": 3,
}

@st.cache_data(ttl=60)
def carregar_base():
    try:
        res = requests.get(URL_BASE, timeout=15)
        df = pd.read_csv(StringIO(res.text), header=None).astype(str)
        m_row, m_col = -1, -1
        for r in range(min(100, len(df))):
            for c in range(len(df.columns)):
                if "MODELO" in str(df.iloc[r, c]).upper():
                    m_row, m_col = r, c
                    break
            if m_row != -1: break
        if m_row == -1: return pd.DataFrame()
        
        dados = df.iloc[m_row+1:].copy()
        lista = []
        cel_atual = "Indefinida"
        for i in range(len(dados)):
            mod = str(dados.iloc[i, m_col]).strip()
            try:
                unid = pd.to_numeric(dados.iloc[i, m_col+1].replace(',', '.'), errors='coerce')
                ups_l = str(dados.iloc[i, m_col+3]).strip().upper()
                if any(x in ups_l for x in ["UPS", "ACS"]): cel_atual = str(dados.iloc[i, m_col+3]).strip()
                if mod != 'nan' and len(mod) > 5 and not pd.isna(unid):
                    lista.append({'ID': mod, 'UNIDADE_HORA': unid, 'CEL_ORIGEM': cel_atual})
            except: continue
        return pd.DataFrame(lista)
    except: return pd.DataFrame()

# --- INTERFACE ---
base_dados = carregar_base()

st.sidebar.title("🏭 Configurações")
sel_ups = st.sidebar.selectbox("Célula", list(MAPA_N_NATURAL.keys()))
h_ini = st.sidebar.text_input("Início", "07:45")
n_dia = st.sidebar.number_input("Pessoas", 1, 20, value=MAPA_N_NATURAL.get(sel_ups, 5))

st.title("📸 NHS Vision - Leitura Automática")

if 'rows' not in st.session_state:
    st.session_state.rows = pd.DataFrame(columns=["Equipamento", "Qtd"])

arq = st.file_uploader("Suba o print", type=["png", "jpg", "jpeg"])

if arq:
    img = Image.open(arq)
    if st.button("🔍 LER IMAGEM E PREENCHER"):
        try:
            with st.spinner("Extraindo texto..."):
                img_np = np.array(img.convert('RGB'))
                gray = cv2.cvtColor(img_np, cv2.COLOR_RGB2GRAY)
                # O comando abaixo causava o erro se o packages.txt não existisse
                texto = pytesseract.image_to_string(gray)
                
                p_mods = re.findall(r"((?:85|190)\.[A-Z0-9\.]+)", texto)
                p_qtds = re.findall(r"(\d+[\.,]\d+|\d+)\s*\(un\)", texto)
                
                validos = []
                for m, q in zip(p_mods, p_qtds):
                    if not base_dados.empty and m in base_dados['ID'].values:
                        validos.append({"Equipamento": m, "Qtd": int(float(q.replace(',', '.')))})
                
                if validos:
                    st.session_state.rows = pd.DataFrame(validos)
                    st.success(f"{len(validos)} itens identificados!")
                else:
                    st.warning("Nenhum modelo compatível encontrado na imagem.")
        except Exception as e:
            st.error(f"Erro no OCR: Certifique-se que o arquivo packages.txt foi criado no GitHub. Detalhe: {e}")

st.data_editor(st.session_state.rows, num_rows="dynamic", use_container_width=True)
