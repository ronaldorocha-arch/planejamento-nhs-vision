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

# --- 1. CONFIGURAÇÃO ---
st.set_page_config(page_title="NHS Vision - Automação Total", page_icon="🏭", layout="wide")

ID_PLANILHA = "11-jv_ZFetz9xdbJY8JZwPFSc3gtB65duvtDlLEk4I2E"
URL_BASE = f"https://docs.google.com/spreadsheets/d/{ID_PLANILHA}/export?format=csv&gid=0"

MAPA_N_NATURAL = {
    "UPS - 1": 5, "UPS - 2": 3, "UPS - 3": 3, "UPS - 4": 3,
    "UPS - 6": 4, "UPS - 7": 4, "UPS - 8": 4, "ACS - 01": 3,
}

# CACHE DE APENAS 1 SEGUNDO PARA GARANTIR ATUALIZAÇÃO REAL
@st.cache_data(ttl=1) 
def carregar_base():
    try:
        response = requests.get(URL_BASE, timeout=15)
        df_raw = pd.read_csv(StringIO(response.text), header=None).astype(str)
        lista_final = []
        for r in range(len(df_raw)):
            for c in range(len(df_raw.columns) - 1):
                celula_val = str(df_raw.iloc[r, c]).strip()
                # Pega qualquer código que comece com os padrões NHS
                if re.match(r"^(85|190|90|01|05)\.", celula_val):
                    try:
                        cad_str = str(df_raw.iloc[r, c+1]).replace(',', '.')
                        num_cad = pd.to_numeric(cad_str, errors='coerce')
                        if not pd.isna(num_cad) and num_cad > 0:
                            lista_final.append({'ID': celula_val, 'UNIDADE_HORA': num_cad})
                    except: continue
        
        df_res = pd.DataFrame(lista_final).drop_duplicates('ID')
        return df_res, f"✅ Base Sincronizada: {len(df_res)} modelos ativos."
    except Exception as e:
        return pd.DataFrame(), f"❌ Erro ao conectar: {str(e)}"

# --- 2. MOTOR DE CÁLCULO ---
def calcular_cronograma(df_in, df_ba, h_ini, n_dia):
    def para_min(s):
        h, m = map(int, s.split(':'))
        return h * 60 + m

    m_ini = para_min(h_ini)
    m_alm_i, m_alm_f = para_min("11:30"), para_min("12:30")
    m_cafe_m, m_cafe_t = para_min("09:20"), para_min("15:20")
    
    marcos = ["08:30", "09:30", "10:30", "11:30", "12:30", "13:30", "14:30", "15:30", "16:30", "17:30"]
    pontos = [h_ini] + [m for m in marcos if para_min(m) > m_ini]
    
    df_proc = df_in.merge(df_ba, left_on='Equipamento', right_on='ID', how='left')
    df_proc['UNIDADE_HORA'] = df_proc['UNIDADE_HORA'].fillna(0)
    df_proc['T_PC'] = df_proc['UNIDADE_HORA'].apply(lambda x: 60/x if x > 0 else 0)
    df_proc['FALTA'] = pd.to_numeric(df_proc['Qtd'], errors='coerce').fillna(0)
    
    resultado, idx, acum, tot, h_fim = [], 0, 0.0, 0, "Finalizado"
    total_pedir = df_proc['FALTA'].sum()

    for p in range(len(pontos)-1):
        p1, p2 = para_min(pontos[p]), para_min(pontos[p+1])
        is_alm = (p1 == m_alm_i and p2 == m_alm_f)
        min_u = 0
        if not is_alm:
            for m in range(p1, p2):
                if not ((m_cafe_m <= m < m_cafe_m+10) or (m_cafe_t <= m < m_cafe_t+10) or (m_alm_i <= m < m_alm_f)):
                    min_u += 1
        acum += min_u
        p_h, m_n = 0, []
        if is_alm:
            resultado.append({'Horário': f"{pontos[p]} - {pontos[p+1]}", 'Modelos': "🍱 ALMOÇO", 'Peças': 0, 'Acum': int(tot)})
            continue
        while idx < len(df_proc):
            t_pc = df_proc.loc[idx, 'T_PC']
            if t_pc > 0 and acum >= (t_pc - 0.0001):
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

# --- 3. INTERFACE ---
st.sidebar.title("⚙️ Painel de Controle")
base_dados, msg_base = carregar_base()

if st.sidebar.button("🔄 FORÇAR ATUALIZAÇÃO DA BASE"):
    st.cache_data.clear()
    st.rerun()

sel_ups = st.sidebar.selectbox("Célula", list(MAPA_N_NATURAL.keys()))
h_ini = st.sidebar.text_input("Hora Início", "07:45")
n_dia = st.sidebar.number_input("Pessoas", 1, 30, value=MAPA_N_NATURAL.get(sel_ups, 5))

st.title("📸 NHS Vision - Automação Total")
st.sidebar.info(msg_base)

if 'rows' not in st.session_state:
    st.session_state.rows = pd.DataFrame(columns=["Equipamento", "Qtd"])

arq = st.file_uploader("Suba o print das faixas verdes", type=["png", "jpg", "jpeg"])

if arq and st.button("🔍 IDENTIFICAR E VALIDAR"):
    with st.spinner("Analisando imagem e conferindo cadastro..."):
        img = Image.open(arq)
        img_np = np.array(img.convert('RGB'))
        img_hsv = cv2.cvtColor(img_np, cv2.COLOR_RGB2HSV)
        # Isola o verde das faixas de programação
        mask = cv2.inRange(img_hsv, np.array([35, 40, 20]), np.array([90, 255, 160]))
        
        contours, _ = cv2.findContours(mask, cv2.RETR_EXTERNAL, cv2.CHAIN_APPROX_SIMPLE)
        contours = sorted(contours, key=lambda c: cv2.boundingRect(c)[1])
        
        dados_lidos = []
        faltando = []
        
        for cnt in contours:
            x, y, w, h = cv2.boundingRect(cnt)
            if w > 80 and h > 10:
                roi = mask[y:y+h, x:x+w]
                text = pytesseract.image_to_string(roi, config='--psm 7')
                
                # Regex mais amplo para pegar modelos longos
                mod_match = re.search(r"((?:85|190|90|01|05)\.[A-Z0-9\.]+)", text)
                qtd_match = re.search(r"(\d+[\.,]?\d*)\s*\(un\)", text)
                
                if mod_match and qtd_match:
                    modelo = mod_match.group(1).strip()
                    quantidade = int(float(qtd_match.group(1).replace(',', '.')))
                    
                    if quantidade > 0:
                        # VALIDAÇÃO OBRIGATÓRIA NA PLANILHA
                        if modelo in base_dados['ID'].values:
                            dados_lidos.append({"Equipamento": modelo, "Qtd": quantidade})
                        else:
                            faltando.append(modelo)

        # MOSTRAR ERRO SE FALTAR CADASTRO
        if faltando:
            lista_final_faltante = sorted(list(set(faltando)))
            st.error(f"🛑 BLOQUEADO: {len(lista_final_faltante)} equipamentos NÃO estão na planilha!")
            st.warning("Adicione estes códigos na aba BASE e clique em 'FORÇAR ATUALIZAÇÃO':")
            for item in lista_final_faltante:
                st.code(item)
            st.session_state.rows = pd.DataFrame(columns=["Equipamento", "Qtd"])
        elif dados_lidos:
            st.session_state.rows = pd.DataFrame(dados_lidos).drop_duplicates()
            st.success(f"✅ {len(st.session_state.rows)} equipamentos validados com sucesso!")
        else:
            st.warning("⚠️ Nenhuma faixa verde reconhecida ou modelos sem '(un)'.")

st.subheader("📋 Tabela Identificada")
df_editado = st.data_editor(st.session_state.rows, num_rows="dynamic", use_container_width=True)

if st.button("🚀 GERAR CRONOGRAMA"):
    if not df_editado.empty:
        df_res, total, fim = calcular_cronograma(df_editado, base_dados, h_ini, n_dia)
        st.divider()
        st.metric("Volume Total", f"{int(total)} un")
        st.metric("Término Previsto", fim)
        st.dataframe(df_res, use_container_width=True)
