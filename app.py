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

@st.cache_data(ttl=60)
def carregar_base():
    try:
        res = requests.get(URL_BASE)
        df = pd.read_csv(StringIO(res.text), header=None).astype(str)
        return df
    except: return pd.DataFrame()

# --- 2. SIDEBAR ---
st.sidebar.title("🏭 Configurações")
sel_ups = st.sidebar.selectbox("Célula de Trabalho", ["UPS - 1", "UPS - 2", "UPS - 3", "UPS - 4", "UPS - 6", "UPS - 7", "UPS - 8", "ACS - 01"])
h_ini = st.sidebar.text_input("Início da Produção", "07:45")
tem_gin = st.sidebar.checkbox("🤸 Ginástica Laboral?")

# --- 3. ÁREA DE UPLOAD E OCR ---
st.title("📸 NHS Vision - Leitura Automática")
arquivo = st.file_uploader("Suba o print da programação", type=["png", "jpg", "jpeg"])

# Inicializa o estado da tabela se não existir
if 'dados_lidos' not in st.session_state:
    st.session_state.dados_lidos = pd.DataFrame(columns=["Equipamento", "Qtd"])

if arquivo:
    img = Image.open(arquivo)
    if st.button("🔍 Ler Imagem e Gerar Tabela"):
        with st.spinner("Processando imagem..."):
            img_np = np.array(img.convert('RGB'))
            
            # --- MELHORIA DA IMAGEM PARA O OCR ---
            gray = cv2.cvtColor(img_np, cv2.COLOR_RGB2GRAY)
            # Aumenta o contraste e remove ruído
            _, thresh = cv2.threshold(gray, 150, 255, cv2.THRESH_BINARY + cv2.THRESH_OTSU)
            
            texto = pytesseract.image_to_string(thresh, lang='eng')
            
            # Expressões Regulares para capturar os padrões NHS
            # Padrão 1: Códigos que começam com 190 ou 85
            # Padrão 2: Números seguidos de (un)
            p_modelos = re.findall(r"((?:190|85)\.[A-Z0-9\.]+)", texto)
            p_qtds = re.findall(r"(\d+[\.,]\d+|\d+)\s*\(un\)", texto)
            
            novos_dados = []
            for m, q in zip(p_modelos, p_qtds):
                novos_dados.append({"Equipamento": m, "Qtd": q})
            
            if novos_dados:
                st.session_state.dados_lidos = pd.DataFrame(novos_dados)
                st.success(f"Encontrados {len(novos_dados)} itens!")
            else:
                st.warning("Não foi possível identificar modelos. Verifique se o print está nítido.")

# --- 4. EDITOR DE DADOS ---
st.subheader("📋 Itens para Planejamento")
df_ed = st.data_editor(st.session_state.dados_lidos, num_rows="dynamic", use_container_width=True)

if st.button("🚀 Gerar Cronograma"):
    if not df_ed.empty:
        st.write("### Dados Finais para Processamento:")
        st.dataframe(df_ed)
        st.balloons()
    else:
        st.error("A tabela está vazia!")
