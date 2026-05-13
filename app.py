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

# Link da sua planilha (Aba BASE)
ID_PLANILHA = "11-jv_ZFetz9xdbJY8JZwPFSc3gtB65duvtDlLEk4I2E"
URL_BASE = f"https://docs.google.com/spreadsheets/d/{ID_PLANILHA}/export?format=csv&gid=0"

# Mapeamento de pessoas por célula (N Natural)
MAPA_N_NATURAL = {
    "UPS - 1": 5, "UPS - 2": 3, "UPS - 3": 3, "UPS - 4": 3,
    "UPS - 6": 4, "UPS - 7": 4, "UPS - 8": 4, "ACS - 01": 3,
}

# --- 2. FUNÇÃO PARA CARREGAR A BASE ---
@st.cache_data(ttl=60)
def carregar_base():
    try:
        # Tenta carregar a planilha diretamente como CSV
        response = requests.get(URL_BASE, timeout=15)
        if response.status_code != 200:
            return pd.DataFrame()
            
        df_raw = pd.read_csv(StringIO(response.text), header=None).astype(str)
        
        # Procura a célula que contém "MODELO" (ignora maiúsculas/minúsculas)
        m_row, m_col = -1, -1
        for r in range(min(100, len(df_raw))):
            for c in range(len(df_raw.columns)):
                if "MODELO" in str(df_raw.iloc[r, c]).upper().strip():
                    m_row, m_col = r, c
                    break
            if m_row != -1: break
            
        if m_row == -1:
            return pd.DataFrame()
        
        # Extrai os dados a partir da linha encontrada
        dados = df_raw.iloc[m_row+1:].copy()
        lista_final = []
        cel_atual = "Indefinida"
        
        for i in range(len(dados)):
            mod = str(dados.iloc[i, m_col]).strip()
            try:
                # Unidade/Hora está na coluna ao lado do Modelo
                unid_str = str(dados.iloc[i, m_col+1]).replace(',', '.')
                unid = pd.to_numeric(unid_str, errors='coerce')
                
                # Célula de origem está 3 colunas à direita do Modelo
                ups_linha = str(dados.iloc[i, m_col+3]).strip().upper()
                
                if any(x in ups_linha for x in ["UPS", "ACS", "ACE"]):
                    cel_atual = str(dados.iloc[i, m_col+3]).strip()
                
                if mod != 'nan' and len(mod) > 5 and not pd.isna(unid):
                    lista_final.append({
                        'ID': mod, 
                        'UNIDADE_HORA': unid, 
                        'CEL_ORIGEM': cel_atual
                    })
            except: continue
            
        return pd.DataFrame(lista_final)
    except Exception as e:
        return pd.DataFrame()

# --- 3. LÓGICA DE CÁLCULO ---
def calcular_cronograma(df_input, df_base, h_ini, n_dia, tem_gin):
    def para_min(s):
        h, m = map(int, s.split(':'))
        return h * 60 + m
    
    m_ini = para_min(h_ini)
    m_alm_i, m_alm_f = para_min("11:30"), para_min("12:30")
    m_cafe_m, m_cafe_t = para_min("09:20"), para_min("15:20")
    m_gin_i, m_gin_f = para_min("09:30"), para_min("09:40")
    
    marcos = ["08:30", "09:30", "10:30", "11:30", "12:30", "13:30", "14:30", "15:30", "16:30", "17:30"]
    pontos = [h_ini] + [m for m in marcos if para_min(m) > m_ini]
    
    # Cruza os dados lidos com a base da planilha
    df_proc = df_input.merge(df_base, left_on='Equipamento', right_on='ID', how='left')
    
    def calc_cad(row):
        n_nom = MAPA_N_NATURAL.get(row['CEL_ORIGEM'], 5)
        return (row['UNIDADE_HORA'] / n_nom) * n_dia

    df_proc['CAD_R'] = df_proc.apply(calc_cad, axis=1)
    df_proc['T_PC'] = 60 / df_proc['CAD_R']
    df_proc['FALTA'] = pd.to_numeric(df_proc['Qtd'])
    
    resultado = []
    idx, acum, tot = 0, 0.0, 0
    total_pedir = df_proc['FALTA'].sum()
    h_fim = "Não finalizado"

    for p in range(len(pontos)-1):
        p1, p2 = para_min(pontos[p]), para_min(pontos[p+1])
        is_alm = (p1 == m_alm_i and p2 == m_alm_f)
        min_uteis = 0
        
        if not is_alm:
            for m in range(p1, p2):
                if not ((m_cafe_m <= m < m_cafe_m+10) or (m_cafe_t <= m < m_cafe_t+10) or 
                        (m_alm_i <= m < m_alm_f) or (tem_gin and m_gin_i <= m < m_gin_f)):
                    min_uteis += 1
        
        acum += min_uteis
        p_hora, modelos_h = 0, []
        
        if is_alm:
            resultado.append({'Horário': f"{pontos[p]} – {pontos[p+1]}", 'Modelos': "🍱 ALMOÇO", 'Peças': 0, 'Acum': int(tot)})
            continue

        while idx < len(df_proc):
            t_pc = df_proc.loc[idx, 'T_PC']
            if acum >= (t_pc - 0.0001):
                qtd_pode = min(math.floor(acum / t_pc + 0.0001), df_proc.loc[idx, 'FALTA'])
                if qtd_pode > 0:
                    acum -= (qtd_pode * t_pc)
                    df_proc.loc[idx, 'FALTA'] -= qtd_pode
                    tot += qtd_pode
                    p_hora += qtd_pode
                    modelos_h.append(f"{df_proc.loc[idx, 'ID']} ({int(qtd_pode)})")
                if df_proc.loc[idx, 'FALTA'] <= 0: idx += 1
                else: break
            else: break
            
        resultado.append({'Horário': f"{pontos[p]} – {pontos[p+1]}", 'Modelos': " + ".join(modelos_h) if modelos_h else "-", 'Peças': int(p_hora), 'Acum': int(tot)})
        
        if tot >= total_pedir and h_fim == "Não finalizado" and total_pedir > 0:
            sobra_min = min_uteis - acum
            dt = datetime.strptime(pontos[p], "%H:%M") + timedelta(minutes=int(sobra_min))
            h_fim = dt.strftime("%H:%M")

    return pd.DataFrame(resultado), tot, h_fim

# --- 4. INTERFACE ---
base_dados = carregar_base()

st.sidebar.title("🏭 Configurações")
sel_ups = st.sidebar.selectbox("Célula de Trabalho", list(MAPA_N_NATURAL.keys()))
n_sugerido = MAPA_N_NATURAL.get(sel_ups, 5)
h_ini = st.sidebar.text_input("Início da Produção", "07:45")
n_dia = st.sidebar.number_input(f"Pessoas na {sel_ups}", 1, 25, value=n_sugerido)
tem_gin = st.sidebar.checkbox("🤸 Ginástica Laboral?", value=True)

st.title("📸 NHS Vision - Automação")

if 'rows' not in st.session_state:
    st.session_state.rows = pd.DataFrame(columns=["Equipamento", "Qtd"])

# Upload e OCR
arq = st.file_uploader("Suba o print da programação aqui", type=["png", "jpg", "jpeg"])

if arq:
    img = Image.open(arq)
    if st.button("🔍 LER IMAGEM E PREENCHER"):
        if base_dados.empty:
            st.error("Erro: A Planilha Base não pôde ser carregada. Verifique se a aba BASE é a primeira da planilha e se contém a coluna 'MODELO'.")
        else:
            with st.spinner("Processando imagem..."):
                img_np = np.array(img.convert('RGB'))
                gray = cv2.cvtColor(img_np, cv2.COLOR_RGB2GRAY)
                _, thresh = cv2.threshold(gray, 155, 255, cv2.THRESH_BINARY + cv2.THRESH_OTSU)
                texto = pytesseract.image_to_string(thresh)
                
                p_mods = re.findall(r"((?:85|190)\.[A-Z0-9\.]+)", texto)
                p_qtds = re.findall(r"(\d+[\.,]\d+|\d+)\s*\(un\)", texto)
                
                dados_v = []
                for m, q in zip(p_mods, p_qtds):
                    if m in base_dados['ID'].values:
                        dados_v.append({"Equipamento": m, "Qtd": int(float(q.replace(',', '.')))})
                    else:
                        st.warning(f"Modelo {m} não encontrado na base de dados.")
                
                if dados_v:
                    st.session_state.rows = pd.DataFrame(dados_v)
                    st.success("Tabela preenchida!")

st.subheader("📋 Tabela de Produção")
df_editado = st.data_editor(st.session_state.rows, num_rows="dynamic", use_container_width=True)

if st.button("🚀 GERAR CRONOGRAMA"):
    if not df_editado.empty:
        df_res, total, fim = calcular_cronograma(df_editado, base_dados, h_ini, n_dia, tem_gin)
        st.divider()
        c1, c2 = st.columns(2)
        c1.metric("Total Peças", f"{int(total)} un")
        c2.metric("Término", fim)
        
        def cor_intervalo(row):
            return ['background-color: #f8d7da'] * len(row) if "ALMOÇO" in str(row["Modelos"]) else [''] * len(row)
        
        st.dataframe(df_res.style.apply(cor_intervalo, axis=1), use_container_width=True, height=500)
