import cv2
import numpy as np
import math
import pandas as pd

# Calcula o angulo interno entre tres pontos - lei dos cossenos
def calcular_angulo(a, b, c):
    a = np.array(a)    # ponto A -  quadril
    b = np.array(b)    # ponto B -  joelho
    c = np.array(c)    # ponto C -  tornozelo

    # vetores
    ba = a - b  # vetor do joelho para o quadril
    bc = c - b  # vetor do joelho para o tornozelo

    # normas dos vetores
    norma_ba = np.linalg.norm(ba)
    norma_bc = np.linalg.norm(bc)

    if norma_ba == 0 or norma_bc == 0: return 0  # evita divisao por zero

    #  produto escalar 
    cosine_angle = np.dot(ba, bc) / (norma_ba * norma_bc)

    return np.degrees(np.arccos(np.clip(cosine_angle, -1.0, 1.0)))   #  converte para graus

# calcula o desvio linear (distancia ponto-reta) para valgo/varo
def calcular_desvio_linear(quadril, joelho, tornozelo):
    p1, p2, p3 = np.array(quadril), np.array(tornozelo), np.array(joelho)

    # vetores
    vec_linha = p2 - p1  # vetor da linha quadril-tornozelo
    vec_ponto = p3 - p1  # vetor do quadril ao joelho
  
    # produto vetorial (cross product) em 2D retorna um escalar
    cross_prod = vec_linha[0]*vec_ponto[1] - vec_linha[1]*vec_ponto[0]

    #  norma do vetor linha
    norma = np.linalg.norm(vec_linha)

    #  retorna a distancia - se positiva, valgo; se negativa, varo
    return cross_prod / norma if norma != 0 else 0

# calcula inclinacao entre dois pontos  -  queda pelvica
def calcular_inclinacao(p1, p2):

    #  calcula   o arcotangente da diferenca y/x, retornado em  angulo polar  
    return math.degrees(math.atan2(p2[1] - p1[1], p2[0] - p1[0]))

# calcula inclinacao do tronco    -   compara esterno com meio dos quadris
def calcular_tronco(esterno, q_dir, q_esq):

    #  ponto medio entre os quadris
    mid_x = (q_dir[0] + q_esq[0]) / 2   
    mid_y = (q_dir[1] + q_esq[1]) / 2

    #   calcula  a  diferença (delta) entre esterno e ponto médio
    dx = esterno[0] - mid_x
    dy = mid_y - esterno[1]

    #  retorna o angulo de inclinacao do tronco
    return math.degrees(math.atan2(dx, dy)) if dy != 0 else 0

# Funçao para refinar o ponto clicado baseado na cor do marcador  ("imã")
def refinar_ponto_pela_cor(frame, x, y, janela=20):

    h, w = frame.shape[:2]
    
    # define os limites da janela ao redor do clique
    # max  e min para evitar sair dos limites da imagem
    x1 = max(0, x - janela); x2 = min(w, x + janela)
    y1 = max(0, y - janela); y2 = min(h, y + janela)
    
    # recorta a pequena área ao redor do clique
    roi = frame[y1:y2, x1:x2]
    
    # converte  BGR (OpenCV) para HSV
    hsv_roi = cv2.cvtColor(roi, cv2.COLOR_BGR2HSV)
    
    # definição  da   cor  dos marcadores  amarelos  em HSV
    lower = np.array([15, 70, 70]) 
    upper = np.array([35, 255, 255])

    # cria uma máscara para a cor amarela  - o que é amarelo fica branco (255)  e o resto preto (0)
    mask = cv2.inRange(hsv_roi, lower, upper)
    
    # calcula os momentos da máscara para encontrar o centro de massa
    M = cv2.moments(mask)

    #  se encontrou pixels amarelos na máscara
    if M["m00"] > 0:
        # novo centro local
        cx_local = int(M["m10"] / M["m00"])
        cy_local = int(M["m01"] / M["m00"])
        
        # converte a coordenada local para global
        novo_x = x1 + cx_local
        novo_y = y1 + cy_local
        return int(novo_x), int(novo_y)
    
    # se não achou amarelo (ex: clicou no esterno sem marcador), mantém o original
    return x, y


class AnalisadorBioStep:
    def __init__(self, video_path, titulo="Analise"):
        #carrega o vídeo
        self.cap = cv2.VideoCapture(video_path)
        self.titulo = titulo
        self.dados = [] # lista para armazenar os dados calculados
        
        # lê o primeiro frame
        success, frame = self.cap.read()
        if not success: raise ValueError("Erro ao ler video")
        
        # tamanho fixo para o vídeo processado
        self.LARGURA = 480
        self.ALTURA = 850
        
        
        self.frame_inicial = cv2.resize(frame, (self.LARGURA, self.ALTURA))
        #converte para escala  de cinza para o rastreamento óptico
        self.old_gray = cv2.cvtColor(self.frame_inicial, cv2.COLOR_BGR2GRAY)
        # parâmetros do Lucas-Kanade
        # winSize: tamanho da janela de busca
        # maxLevel: níveis de pirâmide (para movimentos rápidos)
        self.lk_params = dict(winSize=(25, 25), maxLevel=3, criteria=(cv2.TERM_CRITERIA_EPS | cv2.TERM_CRITERIA_COUNT, 10, 0.03))

    def get_frame_inicial_rgb(self):
        #converte BGR para RGB para exibição no frontend
        return cv2.cvtColor(self.frame_inicial, cv2.COLOR_BGR2RGB)

    def set_pontos(self, lista_pontos):
        #recebe  lista de  pontos  clicados pelo usuário    no  frontend
        self.p0 = np.array(lista_pontos, dtype=np.float32).reshape(-1, 1, 2)

    def processar_video(self):
        #  processa o vídeo frame a frame
        frame_count = 0
        
        while True:
            #  lê o próximo frame
            ret, frame = self.cap.read()
            if not ret: break  # fim do vídeo
            frame_count += 1
            
            # redimensiona e converte para escala de cinza
            frame = cv2.resize(frame, (self.LARGURA, self.ALTURA))
            frame_gray = cv2.cvtColor(frame, cv2.COLOR_BGR2GRAY)
            
            # cv2.calcOpticalFlowPyrLK compara a imagem anterior (old_gray) com a atual (frame_gray).
            # ele pega os pontos antigos (self.p0) e descobre onde eles foram parar (p1).
            p1, st, err = cv2.calcOpticalFlowPyrLK(self.old_gray, frame_gray, self.p0, None, **self.lk_params)
            
            if p1 is None: break # se não conseguiu rastrear, sai do loop
            
            pts = p1.reshape(-1, 2)  #   organiza os pontos rastreados

            # define quadril de apoio (o mais próximo do joelho  analisado)
            dist_d = np.linalg.norm(pts[1] - pts[3])
            dist_e = np.linalg.norm(pts[2] - pts[3])
            q_apoio = pts[1] if dist_d < dist_e else pts[2]

            # calculos biomecânicos
            ang = calcular_angulo(q_apoio, pts[3], pts[4])
            desvio = calcular_desvio_linear(q_apoio, pts[3], pts[4])
            pelve = calcular_inclinacao(pts[1], pts[2])
            tronco = calcular_tronco(pts[0], pts[1], pts[2])

            # armazena os dados calculados
            self.dados.append({
                'Frame': frame_count,
                'Angulo Joelho': ang,
                'Desvio Valgo (px)': desvio,
                'Queda Pelvica': pelve,
                'Inclinacao Tronco': tronco
            })

            self.old_gray = frame_gray.copy()   # atualiza o frame anterior
            self.p0 = p1.reshape(-1, 1, 2)

        self.cap.release()  # libera o vídeo
        return pd.DataFrame(self.dados) # retorna os dados como DataFrame pandas