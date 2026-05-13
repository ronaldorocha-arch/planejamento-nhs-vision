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

# Link da sua planilha (Certifique-se que a aba BASE é a 1ª da esquerda)
ID_PLANILHA = "11-jv_ZFetz9xdbJY8JZwPFSc3gtB65duvtDlLEk4I2E"
URL_BASE = f"https://docs.google.com/spreadsheets/d/{ID_PLANILHA}/export?format=csv&gid=0"

MAPA_N_NATURAL = {
    "UPS - 1": 5, "UPS - 2": 3, "UPS - 3": 3, "UPS - 4": 3,
    "UPS - 6": 4, "UPS - 7": 4, "UPS - 8": 4, "ACS - 01": 3,
}

# --- 2. FUNÇÃO PARA CARREGAR A BASE (BUSCA ROBUSTA) ---
@st.cache_data(ttl=30) # Cache menor para testes
def carregar_base():
    try:
        response = requests.get(URL_BASE, timeout=15)
        if response.status_code != 200:
            st.error(f"Erro de conexão com o Google: Status {response.status_code}")
            return pd.DataFrame()
        
        df_raw = pd.read_csv(StringIO(response.text), header=None).astype(str)
        
        # Procura a célula que contém "MODELO" de forma inteligente
        m_row, m_col = -1, -1
        for r in range(min(100, len(df_raw))):
            for c in range(len(df_raw.columns)):
                valor_celula = str(df_raw.iloc[r, c]).upper().strip()
                if valor_celula == "MODELO":
                    m_row, m_col = r, c
                    break
            if m_row != -1: break
            
        if m_row == -1:
            # Se não achou, mostra o que ele leu nas primeiras células para te ajudar a depurar
            st.error(f"Palavra 'MODELO' não encontrada na 1ª aba. Verificado até a linha 100.")
            return pd.DataFrame()
        
        dados = df_raw.iloc[m_row+1:].copy()
        lista_final = []
        cel_atual = "Indefinida"
        
        for i in range(len(dados)):
            mod = str(dados.iloc[i, m_col]).strip()
            try:
                unid = pd.to_numeric(str(dados.iloc[i, m_col+1]).replace(',', '.'), errors='coerce')
                ups_linha = str(dados.iloc[i, m_col+3]).strip().upper()
                if any(x in ups_linha for x in ["UPS", "ACS", "ACE"]):
                    cel_atual = str(dados.iloc[i, m_col+3]).strip()
                if mod != 'nan' and len(mod) > 5 and not pd.isna(unid):
                    lista_final.append({'ID': mod, 'UNIDADE_HORA': unid, 'CEL_ORIGEM': cel_atual})
            except: continue
            
        return pd.DataFrame(lista_final)
    except Exception as e:
        st.error(f"Erro crítico ao processar planilha: {e}")
        return pd.DataFrame()

# --- 3. LÓGICA DE CÁLCULO ---
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
    
    # Se algum modelo não foi encontrado na base, avisa o usuário
    if df_proc['UNIDADE_HORA'].isnull().any():
        modelos_n_f = df_proc[df_proc['UNIDADE_HORA'].isnull()]['Equipamento'].tolist()
        st.error(f"Modelos não encontrados na BASE: {modelos_n_f}")
        return pd.DataFrame(), 0, "Erro"

    df_proc['CAD_R'] = df_proc.apply(lambda r: (r['UNIDADE_HORA'] / MAPA_N_NATURAL.get(r['CEL_ORIGEM'], 5)) * n_dia, axis=1)
    df_proc['T_PC'] = 60 / df_proc['CAD_R']
    df_proc['FALTA'] = pd.to_numeric(df_proc['Qtd'])
    
    resultado, idx, acum, tot, h_fim = [], 0, 0.0, 0, "Não finalizado"
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
        if tot >= total_pedir and h_fim == "Não finalizado" and total_pedir > 0:
            dt = datetime.strptime(pontos[p], "%H:%M") + timedelta(minutes=int(min_u - acum))
            h_fim = dt.strftime("%H:%M")
    return pd.DataFrame(resultado), tot, h_fim

# --- 4. INTERFACE ---
base_dados = carregar_base()

st.sidebar.title("Configurações")
sel_ups = st.sidebar.selectbox("Célula de Trabalho", list(MAPA_N_NATURAL.keys()))
h_ini = st.sidebar.text_input("Início da Produção", "07:45")
n_dia = st.sidebar.number_input(f"Pessoas na {sel_ups}", 1, 25, value=MAPA_N_NATURAL.get(sel_ups, 5))
tem_gin = st.sidebar.checkbox("Ginástica Laboral?", value=True)

st.title("🏭 NHS Vision - Automação")

if 'rows' not in st.session_state:
    st.session_state.rows = pd.DataFrame(columns=["Equipamento", "Qtd"])

arq = st.file_uploader("Suba o print da programação", type=["png", "jpg", "jpeg"])
if arq:
    img = Image.open(arq)
    if st.button("🔍 LER IMAGEM E PREENCHER"):
        if base_dados.empty:
            st.error("Planilha Base não carregada. Verifique as permissões do Google Sheets.")
        else:
            with st.spinner("Processando OCR..."):
                img_np = np.array(img.convert('RGB'))
                gray = cv2.cvtColor(img_np, cv2.COLOR_RGB2GRAY)
                _, thresh = cv2.threshold(gray, 155, 255, cv2.THRESH_BINARY + cv2.THRESH_OTSU)
                texto = pytesseract.image_to_string(thresh)
                p_mods = re.findall(r"((?:85|190)\.[A-Z0-9\.]+)", texto)
                p_qtds = re.findall(r"(\d+[\.,]\d+|\d+)\s*\(un\)", texto)
                dados_v = [{"Equipamento": m, "Qtd": int(float(q.replace(',', '.')))} for m, q in zip(p_mods, p_qtds) if m in base_dados['ID'].values]
                if dados_v:
                    st.session_state.rows = pd.DataFrame(dados_v)
                    st.success("Tabela preenchida com sucesso!")
                else:
                    st.warning("Nenhum modelo compatível encontrado na imagem.")

st.subheader("📋 Dados da Produção")
df_editado = st.data_editor(st.session_state.rows, num_rows="dynamic", width="stretch")

if st.button("🚀 GERAR CRONOGRAMA"):
    if not df_editado.empty and not base_dados.empty:
        df_res, total, fim = calcular_cronograma(df_editado, base_dados, h_ini, n_dia, tem_gin)
        if fim != "Erro":
            st.divider()
            c1, c2 = st.columns(2)
            c1.metric("Total Peças", f"{int(total)} un")
            c2.metric("Término Estimado", fim)
            st.dataframe(df_res.style.apply(lambda r: ['background-color: #f8d7da']*len(r) if "ALMOÇO" in str(r["Modelos"]) else ['']*len(r), axis=1), width="stretch", height=500)
    else:
        st.error("Tabela vazia ou Base de dados não carregada.")
