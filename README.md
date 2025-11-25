# 🦵 BioStep Analyzer

**Sistema de Análise Biomecânica do Valgismo Dinâmico via Visão Computacional**

![Python](https://img.shields.io/badge/Python-3.8%2B-blue?style=for-the-badge\&logo=python)
![Streamlit](https://img.shields.io/badge/Streamlit-FF4B4B?style=for-the-badge\&logo=streamlit)
![OpenCV](https://img.shields.io/badge/OpenCV-5C3EE8?style=for-the-badge\&logo=opencv)
![Status](https://img.shields.io/badge/Status-Finalizado-green?style=for-the-badge)

## 📖 Sobre o Projeto

O **BioStep Analyzer** é uma ferramenta desenvolvida para auxiliar fisioterapeutas e profissionais de educação física na análise quantitativa do movimento humano durante o teste **Step Down**. Ele utiliza algoritmos de **Visão Computacional (Fluxo Óptico)** e uma interface web interativa para transformar a avaliação visual tradicional em dados objetivos, permitindo acompanhar a evolução clínica de forma precisa.

### 🎯 Objetivo

Quantificar o **Valgismo Dinâmico** e outras compensações biomecânicas, oferecendo métricas e relatórios visuais que apoiam diagnósticos e decisões terapêuticas.

---

## ✨ Funcionalidades Principais

* **Rastreamento Híbrido:** Pontos anatômicos selecionados manualmente e ajustados automaticamente por um "imã de cor" baseado nos marcadores adesivos do vídeo.
* **Análise Individual:** Métricas de pico como ângulo mínimo, desvio medial máximo e queda pélvica.
* **Modo Comparação (Antes/Depois):** Análise simultânea de dois vídeos com gráficos sobrepostos.
* **Dashboard Interativo:** Gráficos dinâmicos e indicadores clínicos atualizados em tempo real.
* **Relatórios Automáticos:** Geração de PDF clínico e exportação de dados brutos em CSV.

---

## 📊 Métricas Biomecânicas

O sistema calcula automaticamente quatro indicadores amplamente utilizados na literatura científica:

1. **Ângulo Q Dinâmico:** Relação angular entre coxa e perna.
2. **Desvio Medial Linear:** Distância da patela em relação ao eixo mecânico.
3. **Queda Pélvica:** Inclinação entre as EIAS.
4. **Inclinação do Tronco:** Desvio lateral do esterno.

---

## 🚀 Instalação e Uso

### Pré-requisitos

* Python 3.8+
* Vídeos com marcadores adesivos visíveis (preferencialmente amarelos)

### 1. Clonar o Repositório

```bash
git clone https://github.com/SEU_USUARIO/BioStep-Analyzer.git
cd BioStep-Analyzer
```

### 2. Criar Ambiente Virtual

```bash
# Windows
python -m venv venv
./venv/Scripts/activate

# Linux/macOS
python3 -m venv venv
source venv/bin/activate
```

### 3. Instalar Dependências

```bash
pip install streamlit opencv-python numpy pandas plotly fpdf streamlit-image-coordinates kaleido openpyxl
```

### 4. Executar a Aplicação

```bash
python -m streamlit run dashboard.py
```

---

## 🖥️ Guia de Uso

1. **Upload:** Envie o vídeo do teste (em .mp4, vista frontal).

2. **Marcação de Pontos:** Clique nos 5 pontos anatômicos:

   * Esterno
   * Quadril Direito (EIAS)
   * Quadril Esquerdo (EIAS)
   * Joelho (perna de apoio)
   * Tornozelo (perna de apoio)

   O sistema ajusta automaticamente o ponto para o centro do marcador.

3. **Processamento:** O fluxo óptico rastreia os pontos ao longo do vídeo.

4. **Resultados:** Visualize gráficos, métricas e gere o PDF ou CSV.

---

## 🛠️ Tecnologias Utilizadas

* **Python 3.11**
* **Streamlit**
* **OpenCV (Optical Flow PyrLK)**
* **NumPy**
* **Pandas**
* **Plotly**
* **FPDF**
* **Streamlit-Image-Coordinates**

---

## 📚 Referências

* Hewett et al. (2005)
* Powers (2010)
* Herrington & Munro (2010)
* Nakagawa et al. (2018)

---

## 👨‍💻 Autora

**Maria Eduarda Soares Romana Silva**

Projeto desenvolvido para a disciplina de **Processamento Digital de Imagens**.

*Aviso: Este software é um protótipo acadêmico e não substitui avaliação clínica profissional.*
