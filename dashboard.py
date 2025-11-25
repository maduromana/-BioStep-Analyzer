import streamlit as st
import pandas as pd
import plotly.express as px
import tempfile
import os
import cv2
import numpy as np
from datetime import datetime
from fpdf import FPDF
from streamlit_image_coordinates import streamlit_image_coordinates
from biostep_engine import AnalisadorBioStep, refinar_ponto_pela_cor

# Configuração da Página
st.set_page_config(page_title="BioStep Analyzer", layout="wide", page_icon="🦵")

# CSS para centralizar a imagem de clique
st.markdown("""
    <style>
        div[data-testid="stImage"] {display: block; margin-left: auto; margin-right: auto;}
    </style>
""", unsafe_allow_html=True)

st.title("BioStep Analyzer – Plataforma de Avaliação Biomecânica")
st.markdown("Sistema de análise biomecânica baseada em visão computacional para o teste **Step Down**.")

# ---- Menu Lateral ----
st.sidebar.image("logo.png", use_container_width=True)
st.sidebar.header("Navegação")
# opções do menu
OPT_INICIO = "🏠 Início"
OPT_COMO_USAR = "📖 Como Usar"
OPT_METODOLOGIA = "📐 Metodologia"
OPT_INDIVIDUAL = "📂 Análise Individual"
OPT_COMPARACAO = "🔄 Comparação (Antes/Depois)"

opcao_menu = st.sidebar.radio(
    "Escolha uma opção:",
    [OPT_INICIO, OPT_COMO_USAR, OPT_METODOLOGIA, OPT_INDIVIDUAL, OPT_COMPARACAO]
)

# Função para salvar vídeo
def salvar_temp(uploaded_file):
    if uploaded_file is not None:
        tfile = tempfile.NamedTemporaryFile(delete=False, suffix='.mp4')
        tfile.write(uploaded_file.read())
        return tfile.name
    return None

#Função PDF
class  PDFReport(FPDF):
    def header(self):
        self.set_font('Arial', 'B', 12)
        self.cell(0, 10, 'Relatório BioStep Analyzer', 0, 1, 'C')

    def footer(self):
        self.set_y(-15)
        self.set_font('Arial', 'I', 8)
        self.cell(0, 10, f'Página {self.page_no()}', 0, 0, 'C')

#Função para gerar relatório PDF
def gerar_pdf(nome_paciente, df, fig_ang,fig_desvio, fig_pelve, tipo_analise="Individual"):
    pdf = PDFReport()
    pdf.add_page()
    pdf.set_font("Arial", size=12)

    #  dados do paciente
    pdf.set_font("Arial", 'B', 12)
    pdf.cell(0,10, f"Paciente: {nome_paciente}", 0,1)
    pdf.cell(0,10, f"Data: {datetime.now().strftime('%d/%m/%Y')}", 0,1)
    pdf.cell(0,10, f"Tipo de Análise: {tipo_analise}", 0,1)
    
    # resumo dos dados
    pdf.set_font("Arial", 'B', 14)
    pdf.cell(0, 10, 'Resumo das Métricas Principais', 0, 1)
    pdf.set_font("Arial", size=11)

    # extrair metricas dependendo  do tipo de análise
    if 'Periodo' in df.columns: # Comparação
        valgo_antes = df[df['Periodo']=='Antes']['Angulo Joelho'].min()
        valgo_depois = df[df['Periodo']=='Depois']['Angulo Joelho'].min()
        pdf.cell(0, 8, f"Angulo Minimo (Antes): {valgo_antes:.1f} graus", 0, 1)
        pdf.cell(0, 8, f"Angulo Minimo (Depois): {valgo_depois:.1f} graus", 0, 1)
        pdf.cell(0, 8, f"Evolucao: {valgo_depois - valgo_antes:.1f} graus", 0, 1)
    else: # Individual
        pdf.cell(0, 8, f"Angulo Minimo de Valgo: {df['Angulo Joelho'].min():.1f} graus", 0, 1)
        pdf.cell(0, 8, f"Desvio Medial Maximo: {df['Desvio Valgo (px)'].max():.1f} px", 0, 1)
        pdf.cell(0, 8, f"Queda Pelvica Maxima: {abs(df['Queda Pelvica'].max() - 180):.1f} graus", 0, 1)
    
    pdf.ln(5)
    
    # salvar e inserir graficos
    imgs = []
    for fig in [fig_ang, fig_desvio, fig_pelve]:
        if fig:
            with tempfile.NamedTemporaryFile(delete=False, suffix=".png") as tmp:
                fig.write_image(tmp.name, width=800, height=400) # Requer 'kaleido'
                imgs.append(tmp.name)
                pdf.image(tmp.name, x=10, w=190)
                pdf.ln(5)
    
    # limpar imagens temporárias
    for img in imgs:
        os.remove(img)
        
    return pdf.output(dest='S').encode('latin-1')

# ------ Interface de Marcação de Pontos com Correção ------
def interface_marcador_pontos(video_path, key_suffix):
 
    if f'pontos_{key_suffix}' not in st.session_state:
        st.session_state[f'pontos_{key_suffix}'] = []
    
    pontos = st.session_state[f'pontos_{key_suffix}']
    nomes_pontos = ["1. Esterno", "2. Quadril Dir", "3. Quadril Esq", "4. Joelho (Apoio)", "5. Tornozelo"]
    
    # cria analisador para pegar frames
    analise = AnalisadorBioStep(video_path)
    frame_bgr = analise.frame_inicial # Usado para o cálculo (OpenCV - BGR)
    frame_rgb = analise.get_frame_inicial_rgb() # Usado para exibir (Streamlit - RGB)
    
    # desenha os pontos já marcados
    img_display = frame_rgb.copy()
    for i, p in enumerate(pontos):
        # Desenha um alvo verde onde o ponto foi salvo
        cv2.circle(img_display, p, 5, (0, 255, 0), -1) 
        cv2.circle(img_display, p, 10, (0, 255, 0), 1) 
        cv2.putText(img_display, str(i+1), (p[0]+10, p[1]), cv2.FONT_HERSHEY_SIMPLEX, 0.8, (255, 255, 255), 2)

    # total de pontos = 5, se não completou, pede próximo ponto
    if len(pontos) < 5:
        st.warning(f"📍 Clique no ponto: **{nomes_pontos[len(pontos)]}** (O sistema ajustará para o centro amarelo)")
        
        # capta coordenadas do clique
        value = streamlit_image_coordinates(img_display, key=f"clicker_{key_suffix}")
        
        if value is not None:
            x_click = value['x']
            y_click = value['y']
            
            # --- Ajuste automatico ("IMÃ") ---
            # BGR original --> função matemática procurar o amarelo
            x_refinado, y_refinado = refinar_ponto_pela_cor(frame_bgr, x_click, y_click)
            
            novo_ponto = (x_refinado, y_refinado)
            
            # verifica se é um novo clique para evitar loops do Streamlit
            if not pontos or pontos[-1] != novo_ponto:
                pontos.append(novo_ponto)
                st.rerun() # Recarrega para mostrar o ponto corrigido
    else:
        st.success("✅ Todos os pontos marcados!")
        st.image(img_display, caption="Pontos Definidos")
        
        col1, col2 = st.columns(2)
        if col1.button("🗑️ Limpar Pontos", key=f"clean_{key_suffix}"):
            st.session_state[f'pontos_{key_suffix}'] = []
            st.rerun()
            
        return pontos 
    
    return None

# --- LÓGICA DO DASHBOARD ---

if opcao_menu == OPT_INICIO:
    st.header("🏠 Bem-vindo ao BioStep Analyzer!")
    st.markdown("""
    O **BioStep Analyzer** é uma ferramenta desenvolvida para auxiliar profissionais de saúde na avaliação do **valgismo dinâmico**.
    
    ### Funcionalidades Principais:
    - **Rastreamento de Pontos:** Identificação de pontos com **ajuste automático** (imã de cor).
    - **Métricas Biomecânicas:** Cálculo de ângulo do joelho, desvio medial e queda pélvica.
    - **Comparação:** Avaliação do progresso (Antes vs Depois).
    """)

elif opcao_menu == OPT_COMO_USAR:
    st.header("📖 Guia de Uso")
    st.markdown("""
    1. **Carregue o Vídeo:** Na aba de análise.
    2. **Marque os Pontos:** Clique **próximo** ao adesivo amarelo. 
       * O sistema detectará automaticamente o centro da bolinha amarela para garantir precisão.
    3. **Ordem dos Cliques:**
        * 1. Esterno (Thorax)
        * 2. Quadril Direito
        * 3. Quadril Esquerdo
        * 4. Joelho (Apoio)
        * 5. Tornozelo (Apoio)
    """)

elif opcao_menu == OPT_METODOLOGIA:
    st.header("📐 Metodologia Biomecânica")
    st.markdown("""
    A base matemática deste software fundamenta-se nos princípios de cinemática vetorial aplicados à análise clínica do movimento.
    Abaixo, detalhamos as fórmulas e as referências científicas que validam cada métrica.
    """)
    
    st.divider()
    
    # 1. Ângulo do Joelho
    st.subheader("1. Ângulo Q Dinâmico (Valgo Angular)")
    cols = st.columns([1, 2])
    with cols[0]:
        st.info("Interpretação: Valores decrescentes (< 180°) indicam aumento do valgo.")
        st.markdown("**Referência Teórica:**")
        st.caption("""
        *"O valgo dinâmico relaciona-se com a adução e rotação interna de quadril e abdução tibial."* \n— **Szklar e Ahmed (1987)**; **Powers (2010)**.
        """)
    with cols[1]:
        st.markdown("""
        Calculado através do **produto escalar** entre dois vetores 3D projetados no plano frontal:
        1. Vetor Coxa ($\overrightarrow{BA}$): Do Joelho ao Quadril.
        2. Vetor Perna ($\overrightarrow{BC}$): Do Joelho ao Tornozelo.
        """)
        st.latex(r"\theta = \arccos\left(\frac{\vec{BA} \cdot \vec{BC}}{|\vec{BA}| |\vec{BC}|}\right)")
        st.markdown("Este cálculo extrai o ângulo interno da articulação, quantificando o colapso medial.")

    st.divider()

    # 2. Desvio Linear
    st.subheader("2. Desvio Medial (Linha de Força)")
    cols = st.columns([1, 2])
    with cols[0]:
        st.info("Interpretação: Mede o deslocamento do centro da patela em relação ao eixo mecânico.")
        st.markdown("**Referência Teórica:**")
        st.caption("""
        *"O deslocamento medial do joelho além da linha do hálux é classificado como posição de alto risco."*
        \n— **Herrington e Munro (2010)**; **Munro et al. (2012)**.
        """)
    with cols[1]:
        st.markdown("""
        Traça-se uma **linha reta imaginária (Vetor Unitário)** conectando o Quadril ao Tornozelo (Eixo Mecânico).
        Calcula-se a distância perpendicular (produto vetorial em 2D) do centro da Patela até esta linha.
        * **Positivo:** Joelho medializado (Valgo).
        * **Zero:** Alinhamento mecânico neutro.
        """)
        st.latex(r"Desvio = \frac{|\vec{QP} \times \vec{QJ}|}{|\vec{QT}|}")
    
    st.divider()

    # 3. Queda Pélvica
    st.subheader("3. Queda Pélvica (Trendelenburg)")
    cols = st.columns([1, 2])
    with cols[0]:
        st.info("Interpretação: Inclinações indicam instabilidade lombo-pélvica.")
        st.markdown("**Referência Teórica:**")
        st.caption("""
        *"A queda pélvica contralateral é um preditor chave de fraqueza do glúteo médio e controle neuromuscular deficiente."*
        \n— **Nakagawa et al. (2018)**; **Petermann et al. (2016)**.
        """)
    with cols[1]:
        st.markdown("""
        Calcula-se o ângulo da linha que conecta as duas Espinhas Ilíacas Antero-Superiores (EIAS) em relação à linha horizontal absoluta (chão).
        """)
        st.latex(r"\alpha = \arctan\left(\frac{y_{dir} - y_{esq}}{x_{dir} - x_{esq}}\right)")

    st.divider()

    # 4. Tronco
    st.subheader("4. Inclinação do Tronco (Compensação)")
    cols = st.columns([1, 2])
    with cols[0]:
        st.info("Interpretação: Desvio lateral do tronco para compensar fraqueza de quadril.")
        st.markdown("**Referência Teórica:**")
        st.caption("""
        *"Compensações do tronco influenciam diretamente o momento de abdução do joelho e aumentam o risco de lesão no LCA."*
        \n— **Hewett et al. (2005)**; **Lewis et al. (2015)**.
        """)
    with cols[1]:
        st.markdown("""
        Define-se o **Centro Pélvico** (ponto médio entre as duas EIAS).
        Calcula-se o ângulo do vetor que liga o Centro Pélvico ao Esterno (Manúbrio) em relação à vertical verdadeira.
        """)
        st.latex(r"\beta_{tronco} = \arctan\left(\frac{\Delta x}{\Delta y}\right)")

elif opcao_menu == OPT_INDIVIDUAL:
    st.header("📂 Análise Individual")
    nome_paciente = st.text_input("Nome do Paciente", "Paciente X")
    video_file = st.file_uploader("Carregar Vídeo", type=['mp4', 'mov'])
    
    if video_file:
        path = salvar_temp(video_file)
        pontos_finais = interface_marcador_pontos(path, "unico")
        
        if pontos_finais:
            if st.button("🚀 Processar"):
                analise = AnalisadorBioStep(path, "Video Unico")
                analise.set_pontos(pontos_finais)
                with st.spinner('Processando...'):
                    df = analise.processar_video()
                os.remove(path)
                st.session_state['resultado_df'] = df
                
            if 'resultado_df' in st.session_state:
                df = st.session_state['resultado_df']
                c1, c2, c3 = st.columns(3)
                c1.metric("Pico Valgo", f"{df['Angulo Joelho'].min():.1f}°")
                c2.metric("Desvio Máx", f"{df['Desvio Valgo (px)'].max():.1f} px")
                c3.metric("Queda Pélvica", f"{abs(df['Queda Pelvica'].max() - 180):.1f}°")

                fig_ang = px.line(df, x="Frame", y="Angulo Joelho", title="Ângulo Joelho")
                fig_desvio = px.line(df, x="Frame", y="Desvio Valgo (px)", title="Desvio Linear")
                fig_pelve = px.line(df, x="Frame", y="Queda Pelvica", title="Pelve")
                
                st.plotly_chart(fig_ang, use_container_width=True)
                col_g1, col_g2 = st.columns(2)
                col_g1.plotly_chart(fig_desvio, use_container_width=True)
                col_g2.plotly_chart(fig_pelve, use_container_width=True)
                
                st.divider()
                st.subheader("💾 Exportar Resultados")
                col_d1, col_d2 = st.columns(2)
                excel_data = df.to_csv(index=False).encode('utf-8')
                col_d1.download_button("📥 Baixar Dados (CSV)", excel_data, f"{nome_paciente}_dados.csv", "text/csv")
                
                if col_d2.button("📄 Gerar Relatório PDF"):
                    with st.spinner("Gerando PDF..."):
                        pdf_bytes = gerar_pdf(nome_paciente, df, fig_ang, fig_desvio, fig_pelve)
                        st.download_button("📥 Clique para Baixar PDF", pdf_bytes, f"{nome_paciente}_relatorio.pdf", "application/pdf")


elif opcao_menu == OPT_COMPARACAO:
    st.header("🔄 Comparativo")
    nome_paciente = st.text_input("Nome do Paciente", "Paciente X")
    c1, c2 = st.columns(2)
    v1 = c1.file_uploader("Vídeo ANTES", type=['mp4'])
    v2 = c2.file_uploader("Vídeo DEPOIS", type=['mp4'])

    if v1 and v2:
        path1, path2 = salvar_temp(v1), salvar_temp(v2)
        
        col_esq, col_dir = st.columns(2) 
        
        with col_esq: 
            st.subheader("Antes")
            pts1 = interface_marcador_pontos(path1, "v1")
        with col_dir: 
            st.subheader("Depois")
            pts2 = interface_marcador_pontos(path2, "v2")

        if pts1 and pts2:
            if st.button("🚀 Comparar"):
                a1 = AnalisadorBioStep(path1); a1.set_pontos(pts1)
                df1 = a1.processar_video()
                a2 = AnalisadorBioStep(path2); a2.set_pontos(pts2)
                df2 = a2.processar_video()
                os.remove(path1); os.remove(path2)
                
                df1['Periodo'] = 'Antes'; df2['Periodo'] = 'Depois'
                df_final = pd.concat([df1, df2])
                st.session_state['comp_df'] = df_final
            
            if 'comp_df' in st.session_state:
                df_final = st.session_state['comp_df']
                fig_comp = px.line(df_final, x="Frame", y="Angulo Joelho", color="Periodo", title="Comparativo: Ângulo Q Dinâmico", color_discrete_map={"Antes":"red", "Depois":"green"})
                st.plotly_chart(fig_comp, use_container_width=True)
                
                st.divider()
                st.subheader("💾 Exportar Resultados")
                cd1, cd2 = st.columns(2)
                csv_data = df_final.to_csv(index=False).encode('utf-8')
                cd1.download_button("📥 Baixar Dados (CSV)", csv_data, f"{nome_paciente}_comparacao.csv", "text/csv")
                if cd2.button("📄 Relatório PDF"):
                    pdf_bytes = gerar_pdf(nome_paciente, df_final, fig_comp, None, None, "Comparativa")
                    st.download_button("📥 Baixar PDF", pdf_bytes, f"{nome_paciente}_relatorio_comp.pdf", "application/pdf")