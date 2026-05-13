import streamlit as st
import pandas as pd
import pytesseract
import cv2
import numpy as np
import re
from PIL import Image
import requests
from io import StringIO

st.set_page_config(page_title="NHS Vision - Planejamento", layout="wide")

# --- 1. CONFIGURAÇÕES DA BASE ---
ID_PLANILHA = "11-jv_ZFetz9xdbJY8JZwPFSc3gtB65duvtDlLEk4I2E"
URL_BASE = f"https://docs.google.com/spreadsheets/d/{ID_PLANILHA}/export?format=csv&gid=0"

@st.cache_data
def carregar_base():
    try:
        res = requests.get(URL_BASE)
        df = pd.read_csv(StringIO(res.text), header=None).astype(str)
        # Aqui você pode manter a lógica de limpeza do seu código original
        return df
    except: return pd.DataFrame()

base_raw = carregar_base()

# --- 2. SIDEBAR (IGUAL AO ANTERIOR) ---
st.sidebar.title("🏭 Configurações")
sel_ups = st.sidebar.selectbox("Célula de Trabalho", ["UPS - 1", "UPS - 2", "UPS - 3", "UPS - 4", "UPS - 6", "UPS - 7", "UPS - 8", "ACS - 01"])
h_ini = st.sidebar.text_input("Início da Produção", "07:45")
tem_gin = st.sidebar.checkbox("🤸 Ginástica Laboral?")

# --- 3. ÁREA DE UPLOAD E OCR ---
st.title("📸 NHS Vision - Leitura Automática")
arquivo = st.file_uploader("Suba o print da programação", type=["png", "jpg", "jpeg"])

lista_detectada = []

if arquivo:
    img = Image.open(arquivo)
    if st.button("🔍 Ler Imagem e Gerar Tabela"):
        with st.spinner("Extraindo dados da imagem..."):
            img_np = np.array(img)
            gray = cv2.cvtColor(img_np, cv2.COLOR_RGB2GRAY)
            
            # Tenta ler o texto
            try:
                texto = pytesseract.image_to_string(gray)
                
                # Procura Modelo (85.A1...) e Quantidade (número antes de un)
                modelos = re.findall(r"(85\.[A-Z0-9\.]+)", texto)
                qtds = re.findall(r"(\d+[\.,]\d+|\d+)\s*\(un\)", texto)
                
                for m, q in zip(modelos, qtds):
                    lista_detectada.append({"Equipamento": m, "Qtd": q})
            except Exception as e:
                st.error("O motor de leitura ainda não está pronto. Aguarde o Reboot ou verifique o packages.txt.")

# --- 4. EDITOR DE DADOS (PRÉ-PREENCHIDO) ---
st.subheader("📋 Itens para Planejamento")
df_para_editar = pd.DataFrame(lista_detectada if lista_detectada else [{}], columns=["Equipamento", "Qtd"])

df_ed = st.data_editor(df_para_editar, num_rows="dynamic", use_container_width=True)

if st.button("🚀 Gerar Cronograma"):
    st.info("Aqui entrará a lógica de cálculo que você já tem no outro código!")
