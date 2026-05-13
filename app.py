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

# 1. CONFIGURAÇÃO E MAPEAMENTO
st.set_page_config(page_title="NHS Vision - Planejamento", page_icon="🏭", layout="wide")

ID_PLANILHA = "11-jv_ZFetz9xdbJY8JZwPFSc3gtB65duvtDlLEk4I2E"
URL_BASE = f"https://docs.google.com/spreadsheets/d/{ID_PLANILHA}/export?format=csv&gid=0"

MAPA_N_NATURAL = {
    "UPS - 1": 5, "UPS - 2": 3, "UPS - 3": 3, "UPS - 4": 3,
    "UPS - 6": 4, "UPS - 7": 4, "UPS - 8": 4, "ACS - 01": 3,
}

@st.cache_data(ttl=10)
def carregar_base():
    try:
        response = requests.get(URL_BASE, timeout=10)
        df_raw = pd.read_csv(StringIO(response.text), header=None).astype(str)
        m_row, m_col = -1, -1
        for r in range(min(50, len(df_raw))):
            for c in range(len(df_raw.columns)):
                if str(df_raw.iloc[r, c]).strip().upper() == "MODELO":
                    m_row, m_col = r, c
                    break
            if m_row != -1: break
        if m_row == -1: return pd.DataFrame()
        
        dados = df_raw.iloc[m_row+1:].copy()
        lista_final, cel_atual = [], "Indefinida"
        for i in range(len(dados)):
            mod = str(dados.iloc[i, m_col]).strip()
            try:
                unid = pd.to_numeric(dados.iloc[i, m_col+1].replace(',', '.'), errors='coerce')
                ups_linha = str(dados.iloc[i, m_col+3]).strip().upper()
                if any(x in ups_linha for x in ["UPS", "ACS", "ACE"]):
                    cel_atual = str(dados.iloc[i, m_col+3]).strip()
                if mod != 'nan' and len(mod) > 5 and not pd.isna(unid):
                    lista_final.append({
                        'ID': mod, 'UNIDADE_HORA': unid, 
                        'CEL_ORIGEM': cel_atual, 
                        'DISPLAY': f"[{cel_atual}] {mod}"
                    })
            except: continue
        return pd.DataFrame(lista_final)
    except: return pd.DataFrame()

# --- REGRAS DE CÁLCULO (CÉREBRO DO APP 1) ---
def calcular(df_in, df_ba, h_ini, n_dia, tem_gin, sel_ups):
    def para_min(s):
        h, m = map(int, s.split(':'))
        return h * 60 + m
    
    m_ini = para_min(h_ini)
    m_alm_i, m_alm_f = para_min("11:30"), para_min("12:30")
    m_cafe_m, m_cafe_t = para_min("09:20"), para_min("15:20")
    m_gin_i, m_gin_f = para_min("09:30"), para_min("09:40")
    
    marcos = ["08:30", "09:30", "10:30", "11:30", "12:30", "13:30", "14:30", "15:30", "16:30", "17:30"]
    pontos = [h_ini] + [m for m in marcos if para_min(m) > m_ini]
    
    # Merge para pegar a cadência correta da planilha
    df_in = df_in.merge(df_ba, left_on='Equipamento', right_on='ID', how='left')
    
    def calcular_cadencia_real(row):
        n_nominal = MAPA_N_NATURAL.get(row['CEL_ORIGEM'], 5)
        return (row['UNIDADE_HORA'] / n_nominal) * n_dia

    df_in['CAD_R'] = df_in.apply(calcular_cadencia_real, axis=1)
    df_in['T_PC'] = 60 / df_in['CAD_R']
    df_in['FALTA'] = pd.to_numeric(df_in['Qtd'])
    
    res, total_ped = [], df_in['FALTA'].sum()
    acum, idx, tot, termino = 0.0, 0, 0, "Não finalizado"

    for p in range(len(pontos)-1):
        p1, p2 = para_min(pontos[p]), para_min(pontos[p+1])
        is_alm = (p1 == m_alm_i and p2 == m_alm_f)
        min_u = 0
        if not is_alm:
            for m in range(p1, p2):
                if not ((m_cafe_m <= m < m_cafe_m+10) or (m_cafe_t <= m < m_cafe_t+10) or 
                        (m_alm_i <= m < m_alm_f) or (tem_gin and m_gin_i <= m < m_gin_f)):
                    min_u += 1
        acum += min_u
        p_h, m_n = 0, []
        if is_alm:
            res.append({'Horário': f"{pontos[p]} – {pontos[p+1]}", 'Modelos': "🍱 INTERVALO", 'Peças': 0, 'Acum': int(tot)})
            continue
        while idx < len(df_in):
            t_pc = df_in.loc[idx, 'T_PC']
            if acum >= (t_pc - 0.001):
                q = min(math.floor(acum / t_pc + 0.001), df_in.loc[idx, 'FALTA'])
                if q > 0:
                    acum -= (q * t_pc); df_in.loc[idx, 'FALTA'] -= q
                    tot += q; p_h += q
                    m_n.append(f"{df_in.loc[idx, 'ID']} ({int(q)})")
                if df_in.loc[idx, 'FALTA'] <= 0: idx += 1
                else: break
            else: break
        res.append({'Horário': f"{pontos[p]} – {pontos[p+1]}", 'Modelos': " + ".join(m_n) if m_n else "-", 'Peças': int(p_h), 'Acum': int(tot)})
        if tot >= total_ped and termino == "Não finalizado" and total_ped > 0:
            sobra = min_u - acum
            dt = datetime.strptime(pontos[p], "%H:%M") + timedelta(minutes=int(sobra))
            termino = dt.strftime("%H:%M")
    return {'df': pd.DataFrame(res), 'tot': tot, 'termino': termino}

# --- INTERFACE ---
base = carregar_base()

st.sidebar.markdown("### Tecnologia de Processos")
st.sidebar.title("🏭 NHS Vision")
sel_ups = st.sidebar.selectbox("Célula de Trabalho", list(MAPA_N_NATURAL.keys()))
n_sugerido = MAPA_N_NATURAL.get(sel_ups, 5)
h_ini = st.sidebar.text_input("Início da Produção", "07:45")
n_dia = st.sidebar.number_input(f"Pessoas na {sel_ups}", 1, 20, value=n_sugerido)
tem_gin = st.sidebar.checkbox("🤸 Ginástica Laboral?")

st.header(f"📋 Planejamento NHS: {sel_ups}")

# Lógica de OCR
arquivo = st.file_uploader("Cole o print da programação aqui", type=["png", "jpg", "jpeg"])

if 'dados_lidos' not in st.session_state:
    st.session_state.dados_lidos = pd.DataFrame(columns=["Equipamento", "Qtd"])

if arquivo:
    img = Image.open(arquivo)
    if st.button("🔍 LER IMAGEM E PREENCHER TABELA"):
        with st.spinner("Processando imagem..."):
            img_np = np.array(img.convert('RGB'))
            gray = cv2.cvtColor(img_np, cv2.COLOR_RGB2GRAY)
            _, thresh = cv2.threshold(gray, 160, 255, cv2.THRESH_BINARY + cv2.THRESH_OTSU)
            texto = pytesseract.image_to_string(thresh)
            
            # Regex para buscar Modelo (85... ou 190...) e Quantidade
            modelos = re.findall(r"((?:85|190)\.[A-Z0-9\.]+)", texto)
            qtds = re.findall(r"(\d+[\.,]\d+|\d+)\s*\(un\)", texto)
            
            lista_valida = []
            for m, q in zip(modelos, qtds):
                if m in base['ID'].values:
                    lista_valida.append({"Equipamento": m, "Qtd": q})
                else:
                    st.warning(f"Atenção: Modelo {m} lido na imagem não foi encontrado na planilha BASE!")
            
            if lista_valida:
                st.session_state.dados_lidos = pd.DataFrame(lista_valida)
                st.success("Tabela preenchida com sucesso!")

# Editor de Dados (pode ser manual ou preenchido pelo OCR)
df_ed = st.data_editor(st.session_state.dados_lidos, num_rows="dynamic", use_container_width=True,
                       column_config={"Equipamento": st.column_config.TextColumn("Modelo (ID)"),
                                      "Qtd": st.column_config.NumberColumn("Qtd", min_value=1)})

if st.button("🚀 GERAR PLANEJAMENTO"):
    df_v = df_ed.dropna(subset=['Equipamento'])
    if not df_v.empty:
        r = calcular(df_v, base, h_ini, n_dia, tem_gin, sel_ups)
        st.divider()
        c1, c2 = st.columns(2)
        c1.metric("Total Planejado", f"{int(r['tot'])} pçs")
        c2.metric("Término Estimado", r['termino'])
        
        def style_row(row):
            return ['background-color: #fff3cd'] * len(row) if "INTERVALO" in str(row["Modelos"]) else [''] * len(row)
        
        st.dataframe(r['df'].style.apply(style_row, axis=1), use_container_width=True, height=450)
