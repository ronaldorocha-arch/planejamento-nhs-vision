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

# --- CONFIGURAÇÃO ---
st.set_page_config(page_title="NHS Vision - Automação", page_icon="🏭", layout="wide")

ID_PLANILHA = "11-jv_ZFetz9xdbJY8JZwPFSc3gtB65duvtDlLEk4I2E"
URL_BASE = f"https://docs.google.com/spreadsheets/d/{ID_PLANILHA}/export?format=csv&gid=0"

MAPA_N_NATURAL = {
    "UPS - 1": 5, "UPS - 2": 3, "UPS - 3": 3, "UPS - 4": 3,
    "UPS - 6": 4, "UPS - 7": 4, "UPS - 8": 4, "ACS - 01": 3,
}

@st.cache_data(ttl=60)
def carregar_base():
    try:
        response = requests.get(URL_BASE, timeout=15)
        df_raw = pd.read_csv(StringIO(response.text), header=None).astype(str)
        
        lista_final = []
        # VARREDURA GLOBAL: Procura modelos e cadências em qualquer lugar da planilha
        for r in range(len(df_raw)):
            for c in range(len(df_raw.columns) - 1):
                celula_val = str(df_raw.iloc[r, c]).strip()
                # Verifica se a célula tem o formato de modelo NHS (85..., 01..., 190..., 90...)
                if re.match(r"^(85|190|90|01)\.", celula_val):
                    try:
                        # Pega o número da coluna vizinha (Cadência)
                        cad_str = str(df_raw.iloc[r, c+1]).replace(',', '.')
                        num_cad = pd.to_numeric(cad_str, errors='coerce')
                        
                        if not pd.isna(num_cad) and num_cad > 0:
                            lista_final.append({'ID': celula_val, 'UNIDADE_HORA': num_cad})
                    except:
                        continue
        
        if not lista_final:
            return pd.DataFrame(), "Não foram encontrados modelos NHS com cadências válidas."
            
        return pd.DataFrame(lista_final).drop_duplicates('ID'), "Sucesso"
    except Exception as e:
        return pd.DataFrame(), f"Erro de conexão: {str(e)}"

# --- MOTOR DE CÁLCULO ---
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
    # Se não achar na base, usa 10 pç/h como segurança
    df_proc['UNIDADE_HORA'] = df_proc['UNIDADE_HORA'].fillna(10)
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

# --- INTERFACE ---
st.sidebar.title("⚙️ Painel de Controle")
base_dados, msg_base = carregar_base()

if st.sidebar.button("🔄 Sincronizar Planilha"):
    st.cache_data.clear()
    st.rerun()

sel_ups = st.sidebar.selectbox("Célula", list(MAPA_N_NATURAL.keys()))
h_ini = st.sidebar.text_input("Hora Início", "07:45")
n_dia = st.sidebar.number_input("Pessoas", 1, 30, value=MAPA_N_NATURAL.get(sel_ups, 5))

st.title("📸 NHS Vision - Automação")

if 'rows' not in st.session_state:
    st.session_state.rows = pd.DataFrame(columns=["Equipamento", "Qtd"])

arq = st.file_uploader("Arraste o print aqui", type=["png", "jpg", "jpeg"])

if arq and st.button("🔍 IDENTIFICAR PRODUTOS"):
    with st.spinner("Processando imagem..."):
        img = Image.open(arq)
        img_np = np.array(img.convert('RGB'))
        img_hsv = cv2.cvtColor(img_np, cv2.COLOR_RGB2HSV)
        # Filtro para destacar o texto no fundo verde escuro
        mask = cv2.inRange(img_hsv, np.array([35, 40, 20]), np.array([90, 255, 160]))
        texto = pytesseract.image_to_string(mask)
        
        p_mods = re.findall(r"((?:85|190|90|01)\.[A-Z0-9\.]+)", texto)
        # Captura o número que aparece antes de (un) ou un
        p_qtds = re.findall(r"(\d+)\s*\(?un\)?", texto)
        
        dados_v = []
        for m, q in zip(p_mods, p_qtds):
            dados_v.append({"Equipamento": m, "Qtd": int(q)})
        
        if dados_v:
            st.session_state.rows = pd.DataFrame(dados_v)
            st.success("✅ Produtos e quantidades lidos com sucesso!")
        else:
            st.warning("⚠️ Não encontrei dados no print. Verifique se as faixas verdes estão visíveis.")

df_editado = st.data_editor(st.session_state.rows, num_rows="dynamic", use_container_width=True)

if st.button("🚀 GERAR CRONOGRAMA DE PRODUÇÃO"):
    if not df_editado.empty:
        df_res, total, fim = calcular_cronograma(df_editado, base_dados, h_ini, n_dia)
        st.divider()
        c1, c2 = st.columns(2)
        c1.metric("Volume Total", f"{int(total)} un")
        c2.metric("Hora de Término", fim)
        st.dataframe(df_res, use_container_width=True)

if msg_base == "Sucesso":
    st.sidebar.success("✅ Base Conectada")
else:
    st.sidebar.warning(f"⚠️ {msg_base}")
