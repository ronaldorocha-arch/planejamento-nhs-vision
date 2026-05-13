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

ID_PLANILHA = "11-jv_ZFetz9xdbJY8JZwPFSc3gtB65duvtDlLEk4I2E"
URL_BASE = f"https://docs.google.com/spreadsheets/d/{ID_PLANILHA}/gviz/tq?tqx=out:csv&gid=0"

MAPA_N_NATURAL = {
    "UPS - 1": 5, "UPS - 2": 3, "UPS - 3": 3, "UPS - 4": 3,
    "UPS - 6": 4, "UPS - 7": 4, "UPS - 8": 4, "ACS - 01": 3,
}

# --- 2. FUNÇÃO PARA CARREGAR A BASE ---
@st.cache_data(ttl=60)
def carregar_base():
    try:
        response = requests.get(URL_BASE, timeout=15)
        if response.status_code != 200:
            return pd.DataFrame(), f"Erro de conexão: Status {response.status_code}"
        df_raw = pd.read_csv(StringIO(response.text), header=None, quoting=1).astype(str)
        m_row, m_col = -1, -1
        for r in range(min(50, len(df_raw))):
            for c in range(len(df_raw.columns)):
                if "MODELO" in str(df_raw.iloc[r, c]).upper().strip():
                    m_row, m_col = r, c
                    break
            if m_row != -1: break
        if m_row == -1: return pd.DataFrame(), "Palavra 'MODELO' não encontrada."
        dados = df_raw.iloc[m_row+1:].copy()
        lista_final = []
        cel_atual = "Indefinida"
        for i in range(len(dados)):
            mod = str(dados.iloc[i, m_col]).strip().replace('"', '')
            if mod == 'nan' or len(mod) < 3: continue
            try:
                unid = pd.to_numeric(str(dados.iloc[i, m_col+1]).replace(',', '.').replace('"', ''), errors='coerce')
                ups_linha = str(dados.iloc[i, m_col+3]).strip().upper()
                if any(x in ups_linha for x in ["UPS", "ACS", "ACE"]):
                    cel_atual = str(dados.iloc[i, m_col+3]).strip().replace('"', '')
                if not pd.isna(unid):
                    lista_final.append({'ID': mod, 'UNIDADE_HORA': unid, 'CEL_ORIGEM': cel_atual})
            except: continue
        return pd.DataFrame(lista_final), "Sucesso"
    except Exception as e:
        return pd.DataFrame(), f"Erro: {str(e)}"

# --- 3. LOGICA DE CÁLCULO ---
def calcular_cronograma(df_in, df_ba, h_ini, n_dia, tem_gin):
    def para_min(s):
        h, m = map(int, s.split(':'))
        return h * 60 + m

    m_ini = para_min(h_ini)
    m_alm_i, m_alm_f = para_min("11:30"), para_min("12:30")
    m_cafe_m, m_cafe_t = para_min("09:20"), para_min("15:20")
    m_gin_i, m_gin_f = para_min("09:30"), para_min("09:40")
    
    marcos = ["08:30", "09:30", "10:30", "11:30", "12:30", "13:30", "14:30", "15:30", "16:30", "17:30"]
    pontos = [h_ini] + [m for m in marcos if para_min(m) > m_ini]
    
    df_proc = df_in.merge(df_ba, left_on='Equipamento', right_on='ID', how='left')
    df_proc['CAD_R'] = df_proc.apply(lambda r: (r['UNIDADE_HORA'] / MAPA_N_NATURAL.get(r['CEL_ORIGEM'], 5)) * n_dia, axis=1)
    df_proc['T_PC'] = 60 / df_proc['CAD_R']
    df_proc['FALTA'] = pd.to_numeric(df_proc['Qtd'])
    
    resultado, idx, acum, tot, h_fim = [], 0, 0.0, 0, "Finalizado"
    total_pedir = df_proc['FALTA'].sum()

    for p in range(len(pontos)-1):
        p1, p2 = para_min(pontos[p]), para_min(pontos[p+1])
        is_alm = (p1 == m_alm_i and p2 == m_alm_f)
        min_u = 0
        if not is_alm:
            for m in range(p1, p2):
                if not ((m_cafe_m <= m < m_cafe_m+10) or (m_cafe_t <= m < m_cafe_t+10) or (m_alm_i <= m < m_alm_f) or (tem_gin and m_gin_i <= m < m_gin_f)):
                    min_u += 1
        acum += min_u
        p_h, m_n = 0, []
        if is_alm:
            resultado.append({'Horário': f"{pontos[p]} - {pontos[p+1]}", 'Modelos': "🍱 ALMOÇO", 'Peças': 0, 'Acum': int(tot)})
            continue
        while idx < len(df_proc):
            t_pc = df_proc.loc[idx, 'T_PC']
            if acum >= (t_pc - 0.0001):
                q = min(math.floor(acum / t_pc + 0.0001), df_proc.loc[idx, 'FALTA'])
                if q > 0:
                    acum -= (q * t_pc); df_proc.loc[idx, 'FALTA'] -= q; tot += q; p_h += q
                    m_n.append(f"{df_proc.loc[idx, 'ID']} ({int(q)})")
                if df_proc.loc[idx, 'FALTA'] <= 0: idx += 1
                else: break
            else: break
        resultado.append({'Horário': f"{pontos[p]} - {pontos[p+1]}", 'Modelos': " + ".join(m_n) if m_n else "-", 'Peças': int(p_h), 'Acum': int(tot)})
        if tot >= total_pedir and h_fim == "Finalizado" and total_pedir > 0:
            dt = datetime.strptime(pontos[p], "%H:%M") + timedelta(minutes=int(min_u - acum))
            h_fim = dt.strftime("%H:%M")
    return pd.DataFrame(resultado), tot, h_fim

# --- INTERFACE ---
st.sidebar.title("Configurações")
if st.sidebar.button("🔄 Atualizar Planilha"):
    st.cache_data.clear()
    st.rerun()

base_dados, mensagem_base = carregar_base()
sel_ups = st.sidebar.selectbox("Célula", list(MAPA_N_NATURAL.keys()))
h_ini = st.sidebar.text_input("Início", "07:45")
n_dia = st.sidebar.number_input(f"Pessoas na {sel_ups}", 1, 25, value=MAPA_N_NATURAL.get(sel_ups, 5))
tem_gin = st.sidebar.checkbox("Ginástica Laboral?", value=True)

st.title("📸 NHS Vision - Automação Total")

if 'rows' not in st.session_state:
    st.session_state.rows = pd.DataFrame(columns=["Equipamento", "Qtd"])

arq = st.file_uploader("Suba o print aqui", type=["png", "jpg", "jpeg"])

if arq:
    img = Image.open(arq)
    if st.button("🔍 LER IMAGEM AGORA"):
        with st.spinner("Processando imagem (Verde Escuro)..."):
            img_np = np.array(img.convert('RGB'))
            img_hsv = cv2.cvtColor(img_np, cv2.COLOR_RGB2HSV)
            
            # Filtro para isolar apenas o Verde Escuro (ajustado para o print)
            low_green = np.array([35, 50, 20])
            high_green = np.array([85, 255, 150])
            mask = cv2.inRange(img_hsv, low_green, high_green)
            
            # Melhora o texto para o OCR
            kernel = np.ones((2,2), np.uint8)
            mask = cv2.dilate(mask, kernel, iterations=1)
            
            texto = pytesseract.image_to_string(mask)
            
            # Busca os códigos 85. ou 190. e as quantidades
            p_mods = re.findall(r"((?:85|190)\.[A-Z0-9\.]+)", texto)
            p_qtds = re.findall(r"(\d+)\s*\(un\)", texto)
            
            dados_v = []
            for m, q in zip(p_mods, p_qtds):
                if m in base_dados['ID'].values:
                    dados_v.append({"Equipamento": m, "Qtd": int(q)})
            
            if dados_v:
                st.session_state.rows = pd.DataFrame(dados_v)
                st.success(f"✅ {len(dados_v)} itens identificados no verde!")
            else:
                st.warning("⚠️ Não consegui ler os dados. Verifique se o print está nítido.")

st.subheader("📋 Tabela Identificada")
df_editado = st.data_editor(st.session_state.rows, num_rows="dynamic", width="stretch")

if st.button("🚀 GERAR PLANEJAMENTO"):
    if not df_editado.empty and not base_dados.empty:
        df_res, total, fim = calcular_cronograma(df_editado, base_dados, h_ini, n_dia, tem_gin)
        st.divider()
        c1, c2 = st.columns(2)
        c1.metric("Total Planejado", f"{int(total)} pçs")
        c2.metric("Término Estimado", fim)
        
        def highlight_almoco(row):
            return ['background-color: #fff3cd'] * len(row) if "ALMOÇO" in str(row["Modelos"]) else [''] * len(row)
        
        st.dataframe(df_res.style.apply(highlight_almoco, axis=1), width="stretch", height=500)
