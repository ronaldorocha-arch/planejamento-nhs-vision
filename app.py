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

st.title("🏭 NHS Vision - Extrator de Programação")
st.markdown("Suba o print da tela de programação para converter em dados.")

# 1. Carregar Base Original para validação
ID_PLANILHA = "11-jv_ZFetz9xdbJY8JZwPFSc3gtB65duvtDlLEk4I2E"
URL_BASE = f"https://docs.google.com/spreadsheets/d/{ID_PLANILHA}/export?format=csv&gid=0"

@st.cache_data
def carregar_base():
    try:
        res = requests.get(URL_BASE)
        df = pd.read_csv(StringIO(res.text), header=None).astype(str)
        # Pega a coluna onde ficam os nomes dos modelos (ajuste o índice se necessário)
        return df.iloc[:, 0].tolist() 
    except:
        return []

base_nomes = carregar_base()

# 2. Upload
arquivo = st.file_uploader("Selecione o print", type=["png", "jpg", "jpeg"])

if arquivo:
    img = Image.open(arquivo)
    st.image(img, caption="Imagem carregada", width=600)
    
    if st.button("🚀 Iniciar Leitura"):
        with st.spinner("Lendo imagem..."):
            img_np = np.array(img)
            # Converter para Cinza
            gray = cv2.cvtColor(img_np, cv2.COLOR_RGB2GRAY)
            
            # OCR
            texto = pytesseract.image_to_string(gray)
            
            # Regex para buscar Modelo (85.A1...) e Quantidade (número antes de un)
            modelos = re.findall(r"(85\.[A-Z0-9\.]+)", texto)
            qtds = re.findall(r"(\d+[\.,]\d+|\d+)\s*\(un\)", texto)
            
            # Criar Tabela de Resultados
            dados = []
            for m, q in zip(modelos, qtds):
                dados.append({
                    "Modelo": m,
                    "Quantidade": q,
                    "Status": "✅ Ok" if m in str(base_nomes) else "❌ Não cadastrado"
                })
            
            if dados:
                st.subheader("📋 Dados Extraídos")
                st.table(pd.DataFrame(dados))
            else:
                st.warning("Nenhum padrão encontrado. Tente um print mais nítido.")
