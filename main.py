# main.py - Jogo de xadrez completo com todas as melhorias

import pygame
import chess
import chess.engine
import chess.pgn
import os
import sys
import time
from datetime import datetime
import tkinter as tk
from tkinter import filedialog, messagebox
import io

# Inicializar Pygame
pygame.init()

# Configurações da tela
TILE_SIZE = 80
BOARD_WIDTH = TILE_SIZE * 8
BOARD_HEIGHT = TILE_SIZE * 8
UI_HEIGHT = 250
WIDTH = BOARD_WIDTH + 250  # +250 para o painel lateral
HEIGHT = max(BOARD_HEIGHT, 600) + UI_HEIGHT
screen = pygame.display.set_mode((WIDTH, HEIGHT))
pygame.display.set_caption("Jogo de Xadrez Profissional")

# Cores
LIGHT_SQUARE = (240, 217, 181)
DARK_SQUARE = (181, 136, 99)
SELECTED_COLOR = (100, 100, 255, 150)  # Azul claro transparente
HIGHLIGHT_COLOR = (124, 252, 0, 180)   # Verde claro transparente para movimentos válidos
LAST_MOVE_COLOR = (155, 199, 0, 150)   # Amarelo-esverdeado para último movimento
CHECK_COLOR = (255, 0, 0, 150)         # Vermelho para xeque
TEXT_COLOR = (255, 255, 255)
TEXT_COLOR_HIGHLIGHT = (255, 215, 0)  # Dourado
BACKGROUND_COLOR = (30, 30, 40)
MENU_BACKGROUND = (45, 45, 55)
BUTTON_COLOR = (70, 130, 180)
BUTTON_HOVER_COLOR = (100, 170, 220)
BUTTON_TEXT_COLOR = (255, 255, 255)
HISTORY_BG = (50, 50, 60, 200)
PANEL_BG = (40, 40, 50)
EVAL_BAR_BG = (60, 60, 70)
EVAL_BAR_WHITE = (240, 240, 240)
EVAL_BAR_BLACK = (30, 30, 30)

# Fontes
font_title = pygame.font.SysFont("Arial", 36, bold=True)
font_large = pygame.font.SysFont("Arial", 28)
font_medium = pygame.font.SysFont("Arial", 24)
font_small = pygame.font.SysFont("Arial", 20)
font_tiny = pygame.font.SysFont("Arial", 16)

# --- Carregamento de Imagens das Peças ---
SCRIPT_DIR = os.path.dirname(os.path.abspath(__file__))
ASSETS_DIR = os.path.join(SCRIPT_DIR, "assets", "pieces")

# Carregar imagens das peças
PIECE_IMAGES = {}
pieces_list = ['w_pawn', 'w_rook', 'w_knight', 'w_bishop', 'w_queen', 'w_king',
               'b_pawn', 'b_rook', 'b_knight', 'b_bishop', 'b_queen', 'b_king']

for piece in pieces_list:
    image_path = os.path.join(ASSETS_DIR, f'{piece}.png')
    try:
        # Carregar imagem com anti-aliasing
        image = pygame.image.load(image_path).convert_alpha()
        PIECE_IMAGES[piece] = image
    except Exception as e:
        print(f"Erro ao carregar {piece}: {e}")

# --- Configuração do Stockfish ---
ENGINE_PATH = os.path.join(SCRIPT_DIR, "engines", "stockfish.exe")

# Verificar se o executável do Stockfish existe
if not os.path.exists(ENGINE_PATH):
    print(f"ERRO: Executável do Stockfish não encontrado em {ENGINE_PATH}")
    print("Por favor, baixe o Stockfish e coloque o executável na pasta 'engines'.")
    pygame.quit()
    sys.exit()

try:
    engine = chess.engine.SimpleEngine.popen_uci(ENGINE_PATH)
    print("✓ Stockfish carregado com sucesso!")
except Exception as e:
    print(f"ERRO ao iniciar o Stockfish: {e}")
    pygame.quit()
    sys.exit()

class Button:
    def __init__(self, x, y, width, height, text, action=None, font=font_small):
        self.rect = pygame.Rect(x, y, width, height)
        self.text = text
        self.action = action
        self.hovered = False
        self.font = font
        
    def draw(self, screen):
        color = BUTTON_HOVER_COLOR if self.hovered else BUTTON_COLOR
        pygame.draw.rect(screen, color, self.rect, border_radius=6)
        pygame.draw.rect(screen, (200, 200, 200), self.rect, 1, border_radius=6)
        
        text_surf = self.font.render(self.text, True, BUTTON_TEXT_COLOR)
        text_rect = text_surf.get_rect(center=self.rect.center)
        screen.blit(text_surf, text_rect)
        
    def check_hover(self, pos):
        self.hovered = self.rect.collidepoint(pos)
        return self.hovered
        
    def handle_event(self, event):
        if event.type == pygame.MOUSEBUTTONDOWN and event.button == 1:
            if self.hovered and self.action:
                return self.action
        return None

class PromotionDialog:
    def __init__(self, color):
        self.color = color
        self.selected_piece = None
        self.running = True
        
        # Definir peças para promoção
        self.pieces = ['queen', 'rook', 'bishop', 'knight']
        
        # Criar botões para cada peça
        self.buttons = []
        for i, piece in enumerate(self.pieces):
            x = WIDTH // 2 - 150 + i * 100
            y = HEIGHT // 2 - 50
            button = Button(x, y, 80, 80, "", {"action": "promote", "piece": piece})
            self.buttons.append(button)
    
    def draw(self, screen):
        # Fundo semi-transparente
        s = pygame.Surface((WIDTH, HEIGHT), pygame.SRCALPHA)
        s.fill((0, 0, 0, 200))
        screen.blit(s, (0, 0))
        
        # Título
        title = font_medium.render("Escolha uma peça para promoção:", True, TEXT_COLOR)
        screen.blit(title, (WIDTH//2 - title.get_width()//2, HEIGHT//2 - 100))
        
        # Desenhar peças para escolha
        for i, (piece, button) in enumerate(zip(self.pieces, self.buttons)):
            button.draw(screen)
            
            # Desenhar a peça no botão
            piece_name = f"{'w' if self.color == chess.WHITE else 'b'}_{piece}"
            if piece_name in PIECE_IMAGES:
                piece_img = PIECE_IMAGES[piece_name]
                scaled_img = pygame.transform.smoothscale(piece_img, (60, 60))
                img_rect = scaled_img.get_rect(center=button.rect.center)
                screen.blit(scaled_img, img_rect)
    
    def handle_event(self, event, mouse_pos):
        if event.type == pygame.MOUSEBUTTONDOWN and event.button == 1:
            for button in self.buttons:
                if button.rect.collidepoint(mouse_pos):
                    result = button.handle_event(event)
                    if result and result["action"] == "promote":
                        self.selected_piece = result["piece"]
                        self.running = False
                        return result
        return None

class Menu:
    def __init__(self):
        self.state = "main"  # "main", "difficulty", "color", "load"
        
        # Botões principais
        self.main_buttons = [
            Button(WIDTH//2 - 100, 150, 200, 50, "Novo Jogo", {"action": "new_game"}),
            Button(WIDTH//2 - 100, 220, 200, 50, "Carregar Partida", {"action": "load_game"}),
            Button(WIDTH//2 - 100, 290, 200, 50, "Sair", {"action": "quit"})
        ]
        
        # Botões de dificuldade
        self.difficulty_buttons = [
            Button(WIDTH//2 - 100, 120, 200, 40, "Muito Fácil (Nível 0)", {"action": "set_difficulty", "level": 0}),
            Button(WIDTH//2 - 100, 170, 200, 40, "Fácil (Nível 5)", {"action": "set_difficulty", "level": 5}),
            Button(WIDTH//2 - 100, 220, 200, 40, "Médio (Nível 10)", {"action": "set_difficulty", "level": 10}),
            Button(WIDTH//2 - 100, 270, 200, 40, "Difícil (Nível 15)", {"action": "set_difficulty", "level": 15}),
            Button(WIDTH//2 - 100, 320, 200, 40, "Muito Difícil (Nível 20)", {"action": "set_difficulty", "level": 20}),
            Button(WIDTH//2 - 100, 390, 200, 40, "Voltar", {"action": "back_to_main"})
        ]
        self.selected_difficulty = 2  # Nível 10 por padrão
        
        # Botões de cor
        self.color_buttons = [
            Button(WIDTH//2 - 150, 200, 130, 50, "Brancas", {"action": "set_color", "color": "white"}),
            Button(WIDTH//2 + 20, 200, 130, 50, "Pretas", {"action": "set_color", "color": "black"}),
            Button(WIDTH//2 - 100, 300, 200, 40, "Voltar", {"action": "back_to_difficulty"})
        ]
        
        self.difficulty_level = 10
        
    def draw(self, screen, mouse_pos):
        screen.fill(BACKGROUND_COLOR)
        
        # Título
        title = font_title.render("JOGO DE XADREZ PROFISSIONAL", True, TEXT_COLOR_HIGHLIGHT)
        screen.blit(title, (WIDTH//2 - title.get_width()//2, 50))
        
        if self.state == "main":
            # Desenhar botões principais
            for button in self.main_buttons:
                button.check_hover(mouse_pos)
                button.draw(screen)
                
        elif self.state == "difficulty":
            subtitle = font_large.render("Escolha a Dificuldade", True, TEXT_COLOR)
            screen.blit(subtitle, (WIDTH//2 - subtitle.get_width()//2, 90))
            
            # Destacar botão selecionado
            self.difficulty_buttons[self.selected_difficulty].hovered = True
            
            for button in self.difficulty_buttons:
                button.check_hover(mouse_pos)
                button.draw(screen)
                
        elif self.state == "color":
            subtitle = font_large.render("Escolha sua Cor", True, TEXT_COLOR)
            screen.blit(subtitle, (WIDTH//2 - subtitle.get_width()//2, 150))
            
            for button in self.color_buttons:
                button.check_hover(mouse_pos)
                button.draw(screen)
    
    def handle_event(self, event, mouse_pos):
        if event.type == pygame.MOUSEBUTTONDOWN and event.button == 1:
            if self.state == "main":
                for button in self.main_buttons:
                    result = button.handle_event(event)
                    if result:
                        if result["action"] == "new_game":
                            self.state = "difficulty"
                            return None
                        elif result["action"] == "load_game":
                            self.state = "load"
                            return {"action": "load_game"}
                        elif result["action"] == "quit":
                            return {"action": "quit"}
                            
            elif self.state == "difficulty":
                for i, button in enumerate(self.difficulty_buttons):
                    result = button.handle_event(event)
                    if result:
                        if result["action"] == "set_difficulty":
                            self.difficulty_level = result["level"]
                            self.selected_difficulty = i
                            self.state = "color"
                            return None
                        elif result["action"] == "back_to_main":
                            self.state = "main"
                            return None
                            
            elif self.state == "color":
                for button in self.color_buttons:
                    result = button.handle_event(event)
                    if result:
                        if result["action"] == "set_color":
                            return {
                                "action": "start_game",
                                "player_color": chess.WHITE if result["color"] == "white" else chess.BLACK,
                                "difficulty": self.difficulty_level
                            }
                        elif result["action"] == "back_to_difficulty":
                            self.state = "difficulty"
                            return None
        return None

class Game:
    def __init__(self, player_color, difficulty_level):
        self.board = chess.Board()
        self.player_color = player_color  # chess.WHITE ou chess.BLACK
        self.selected_square = None
        self.game_over = False
        self.message = ""
        self.last_move_time = 0
        self.move_delay = 1.0  # 1 segundo de delay entre jogadas
        self.valid_moves = []  # Movimentos válidos da peça selecionada
        self.show_valid_moves = True  # Mostrar movimentos válidos
        self.difficulty_level = difficulty_level  # Armazenar o nível de dificuldade
        self.last_move = None  # Último movimento realizado
        self.move_history = []  # Histórico de movimentos
        self.promotion_dialog = None  # Diálogo de promoção
        self.pawn_promotion_move = None  # Movimento de promoção pendente
        self.analysis_mode = False  # Modo de análise após o fim do jogo
        self.eval_score = 0.0  # Avaliação da posição
        self.thinking = False  # Se o engine está pensando
        self.suggested_move = None  # Movimento sugerido
        
        # Configurar dificuldade do Stockfish
        try:
            engine.configure({"Skill Level": difficulty_level})
            print(f"✓ Nível de dificuldade configurado para {difficulty_level}.")
        except Exception as e:
            print(f"Erro ao configurar dificuldade: {e}")

    def draw_board(self, screen):
        # Desenhar tabuleiro (8x8)
        for row in range(8):
            for col in range(8):
                square = chess.square(col, 7 - row)
                color = LIGHT_SQUARE if (row + col) % 2 == 0 else DARK_SQUARE
                rect = pygame.Rect(col * TILE_SIZE, row * TILE_SIZE, TILE_SIZE, TILE_SIZE)
                pygame.draw.rect(screen, color, rect)

                # Destacar último movimento
                if self.last_move and (square == self.last_move.from_square or square == self.last_move.to_square):
                    s = pygame.Surface((TILE_SIZE, TILE_SIZE), pygame.SRCALPHA)
                    s.fill(LAST_MOVE_COLOR)
                    screen.blit(s, rect)

                # Destacar casa selecionada
                if self.selected_square is not None and square == self.selected_square:
                    s = pygame.Surface((TILE_SIZE, TILE_SIZE), pygame.SRCALPHA)
                    s.fill(SELECTED_COLOR)
                    screen.blit(s, rect)
                
                # Destacar rei em xeque
                king_square = self.board.king(self.board.turn)
                if king_square is not None and self.board.is_check():
                    if square == king_square:
                        s = pygame.Surface((TILE_SIZE, TILE_SIZE), pygame.SRCALPHA)
                        s.fill(CHECK_COLOR)
                        screen.blit(s, rect)
                
                # Desenhar círculos para movimentos válidos (menor)
                if self.show_valid_moves and square in self.valid_moves:
                    # Desenhar círculo pequeno no centro da casa
                    center_x = col * TILE_SIZE + TILE_SIZE // 2
                    center_y = row * TILE_SIZE + TILE_SIZE // 2
                    radius = 6  # Reduzido de 8 para 6
                    
                    # Sombra
                    pygame.draw.circle(screen, (0, 0, 0, 100), (center_x + 1, center_y + 1), radius)
                    # Círculo principal
                    pygame.draw.circle(screen, HIGHLIGHT_COLOR, (center_x, center_y), radius)
                    pygame.draw.circle(screen, (255, 255, 255), (center_x, center_y), radius, 1)

                # Desenhar peça
                piece = self.board.piece_at(square)
                if piece:
                    piece_name = f"{'w' if piece.color == chess.WHITE else 'b'}_{chess.piece_name(piece.piece_type)}"
                    if piece_name in PIECE_IMAGES:
                        image = PIECE_IMAGES[piece_name]
                        # Redimensionar imagem com anti-aliasing
                        scaled_image = pygame.transform.smoothscale(image, (TILE_SIZE, TILE_SIZE))
                        screen.blit(scaled_image, rect.topleft)

    def draw_ui(self, screen):
        # Área da UI abaixo do tabuleiro
        ui_rect = pygame.Rect(0, TILE_SIZE * 8, WIDTH, UI_HEIGHT)
        pygame.draw.rect(screen, MENU_BACKGROUND, ui_rect)
        pygame.draw.line(screen, (100, 100, 100), (0, TILE_SIZE * 8), (WIDTH, TILE_SIZE * 8), 2)
        
        # Mensagem do jogo
        if self.message:
            message_text = font_medium.render(self.message, True, TEXT_COLOR_HIGHLIGHT)
            screen.blit(message_text, (20, TILE_SIZE * 8 + 10))
        else:
            # Mostrar de quem é o turno
            turn_text = "Vez das Brancas" if self.board.turn == chess.WHITE else "Vez das Pretas"
            color = (255, 255, 255) if self.board.turn != self.player_color else TEXT_COLOR_HIGHLIGHT
            text = font_medium.render(turn_text, True, color)
            screen.blit(text, (20, TILE_SIZE * 8 + 10))
            
            # Indicar se é o turno do jogador
            if self.board.turn == self.player_color and not self.game_over and not self.analysis_mode:
                player_text = font_small.render("(Seu turno)", True, (100, 255, 100))
                screen.blit(player_text, (20, TILE_SIZE * 8 + 45))

        # Informações do jogo
        info_y = TILE_SIZE * 8 + 80
        if not self.game_over or self.analysis_mode:
            # Mostrar dificuldade correta
            diff_text = font_small.render(f"Dificuldade: {self.get_difficulty_name()}", True, TEXT_COLOR)
            screen.blit(diff_text, (20, info_y))
            
            # Mostrar cor do jogador
            color_text = font_small.render(f"Você joga com: {'Brancas' if self.player_color == chess.WHITE else 'Pretas'}", True, TEXT_COLOR)
            screen.blit(color_text, (20, info_y + 30))
        
        # Histórico de movimentos
        self.draw_move_history(screen)

    def draw_sidebar(self, screen):
        # Painel lateral
        panel_rect = pygame.Rect(BOARD_WIDTH, 0, 250, HEIGHT)
        pygame.draw.rect(screen, PANEL_BG, panel_rect)
        pygame.draw.line(screen, (100, 100, 100), (BOARD_WIDTH, 0), (BOARD_WIDTH, HEIGHT), 2)
        
        # Título do painel
        title = font_medium.render("Informações", True, TEXT_COLOR_HIGHLIGHT)
        screen.blit(title, (BOARD_WIDTH + 10, 20))
        
        # Barra de avaliação
        self.draw_evaluation_bar(screen)
        
        # Botões do painel
        button_y = 150
        buttons = [
            Button(BOARD_WIDTH + 25, button_y, 200, 40, "Salvar Partida", {"action": "save_game"}, font_tiny),
            Button(BOARD_WIDTH + 25, button_y + 50, 200, 40, "Sugerir Movimento", {"action": "suggest_move"}, font_tiny),
            Button(BOARD_WIDTH + 25, button_y + 100, 200, 40, "Modo Análise", {"action": "toggle_analysis"}, font_tiny),
            Button(BOARD_WIDTH + 25, button_y + 150, 200, 40, "Reiniciar", {"action": "restart"}, font_tiny),
            Button(BOARD_WIDTH + 25, button_y + 200, 200, 40, "Menu Principal", {"action": "main_menu"}, font_tiny)
        ]
        
        mouse_pos = pygame.mouse.get_pos()
        for button in buttons:
            button.check_hover(mouse_pos)
            button.draw(screen)
            
        return buttons

    def draw_evaluation_bar(self, screen):
        # Barra de avaliação
        bar_width = 200
        bar_height = 20
        bar_x = BOARD_WIDTH + 25
        bar_y = 70
        
        # Fundo da barra
        pygame.draw.rect(screen, EVAL_BAR_BG, (bar_x, bar_y, bar_width, bar_height))
        
        # Valor da avaliação (simplificado)
        eval_text = font_tiny.render(f"Avaliação: {self.eval_score:.1f}", True, TEXT_COLOR)
        screen.blit(eval_text, (bar_x, bar_y - 25))
        
        # Preenchimento da barra
        white_width = int(bar_width * min(1.0, max(0.0, (self.eval_score + 5) / 10)))
        pygame.draw.rect(screen, EVAL_BAR_WHITE, (bar_x, bar_y, white_width, bar_height))
        pygame.draw.rect(screen, EVAL_BAR_BLACK, (bar_x + white_width, bar_y, bar_width - white_width, bar_height))
        
        # Linha do centro
        pygame.draw.line(screen, (100, 100, 100), (bar_x + bar_width//2, bar_y), (bar_x + bar_width//2, bar_y + bar_height), 1)

    def draw_move_history(self, screen):
        # Fundo do histórico
        history_rect = pygame.Rect(20, TILE_SIZE * 8 + 130, WIDTH - 40, UI_HEIGHT - 140)
        pygame.draw.rect(screen, HISTORY_BG, history_rect, border_radius=5)
        pygame.draw.rect(screen, (100, 100, 100), history_rect, 1, border_radius=5)
        
        # Título do histórico
        title = font_small.render("Histórico de Movimentos:", True, TEXT_COLOR)
        screen.blit(title, (30, TILE_SIZE * 8 + 135))
        
        # Mostrar movimentos
        y_offset = TILE_SIZE * 8 + 165
        for i, move_text in enumerate(self.move_history[-8:]):  # Mostrar últimos 8 movimentos
            text = font_tiny.render(move_text, True, TEXT_COLOR)
            screen.blit(text, (30, y_offset + i * 20))

    def get_difficulty_name(self):
        # Usar o nível de dificuldade armazenado
        level = self.difficulty_level
        if level <= 2:
            return "Muito Fácil"
        elif level <= 7:
            return "Fácil"
        elif level <= 12:
            return "Médio"
        elif level <= 17:
            return "Difícil"
        else:
            return "Muito Difícil"

    def handle_click(self, pos):
        if self.board.turn != self.player_color and not self.analysis_mode and not self.game_over:
            return
            
        col = pos[0] // TILE_SIZE
        row = pos[1] // TILE_SIZE
        
        # Verificar se o clique foi no tabuleiro
        if 0 <= col < 8 and 0 <= row < 8:
            square = chess.square(col, 7 - row)

            if self.selected_square is None:
                # Selecionar peça
                piece = self.board.piece_at(square)
                if piece and (piece.color == self.player_color or self.analysis_mode):
                    self.selected_square = square
                    # Calcular movimentos válidos
                    self.valid_moves = [move.to_square for move in self.board.legal_moves 
                                      if move.from_square == square]
            else:
                # Tentar mover
                if square == self.selected_square:
                    # Clicou na mesma peça, deselecionar
                    self.selected_square = None
                    self.valid_moves = []
                else:
                    move = chess.Move(self.selected_square, square)
                    if move in self.board.legal_moves:
                        # Verificar se é movimento de promoção
                        if self.board.piece_at(self.selected_square).piece_type == chess.PAWN:
                            if (self.board.turn == chess.WHITE and chess.square_rank(square) == 7) or \
                               (self.board.turn == chess.BLACK and chess.square_rank(square) == 0):
                                # Movimento de promoção
                                self.pawn_promotion_move = move
                                self.promotion_dialog = PromotionDialog(self.board.turn)
                                return
                        
                        # Movimento normal
                        self.execute_move(move)
                    else:
                        # Movimento ilegal, deselecionar
                        self.selected_square = None
                        self.valid_moves = []

    def execute_move(self, move):
        """Executa um movimento e atualiza o histórico"""
        # Converter movimento para notação algébrica
        move_san = self.board.san(move)
        
        # Executar movimento
        self.board.push(move)
        self.last_move = move
        
        # Adicionar ao histórico
        move_number = len(self.move_history) // 2 + 1
        if len(self.move_history) % 2 == 0:
            self.move_history.append(f"{move_number}. {move_san}")
        else:
            self.move_history[-1] += f" {move_san}"
        
        # Limpar seleção
        self.selected_square = None
        self.valid_moves = []
        self.last_move_time = time.time()
        
        # Verificar fim de jogo
        if self.board.is_game_over():
            self.game_over = True
            self.set_game_result()

    def handle_promotion(self, piece_type):
        """Trata a promoção de peão"""
        if self.pawn_promotion_move:
            # Criar movimento de promoção
            promotion_move = chess.Move(
                self.pawn_promotion_move.from_square,
                self.pawn_promotion_move.to_square,
                promotion=getattr(chess, piece_type.upper())
            )
            
            # Executar movimento
            self.execute_move(promotion_move)
            self.pawn_promotion_move = None
            self.promotion_dialog = None

    def make_bot_move(self):
        if ((self.board.turn != self.player_color and not self.game_over) or self.analysis_mode) and \
           not self.promotion_dialog and \
           time.time() - self.last_move_time >= self.move_delay and \
           not self.thinking:
            
            print("Stockfish está pensando...")
            self.thinking = True
            try:
                # Obter avaliação da posição
                info = engine.analyse(self.board, chess.engine.Limit(time=0.1))
                if "score" in info:
                    score = info["score"].white().score(mate_score=10000)
                    self.eval_score = score / 100.0 if score is not None else 0.0
                
                # Jogar movimento
                result = engine.play(self.board, chess.engine.Limit(time=1.0))
                move = result.move
                
                # Verificar se é movimento de promoção
                if self.board.piece_at(move.from_square).piece_type == chess.PAWN:
                    if (self.board.turn == chess.WHITE and chess.square_rank(move.to_square) == 7) or \
                       (self.board.turn == chess.BLACK and chess.square_rank(move.to_square) == 0):
                        # Converter promoção automática do Stockfish
                        if move.promotion:
                            # Executar movimento de promoção
                            self.execute_move(move)
                            self.thinking = False
                            return
                
                # Movimento normal
                self.execute_move(move)
                print(f"Stockfish jogou: {move}")
                
            except Exception as e:
                print(f"Erro ao fazer movimento do bot: {e}")
            finally:
                self.thinking = False

    def set_game_result(self):
        if self.board.is_checkmate():
            winner = "Brancas" if not self.board.turn else "Pretas"
            self.message = f"Xeque-mate! {winner} vencem!"
        elif self.board.is_stalemate():
            self.message = "Empate por afogamento!"
        elif self.board.is_insufficient_material():
            self.message = "Empate por material insuficiente!"
        elif self.board.is_seventyfive_moves():
            self.message = "Empate por regra das 75 jogadas!"
        elif self.board.is_fivefold_repetition():
            self.message = "Empate por repetição quádrupla!"
        else:
            self.message = f"Jogo terminado: {self.board.result()}"

    def save_game(self):
        """Salva a partida atual em formato PGN"""
        try:
            # Criar objeto Game para PGN
            game = chess.pgn.Game()
            
            # Adicionar metadados
            game.headers["Event"] = "Partida de Xadrez"
            game.headers["Site"] = "Jogo Local"
            game.headers["Date"] = datetime.now().strftime("%Y.%m.%d")
            game.headers["Round"] = "1"
            game.headers["White"] = "Jogador" if self.player_color == chess.WHITE else "Stockfish"
            game.headers["Black"] = "Stockfish" if self.player_color == chess.WHITE else "Jogador"
            game.headers["Result"] = self.board.result()
            
            # Adicionar movimentos
            node = game
            temp_board = self.board.copy()
            move_stack = []
            
            # Recuperar todos os movimentos
            while temp_board.move_stack:
                move_stack.append(temp_board.pop())
            
            # Reaplicar movimentos na ordem correta
            for move in reversed(move_stack):
                node = node.add_variation(move)
            
            # Salvar em arquivo usando diálogo
            root = tk.Tk()
            root.withdraw()  # Esconder janela principal
            
            filename = filedialog.asksaveasfilename(
                defaultextension=".pgn",
                filetypes=[("PGN files", "*.pgn"), ("All files", "*.*")],
                title="Salvar Partida"
            )
            
            if filename:
                with open(filename, "w", encoding="utf-8") as f:
                    exporter = chess.pgn.FileExporter(f)
                    game.accept(exporter)
                print(f"Partida salva como {filename}")
                messagebox.showinfo("Sucesso", f"Partida salva como {filename}")
                return filename
            return None
        except Exception as e:
            print(f"Erro ao salvar partida: {e}")
            messagebox.showerror("Erro", f"Erro ao salvar partida: {e}")
            return None

    def load_game(self):
        """Carrega uma partida de um arquivo PGN"""
        try:
            # Abrir diálogo para selecionar arquivo
            root = tk.Tk()
            root.withdraw()  # Esconder janela principal
            
            filename = filedialog.askopenfilename(
                filetypes=[("PGN files", "*.pgn"), ("All files", "*.*")],
                title="Carregar Partida"
            )
            
            if filename:
                with open(filename, "r", encoding="utf-8") as f:
                    game = chess.pgn.read_game(f)
                    if game:
                        self.board = game.board()
                        for move in game.mainline_moves():
                            self.board.push(move)
                        print(f"Partida carregada de {filename}")
                        messagebox.showinfo("Sucesso", f"Partida carregada de {filename}")
                        return True
            return False
        except Exception as e:
            print(f"Erro ao carregar partida: {e}")
            messagebox.showerror("Erro", f"Erro ao carregar partida: {e}")
            return False

    def suggest_move(self):
        """Obtém uma sugestão de movimento do Stockfish"""
        try:
            print("Obtendo sugestão do Stockfish...")
            self.thinking = True
            result = engine.play(self.board, chess.engine.Limit(time=2.0))
            self.suggested_move = result.move
            print(f"Sugestão: {result.move}")
            self.thinking = False
            return result.move
        except Exception as e:
            print(f"Erro ao obter sugestão: {e}")
            self.thinking = False
            return None

    def toggle_analysis_mode(self):
        """Alterna o modo de análise"""
        self.analysis_mode = not self.analysis_mode
        if self.analysis_mode:
            self.message = "Modo de análise ativado"
        else:
            self.message = ""

def main():
    menu = Menu()
    game = None
    state = "menu"  # "menu" ou "game"
    
    clock = pygame.time.Clock()
    running = True
    
    while running:
        mouse_pos = pygame.mouse.get_pos()
        
        for event in pygame.event.get():
            if event.type == pygame.QUIT:
                running = False
            
            if state == "menu":
                result = menu.handle_event(event, mouse_pos)
                if result:
                    if result["action"] == "quit":
                        running = False
                    elif result["action"] == "load_game":
                        # Criar uma instância temporária para carregar
                        temp_game = Game(chess.WHITE, 10)
                        if temp_game.load_game():
                            game = temp_game
                            state = "game"
                    elif result["action"] == "start_game":
                        player_color = result["player_color"]
                        difficulty = result["difficulty"]
                        game = Game(player_color, difficulty)
                        state = "game"
            
            elif state == "game":
                # Lidar com diálogo de promoção primeiro
                if game.promotion_dialog:
                    result = game.promotion_dialog.handle_event(event, mouse_pos)
                    if result and result["action"] == "promote":
                        game.handle_promotion(result["piece"])
                else:
                    if event.type == pygame.MOUSEBUTTONDOWN:
                        if event.button == 1:  # Botão esquerdo do mouse
                            # Verificar cliques no painel lateral
                            sidebar_buttons = game.draw_sidebar(screen)
                            button_clicked = False
                            for button in sidebar_buttons:
                                result = button.handle_event(event)
                                if result:
                                    button_clicked = True
                                    if result["action"] == "save_game":
                                        game.save_game()
                                    elif result["action"] == "suggest_move":
                                        game.suggest_move()
                                    elif result["action"] == "toggle_analysis":
                                        game.toggle_analysis_mode()
                                    elif result["action"] == "restart":
                                        # Reiniciar com as mesmas configurações
                                        game = Game(game.player_color, game.difficulty_level)
                                    elif result["action"] == "main_menu":
                                        state = "menu"
                            
                            # Se não clicou em botão do painel, processar tabuleiro
                            if not button_clicked:
                                game.handle_click(event.pos)
                        elif event.button == 3:  # Botão direito do mouse
                            # Alternar visualização de movimentos válidos
                            game.show_valid_moves = not game.show_valid_moves
        
        # Desenhar
        if state == "menu":
            menu.draw(screen, mouse_pos)
        elif state == "game":
            screen.fill((0, 0, 0))
            game.draw_board(screen)
            game.draw_ui(screen)
            sidebar_buttons = game.draw_sidebar(screen)
            
            # Desenhar diálogo de promoção se necessário
            if game.promotion_dialog:
                game.promotion_dialog.draw(screen)
            
            # Fazer movimento do bot
            game.make_bot_move()
        
        pygame.display.flip()
        clock.tick(60)
    
    # Sair do Pygame e do Stockfish
    pygame.quit()
    engine.quit()
    print("Jogo encerrado.")

if __name__ == "__main__":
    main()