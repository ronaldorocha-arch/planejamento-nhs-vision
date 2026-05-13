import streamlit as st
import pandas as pd
import pytesseract
import cv2
import numpy as np
import re
from PIL import Image
import requests
from io import StringIO

st.set_page_config(page_title="NHS Vision", layout="wide")

# --- 1. CONFIGURAÇÕES E MAPEAMENTO ---
ID_PLANILHA = "11-jv_ZFetz9xdbJY8JZwPFSc3gtB65duvtDlLEk4I2E"
URL_BASE = f"https://docs.google.com/spreadsheets/d/{ID_PLANILHA}/export?format=csv&gid=0"

MAPA_N_NATURAL = {
    "UPS - 1": 5, "UPS - 2": 3, "UPS - 3": 3, "UPS - 4": 3,
    "UPS - 6": 4, "UPS - 7": 4, "UPS - 8": 4, "ACS - 01": 3,
}

@st.cache_data
def carregar_base():
    try:
        res = requests.get(URL_BASE)
        return pd.read_csv(StringIO(res.text), header=None).astype(str)
    except: return pd.DataFrame()

# --- 2. SIDEBAR DINÂMICA ---
st.sidebar.title("🏭 Configurações")
sel_ups = st.sidebar.selectbox("Célula de Trabalho", list(MAPA_N_NATURAL.keys()))
h_ini = st.sidebar.text_input("Início da Produção", "07:45")
n_sugerido = MAPA_N_NATURAL.get(sel_ups, 5)
n_dia = st.sidebar.number_input(f"Pessoas na {sel_ups}", 1, 20, value=n_sugerido)
tem_gin = st.sidebar.checkbox("🤸 Ginástica Laboral?")

# --- 3. LÓGICA DE LEITURA DE IMAGEM ---
st.title("📸 NHS Vision - Leitura Automática")
arquivo = st.file_uploader("Suba o print da programação", type=["png", "jpg", "jpeg"])

# Session State para manter os dados na tabela após a leitura
if 'rows' not in st.session_state:
    st.session_state.rows = pd.DataFrame(columns=["Equipamento", "Qtd"])

if arquivo:
    img = Image.open(arquivo)
    if st.button("🔍 LER IMAGEM AGORA"):
        with st.spinner("Processando imagem..."):
            img_np = np.array(img.convert('RGB'))
            # Tratamento para destacar o texto (Preto e Branco)
            gray = cv2.cvtColor(img_np, cv2.COLOR_RGB2GRAY)
            _, thresh = cv2.threshold(gray, 150, 255, cv2.THRESH_BINARY + cv2.THRESH_OTSU)
            
            texto = pytesseract.image_to_string(thresh)
            
            # Busca códigos 85.A1... ou 1904... e quantidades antes de (un)
            modelos = re.findall(r"((?:85|190)\.[A-Z0-9\.]+)", texto)
            qtds = re.findall(r"(\d+[\.,]\d+|\d+)\s*\(un\)", texto)
            
            if modelos:
                novos_dados = []
                for m, q in zip(modelos, qtds):
                    novos_dados.append({"Equipamento": m, "Qtd": q})
                st.session_state.rows = pd.DataFrame(novos_dados)
                st.success(f"Sucesso! {len(modelos)} itens lidos.")
            else:
                st.error("Não consegui ler os códigos. Tente um print mais aproximado.")

# --- 4. TABELA EDITÁVEL (DADOS LIDOS APARECEM AQUI) ---
st.subheader("📋 Itens Identificados")
df_ed = st.data_editor(
    st.session_state.rows, 
    num_rows="dynamic", 
    use_container_width=True,
    column_config={
        "Equipamento": st.column_config.TextColumn("Modelo Lido"),
        "Qtd": st.column_config.TextColumn("Quantidade")
    }
)

if st.button("🚀 Gerar Planejamento Final"):
    if not df_ed.empty:
        st.write(f"### Planejamento para {sel_ups} ({n_dia} pessoas)")
        st.dataframe(df_ed)
        st.success("Tudo pronto! Copie os dados acima para o seu sistema principal.")
    else:
        st.warning("A tabela está vazia. Adicione itens ou leia uma imagem.")
