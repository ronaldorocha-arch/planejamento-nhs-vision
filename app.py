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

# --- 1. CONFIGURACAO DA PAGINA ---
st.set_page_config(page_title="NHS Vision - Planejamento", page_icon="🏭", layout="wide")

ID_PLANILHA = "11-jv_ZFetz9xdbJY8JZwPFSc3gtB65duvtDlLEk4I2E"
URL_BASE = f"https://docs.google.com/spreadsheets/d/{ID_PLANILHA}/export?format=csv&gid=0"

MAPA_N_NATURAL = {
    "UPS - 1": 5, "UPS - 2": 3, "UPS - 3": 3, "UPS - 4": 3,
    "UPS - 6": 4, "UPS - 7": 4, "UPS - 8": 4, "ACS - 01": 3,
}

# --- 2. FUNCAO PARA CARREGAR A BASE ---
@st.cache_data(ttl=60)
def carregar_base():
    try:
        response = requests.get(URL_BASE, timeout=15)
        if response.status_code != 200:
            return pd.DataFrame()
        df_raw = pd.read_csv(StringIO(response.text), header=None).astype(str)

        m_row, m_col = -1, -1
        for r in range(min(100, len(df_raw))):
            for c in range(len(df_raw.columns)):
                if "MODELO" in str(df_raw.iloc[r, c]).upper().strip():
                    m_row, m_col = r, c
                    break
            if m_row != -1:
                break

        if m_row == -1:
            return pd.DataFrame()

        dados = df_raw.iloc[m_row + 1:].copy()
        lista_final = []
        cel_atual = "Indefinida"

        for i in range(len(dados)):
            mod = str(dados.iloc[i, m_col]).strip()
            try:
                unid = pd.to_numeric(str(dados.iloc[i, m_col + 1]).replace(',', '.'), errors='coerce')
                ups_linha = str(dados.iloc[i, m_col + 3]).strip().upper()
                if any(x in ups_linha for x in ["UPS", "ACS", "ACE"]):
                    cel_atual = str(dados.iloc[i, m_col + 3]).strip()
                if mod != 'nan' and len(mod) > 5 and not pd.isna(unid):
                    lista_final.append({'ID': mod, 'UNIDADE_HORA': unid, 'CEL_ORIGEM': cel_atual})
            except:
                continue

        return pd.DataFrame(lista_final)
    except:
        return pd.DataFrame()


# --- 3. LOGICA DE CALCULO ---
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
    df_proc['CAD_R'] = df_proc.apply(
        lambda r: (r['UNIDADE_HORA'] / MAPA_N_NATURAL.get(r['CEL_ORIGEM'], 5)) * n_dia, axis=1
    )
    df_proc['T_PC'] = 60 / df_proc['CAD_R']
    df_proc['FALTA'] = pd.to_numeric(df_proc['Qtd'])

    resultado, idx, acum, tot, h_fim = [], 0, 0.0, 0, "Nao finalizado"
    total_pedir = df_proc['FALTA'].sum()

    for p in range(len(pontos) - 1):
        p1, p2 = para_min(pontos[p]), para_min(pontos[p + 1])
        is_alm = (p1 == m_alm_i and p2 == m_alm_f)
        min_u = 0
        if not is_alm:
            for m in range(p1, p2):
                in_cafe = (m_cafe_m <= m < m_cafe_m + 10) or (m_cafe_t <= m < m_cafe_t + 10)
                in_alm = m_alm_i <= m < m_alm_f
                in_gin = tem_gin and m_gin_i <= m < m_gin_f
                if not in_cafe and not in_alm and not in_gin:
                    min_u += 1
        acum += min_u
        p_h, m_n = 0, []
        if is_alm:
            resultado.append({
                'Horario': f"{pontos[p]} - {pontos[p + 1]}",
                'Modelos': "Almoco",
                'Pecas': 0,
                'Acum': int(tot)
            })
            continue
        guard = 0
        while idx < len(df_proc) and guard < 999999:
            guard += 1
            t_pc = df_proc.loc[idx, 'T_PC']
            if acum >= (t_pc - 0.00001):
                q = min(math.floor(acum / t_pc + 0.00001), df_proc.loc[idx, 'FALTA'])
                if q > 0:
                    acum -= (q * t_pc)
                    df_proc.loc[idx, 'FALTA'] -= q
                    tot += q
                    p_h += q
                    m_n.append(f"{df_proc.loc[idx, 'ID']} ({int(q)})")
                if df_proc.loc[idx, 'FALTA'] <= 0:
                    idx += 1
                else:
                    break
            else:
                break
        resultado.append({
            'Horario': f"{pontos[p]} - {pontos[p + 1]}",
            'Modelos': " + ".join(m_n) if m_n else "-",
            'Pecas': int(p_h),
            'Acum': int(tot)
        })
        if tot >= total_pedir and h_fim == "Nao finalizado" and total_pedir > 0:
            sobrou = int(min_u - max(0, math.ceil(acum)))
            dt = datetime.strptime(pontos[p], "%H:%M") + timedelta(minutes=sobrou)
            h_fim = dt.strftime("%H:%M")

    return pd.DataFrame(resultado), tot, h_fim


# --- 4. INTERFACE ---
base_dados = carregar_base()

st.sidebar.title("Configuracoes")
sel_ups = st.sidebar.selectbox("Celula", list(MAPA_N_NATURAL.keys()))
h_ini = st.sidebar.text_input("Inicio", "07:45")
n_dia = st.sidebar.number_input(
    f"Pessoas na {sel_ups}", 1, 25, value=MAPA_N_NATURAL.get(sel_ups, 5)
)
tem_gin = st.sidebar.checkbox("Ginastica Laboral?", value=True)

st.title("NHS Vision - Automacao")

if base_dados.empty:
    st.warning("Planilha BASE nao carregada. Verifique o ID da planilha e se ela esta publica.")

if 'rows' not in st.session_state:
    st.session_state.rows = pd.DataFrame(columns=["Equipamento", "Qtd"])

arq = st.file_uploader("Suba o print", type=["png", "jpg", "jpeg"])
if arq:
    img = Image.open(arq)
    st.image(img, caption="Imagem carregada", use_column_width=True)
    if st.button("LER IMAGEM E PREENCHER"):
        if base_dados.empty:
            st.error("Planilha Base nao carregada.")
        else:
            with st.spinner("Lendo imagem..."):
                img_np = np.array(img.convert('RGB'))
                gray = cv2.cvtColor(img_np, cv2.COLOR_RGB2GRAY)
                _, thresh = cv2.threshold(gray, 155, 255, cv2.THRESH_BINARY + cv2.THRESH_OTSU)
                texto = pytesseract.image_to_string(thresh)
                p_mods = re.findall(r"((?:85|190)\.[A-Z0-9\.]+)", texto)
                p_qtds = re.findall(r"(\d+[\.,]\d+|\d+)\s*\(un\)", texto)
                dados_v = [
                    {"Equipamento": m, "Qtd": int(float(q.replace(',', '.')))}
                    for m, q in zip(p_mods, p_qtds)
                    if m in base_dados['ID'].values
                ]
                if dados_v:
                    st.session_state.rows = pd.DataFrame(dados_v)
                    st.success(f"{len(dados_v)} item(ns) encontrado(s) na imagem!")
                else:
                    st.warning("Nenhum item reconhecido na imagem. Verifique a qualidade do print.")

st.subheader("Dados para o Calculo")
df_editado = st.data_editor(st.session_state.rows, num_rows="dynamic", use_container_width=True)

if st.button("GERAR CRONOGRAMA"):
    if not df_editado.empty:
        df_res, total, fim = calcular_cronograma(df_editado, base_dados, h_ini, n_dia, tem_gin)
        st.divider()
        c1, c2 = st.columns(2)
        c1.metric("Total Pecas", f"{int(total)} un")
        c2.metric("Termino", fim)          # BUG CORRIGIDO: era col2.metric

        def highlight_almoco(row):
            if "Almoco" in str(row["Modelos"]):
                return ['background-color: #e6f1fb'] * len(row)
            return [''] * len(row)

        st.dataframe(
            df_res.style.apply(highlight_almoco, axis=1),
            use_container_width=True,
            height=500
        )
    else:
        st.error("Tabela vazia! Adicione ordens de producao.")
