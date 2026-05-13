import os

# Define the content of app.py
app_content = """import streamlit as st
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

# CSS para melhorar a aparência
st.markdown(\"\"\"
    <style>
    .main {
        background-color: #f5f7f9;
    }
    .stMetric {
        background-color: #ffffff;
        padding: 15px;
        border-radius: 10px;
        box-shadow: 0 2px 4px rgba(0,0,0,0.05);
    }
    [data-testid=\"stMetricValue\"] {
        color: #1f77b4;
    }
    </style>
    \"\"\", unsafe_allow_html=True)

# Link da planilha NHS
ID_PLANILHA = "11-jv_ZFetz9xdbJY8JZwPFSc3gtB65duvtDlLEk4I2E"
URL_BASE = f"https://docs.google.com/spreadsheets/d/{ID_PLANILHA}/gviz/tq?tqx=out:csv&gid=0"

# Mapeamento de pessoas por célula (Padrão)
MAPA_N_NATURAL = {
    "UPS - 1": 5, "UPS - 2": 3, "UPS - 3": 3, "UPS - 4": 3,
    "UPS - 6": 4, "UPS - 7": 4, "UPS - 8": 4, "ACS - 01": 3,
}

# --- 2. FUNÇÃO PARA CARREGAR A BASE DA PLANILHA ---
@st.cache_data(ttl=60)
def carregar_base():
    try:
        response = requests.get(URL_BASE, timeout=15)
        if response.status_code != 200:
            return pd.DataFrame(), f"Erro de conexão: Status {response.status_code}"
        
        # Lê o CSV da planilha
        df_raw = pd.read_csv(StringIO(response.text), header=None, quoting=1).astype(str)
        
        # Localiza a linha de cabeçalho "MODELO"
        m_row, m_col = -1, -1
        for r in range(min(50, len(df_raw))):
            for c in range(len(df_raw.columns)):
                if "MODELO" in str(df_raw.iloc[r, c]).upper().strip():
                    m_row, m_col = r, c
                    break
            if m_row != -1: break
            
        if m_row == -1:
            return pd.DataFrame(), "Palavra 'MODELO' não encontrada na aba BASE."
        
        dados = df_raw.iloc[m_row+1:].copy()
        lista_final = []
        cel_atual = "Indefinida"
        
        for i in range(len(dados)):
            mod = str(dados.iloc[i, m_col]).strip().replace('"', '')
            if mod == 'nan' or len(mod) < 3: continue
            
            try:
                # Extração da Unidade/Hora
                unid_str = str(dados.iloc[i, m_col+1]).replace(',', '.').replace('"', '')
                unid = pd.to_numeric(unid_str, errors='coerce')
                
                # Extração da Célula de Origem
                ups_linha = str(dados.iloc[i, m_col+3]).strip().upper()
                if any(x in ups_linha for x in ["UPS", "ACS", "ACE"]):
                    cel_atual = str(dados.iloc[i, m_col+3]).strip().replace('"', '')
                
                if not pd.isna(unid):
                    lista_final.append({'ID': mod, 'UNIDADE_HORA': unid, 'CEL_ORIGEM': cel_atual})
            except: continue
            
        return pd.DataFrame(lista_final), "Sucesso"
    except Exception as e:
        return pd.DataFrame(), f"Erro crítico: {str(e)}"

# --- 3. LÓGICA DE CÁLCULO DO CRONOGRAMA ---
def calcular_cronograma(df_in, df_ba, h_ini, n_dia, tem_gin):
    def para_min(s):
        h, m = map(int, s.split(':'))
        return h * 60 + m

    m_ini = para_min(h_ini)
    m_alm_i, m_alm_f = para_min("11:30"), para_min("12:30")
    m_cafe_m, m_cafe_t = para_min("09:20"), para_min("15:20")
    m_gin_i, m_gin_f = para_min("09:30"), para_min("09:40")
    
    # Marcos de exibição (de hora em hora)
    marcos = ["08:30", "09:30", "10:30", "11:30", "12:30", "13:30", "14:30", "15:30", "16:30", "17:30"]
    pontos = [h_ini] + [m for m in marcos if para_min(m) > m_ini]
    
    # Merge com a base de dados
    df_proc = df_in.merge(df_ba, left_on='Equipamento', right_on='ID', how='left')
    
    # Cálculo da Cadência Real e Tempo por Peça
    # Fórmula: (Unidade Hora / Pessoas Base) * Pessoas Atuais
    df_proc['CAD_R'] = df_proc.apply(
        lambda r: (r['UNIDADE_HORA'] / MAPA_N_NATURAL.get(r['CEL_ORIGEM'], 5)) * n_dia 
        if pd.notnull(r['UNIDADE_HORA']) else 0, axis=1
    )
    df_proc['T_PC'] = df_proc['CAD_R'].apply(lambda x: 60/x if x > 0 else 0)
    df_proc['FALTA'] = pd.to_numeric(df_proc['Qtd'])
    
    resultado, idx, acum, tot, h_fim = [], 0, 0.0, 0, "Finalizado"
    total_pedir = df_proc['FALTA'].sum()

    for p in range(len(pontos)-1):
        p1, p2 = para_min(pontos[p]), para_min(pontos[p+1])
        is_alm = (p1 == m_alm_i and p2 == m_alm_f)
        
        min_u = 0
        if not is_alm:
            for m in range(p1, p2):
                # Descontar Café, Almoço e Ginástica
                if not ((m_cafe_m <= m < m_cafe_m+10) or 
                        (m_cafe_t <= m < m_cafe_t+10) or 
                        (m_alm_i <= m < m_alm_f) or 
                        (tem_gin and m_gin_i <= m < m_gin_f)):
                    min_u += 1
        
        acum += min_u
        p_h, m_n = 0, []
        
        if is_alm:
            resultado.append({'Horário': f"{pontos[p]} - {pontos[p+1]}", 'Modelos': "🍱 INTERVALO DE ALMOÇO", 'Peças': 0, 'Acum': int(tot)})
            continue
            
        while idx < len(df_proc):
            t_pc = df_proc.loc[idx, 'T_PC']
            if t_pc > 0 and acum >= (t_pc - 0.0001):
                q = min(math.floor(acum / t_pc + 0.0001), df_proc.loc[idx, 'FALTA'])
                if q > 0:
                    acum -= (q * t_pc)
                    df_proc.loc[idx, 'FALTA'] -= q
                    tot += q
                    p_h += q
                    m_n.append(f"{df_proc.loc[idx, 'ID']} ({int(q)})")
                if df_proc.loc[idx, 'FALTA'] <= 0: idx += 1
                else: break
            else: break
            
        resultado.append({'Horário': f"{pontos[p]} - {pontos[p+1]}", 'Modelos': " + ".join(m_n) if m_n else "-", 'Peças': int(p_h), 'Acum': int(tot)})
        
        # Marcar horário de término
        if tot >= total_pedir and h_fim == "Finalizado" and total_pedir > 0:
            minutos_usados = min_u - acum
            dt = datetime.strptime(pontos[p], "%H:%M") + timedelta(minutes=int(minutos_usados))
            h_fim = dt.strftime("%H:%M")
            
    return pd.DataFrame(resultado), tot, h_fim

# --- 4. INTERFACE ---
st.sidebar.title("⚙️ Configurações")
if st.sidebar.button("🔄 Atualizar Base (Planilha)"):
    st.cache_data.clear()
    st.rerun()

base_dados, msg_base = carregar_base()

if base_dados.empty:
    st.sidebar.error(f"❌ {msg_base}")
else:
    st.sidebar.success("✅ Planilha Base Conectada")

sel_ups = st.sidebar.selectbox("Célula de Trabalho", list(MAPA_N_NATURAL.keys()))
h_ini = st.sidebar.text_input("Início da Produção (HH:MM)", "07:45")
n_dia = st.sidebar.number_input(f"Pessoas na {sel_ups}", 1, 25, value=MAPA_N_NATURAL.get(sel_ups, 5))
tem_gin = st.sidebar.checkbox("Ginástica Laboral (09:30)?", value=True)

st.title("📸 NHS Vision - Automação de Planejamento")
st.caption("Suba o print da tela de programação para leitura automática dos códigos (verde escuro).")

if 'rows' not in st.session_state:
    st.session_state.rows = pd.DataFrame(columns=["Equipamento", "Qtd"])

# Upload da Imagem
arq = st.file_uploader("Suba o print aqui", type=["png", "jpg", "jpeg"])

if arq:
    img = Image.open(arq)
    st.image(img, caption="Imagem carregada", width=400)
    
    if st.button("🔍 LER IMAGEM E PREENCHER TABELA"):
        if base_dados.empty:
            st.error("Impossível prosseguir: Planilha Base não carregada.")
        else:
            with st.spinner("Processando OCR no Verde Escuro..."):
                img_np = np.array(img.convert('RGB'))
                img_hsv = cv2.cvtColor(img_np, cv2.COLOR_RGB2HSV)
                
                # MÁSCARA HSV PARA O VERDE ESCURO (Ajustado para o print da NHS)
                low_green = np.array([35, 40, 20])
                high_green = np.array([90, 255, 160])
                mask = cv2.inRange(img_hsv, low_green, high_green)
                
                # Melhora a imagem antes do OCR
                kernel = np.ones((2,2), np.uint8)
                mask = cv2.dilate(mask, kernel, iterations=1)
                
                # OCR com Tesseract
                texto = pytesseract.image_to_string(mask)
                
                # Regex para extrair códigos (85. ou 190.) e quantidades (X(un))
                p_mods = re.findall(r"((?:85|190)\.[A-Z0-9\.]+)", texto)
                p_qtds = re.findall(r"(\d+)\s*\(un\)", texto)
                
                dados_v = []
                for m, q in zip(p_mods, p_qtds):
                    # Valida se o modelo lido existe na planilha base
                    if m in base_dados['ID'].values:
                        dados_v.append({"Equipamento": m, "Qtd": int(q)})
                
                if dados_v:
                    st.session_state.rows = pd.DataFrame(dados_v)
                    st.success(f"✅ Sucesso! {len(dados_v)} itens identificados.")
                else:
                    st.warning("⚠️ Nenhum modelo compatível encontrado no verde escuro. Verifique a nitidez do print.")

st.divider()
st.subheader("📋 Dados Identificados para o Cálculo")
df_editado = st.data_editor(st.session_state.rows, num_rows="dynamic", width="stretch")

if st.button("🚀 GERAR PLANEJAMENTO FINAL"):
    if not df_editado.empty and not base_dados.empty:
        df_res, total, fim = calcular_cronograma(df_editado, base_dados, h_ini, n_dia, tem_gin)
        
        st.divider()
        c1, c2 = st.columns(2)
        c1.metric("Total de Peças", f"{int(total)} un")
        c2.metric("Previsão de Término", fim)
        
        # Estilização da tabela de saída
        def highlight_special(row):
            if "INTERVALO" in str(row["Modelos"]):
                return ['background-color: #fff3cd'] * len(row)
            if row["Peças"] > 0:
                return ['background-color: #e3f2fd'] * len(row)
            return [''] * len(row)

        st.dataframe(df_res.style.apply(highlight_special, axis=1), width="stretch", height=550)
    else:
        st.error("A tabela está vazia. Adicione itens manualmente ou use a leitura por imagem.")
\"\"\"

with open("app.py", "w") as f:
    f.write(app_content)

print("File app.py created successfully.")
