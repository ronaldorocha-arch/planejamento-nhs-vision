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

# --- 1. CONFIGURAÇÃO DA PÁGINA ---
st.set_page_config(page_title="NHS Vision - Planejamento", page_icon="🏭", layout="wide")

# NOVO LINK DE EXPORTAÇÃO MAIS ESTÁVEL
ID_PLANILHA = "11-jv_ZFetz9xdbJY8JZwPFSc3gtB65duvtDlLEk4I2E"
URL_BASE = f"https://docs.google.com/spreadsheets/d/{ID_PLANILHA}/gviz/tq?tqx=out:csv&gid=0"

MAPA_N_NATURAL = {
    "UPS - 1": 5, "UPS - 2": 3, "UPS - 3": 3, "UPS - 4": 3,
    "UPS - 6": 4, "UPS - 7": 4, "UPS - 8": 4, "ACS - 01": 3,
}

# --- 2. FUNÇÃO PARA CARREGAR A BASE ---
@st.cache_data(ttl=10) # Cache baixíssimo para atualizar rápido
def carregar_base():
    try:
        response = requests.get(URL_BASE, timeout=15)
        if response.status_code != 200:
            return pd.DataFrame(), f"Erro de conexão: Status {response.status_code}"
        
        # Lê o CSV ignorando possíveis problemas de aspas
        df_raw = pd.read_csv(StringIO(response.text), header=None, quoting=1).astype(str)
        
        m_row, m_col = -1, -1
        # Procura a palavra MODELO
        for r in range(min(50, len(df_raw))):
            for c in range(len(df_raw.columns)):
                if "MODELO" in str(df_raw.iloc[r, c]).upper().strip():
                    m_row, m_col = r, c
                    break
            if m_row != -1: break
            
        if m_row == -1:
            return pd.DataFrame(), "Palavra 'MODELO' não encontrada na 1ª aba."
        
        dados = df_raw.iloc[m_row+1:].copy()
        lista_final = []
        cel_atual = "Indefinida"
        
        for i in range(len(dados)):
            mod = str(dados.iloc[i, m_col]).strip().replace('"', '')
            if mod == 'nan' or len(mod) < 3: continue
            
            try:
                unid_str = str(dados.iloc[i, m_col+1]).replace(',', '.').replace('"', '')
                unid = pd.to_numeric(unid_str, errors='coerce')
                
                ups_linha = str(dados.iloc[i, m_col+3]).strip().upper()
                if any(x in ups_linha for x in ["UPS", "ACS", "ACE"]):
                    cel_atual = str(dados.iloc[i, m_col+3]).strip().replace('"', '')
                
                if not pd.isna(unid):
                    lista_final.append({'ID': mod, 'UNIDADE_HORA': unid, 'CEL_ORIGEM': cel_atual})
            except: continue
            
        if not lista_final:
            return pd.DataFrame(), "Nenhum dado válido extraído após a linha 'MODELO'."
            
        return pd.DataFrame(lista_final), "Sucesso"
    except Exception as e:
        return pd.DataFrame(), f"Erro crítico: {str(e)}"

# --- INTERFACE ---
st.sidebar.title("Configurações")

# Botão para forçar atualização
if st.sidebar.button("🔄 Limpar Cache / Atualizar Planilha"):
    st.cache_data.clear()
    st.rerun()

base_dados, mensagem_base = carregar_base()

if base_dados.empty:
    st.error(f"❌ {mensagem_base}")
    st.info("Dica: A aba 'BASE' deve ser a primeira da esquerda no Google Sheets.")
else:
    st.sidebar.success("✅ Planilha Base Conectada")

sel_ups = st.sidebar.selectbox("Célula", list(MAPA_N_NATURAL.keys()))
h_ini = st.sidebar.text_input("Início", "07:45")
n_dia = st.sidebar.number_input(f"Pessoas na {sel_ups}", 1, 25, value=MAPA_N_NATURAL.get(sel_ups, 5))
tem_gin = st.sidebar.checkbox("Ginástica Laboral?", value=True)

st.title("📸 NHS Vision - Automação")

if 'rows' not in st.session_state:
    st.session_state.rows = pd.DataFrame(columns=["Equipamento", "Qtd"])

arq = st.file_uploader("Suba o print da programação", type=["png", "jpg", "jpeg"])

if arq:
    img = Image.open(arq)
    if st.button("🔍 LER IMAGEM E PREENCHER"):
        if base_dados.empty:
            st.error("Impossível ler imagem: Planilha Base não carregada.")
        else:
            with st.spinner("Lendo Tesseract OCR..."):
                img_np = np.array(img.convert('RGB'))
                gray = cv2.cvtColor(img_np, cv2.COLOR_RGB2GRAY)
                texto = pytesseract.image_to_string(gray)
                p_mods = re.findall(r"((?:85|190)\.[A-Z0-9\.]+)", texto)
                p_qtds = re.findall(r"(\d+[\.,]\d+|\d+)\s*\(un\)", texto)
                
                dados_v = []
                for m, q in zip(p_mods, p_qtds):
                    if m in base_dados['ID'].values:
                        val = int(float(q.replace(',', '.')))
                        dados_v.append({"Equipamento": m, "Qtd": val})
                
                if dados_v:
                    st.session_state.rows = pd.DataFrame(dados_v)
                    st.success(f"{len(dados_v)} itens encontrados!")
                else:
                    st.warning("Nenhum modelo da imagem existe na Planilha Base.")

st.subheader("📋 Tabela de Produção")
df_editado = st.data_editor(st.session_state.rows, num_rows="dynamic", width="stretch")

if st.button("🚀 GERAR CRONOGRAMA"):
    if not df_editado.empty and not base_dados.empty:
        # Reutilize sua função calcular_cronograma aqui...
        st.write("Calculando...")
        # (Adicione aqui a função calcular_cronograma que enviamos anteriormente)
    else:
        st.error("Verifique se a tabela tem dados e se a base foi carregada.")
