import sys
import os
import streamlit as st

# Adiciona a pasta modules ao path
sys.path.append(os.path.join(os.path.dirname(__file__), "modules"))

from modules import module1, module2, module3

st.title("Análise INSAR Alqueva")

# --- Estado para controlar se módulo 1 já rodou ---
if 'module1_done' not in st.session_state:
    st.session_state.module1_done = False

# --- Rodar módulo 1 ---
if not st.session_state.module1_done:
    with st.spinner("Processando deslocamento médio (Módulo 1)..."):
        module1.run()
    st.session_state.module1_done = True
    st.success("Módulo 1 concluído!")

# --- Mostrar escolha dos módulos 2 e 3 após módulo 1 ---
st.sidebar.title("Escolha o módulo de análise complementar")

if st.session_state.module1_done:
    opcao = st.sidebar.radio("Módulo:", ["Top N instáveis", "Correlação nível/temperatura"])
    if st.sidebar.button("Executar módulo selecionado"):
        if opcao == "Top N instáveis":
            module2.run()
        elif opcao == "Correlação nível/temperatura":
            module3.run()






