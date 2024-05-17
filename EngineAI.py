import random
import chess
import chess.engine
import matplotlib.pyplot as plt
import seaborn as sns
import pandas as pd

import torch
import torch.nn as nn

import numpy as np

from StockFishEvalBoard import StockFishEvalBoard
from ConvNEt import ChessCNN



class EngineAI:
    '''Takes in a board to find the next move and evaluate the next best position, using our AI'''
    def __init__(self, board):
        self.board = chess.Board(board) 
        self.model = ChessCNN()
        state_dict = torch.load('chess_cnn_model_50k.pth')
        self.model.load_state_dict(state_dict)
        self.model.eval()


    def get_random_move(self):
        legal_moves = list(self.board.legal_moves)
        
        if legal_moves:
            chosen = random.choice(legal_moves)
            return chosen
        return None

    def evaluate_board_piece_count(self, board):
        return sum([self.get_piece_value(piece) for piece in board.piece_map().values()])
    
    def fen_to_tensor(self, fen):
        piece_list = ['P', 'N', 'B', 'R', 'Q', 'K', 'p', 'n', 'b', 'r', 'q', 'k']
        piece_dict = {piece: i for i, piece in enumerate(piece_list)}
        
        board = chess.Board(fen)
        tensor = np.zeros((12, 8, 8), dtype=np.float32)
        
        for square in chess.SQUARES:
            piece = board.piece_at(square)
            if piece:
                piece_type = piece_dict[piece.symbol()]
                row, col = divmod(square, 8)
                tensor[piece_type, row, col] = 1
        
        return torch.tensor(tensor, dtype=torch.float32).unsqueeze(0)

    def evaluate_board_CNN(self, board):
        fen = board.fen()
        board_tensor = self.fen_to_tensor(fen)
        print(f"Board Tensor: {board_tensor}")
        with torch.no_grad():
            output = self.model(board_tensor)
        print(f"Model Output: {output}")
        return output.item()
    
    def get_piece_value(self, piece):
        values = {
            chess.PAWN: 1,
            chess.KNIGHT: 3,
            chess.BISHOP: 3,
            chess.ROOK: 5,
            chess.QUEEN: 9,
            chess.KING: 0
        }
        return values[piece.piece_type] if piece.color == chess.WHITE else -values[piece.piece_type]

    def minimax(self, board, depth, alpha, beta, is_maximizing, color):
        if depth == 0 or board.is_game_over():
            return color * self.evaluate_board_CNN(board)
        
        legal_moves = list(board.legal_moves)
        
        if is_maximizing:
            max_eval = float('-inf')
            for move in legal_moves:
                board.push(move)
                eval = self.minimax(board, depth - 1, alpha, beta, False, -color)
                board.pop()
                max_eval = max(max_eval, eval)
                alpha = max(alpha, eval)
                if beta <= alpha:
                    break
            return max_eval
        else:
            min_eval = float('inf')
            for move in legal_moves:
                board.push(move)
                eval = self.minimax(board, depth - 1, alpha, beta, True, -color)
                board.pop()
                min_eval = min(min_eval, eval)
                beta = min(beta, eval)
                if beta <= alpha:
                    break
            return min_eval

        
    def negamax(self, board, depth, alpha, beta, color):
        if depth == 0 or board.is_game_over():
            return color * self.evaluate_board_CNN(board)
        
        max_eval = float('-inf')
        legal_moves = list(board.legal_moves)
        
        for move in legal_moves:
            board.push(move)
            eval = -self.negamax(board, depth - 1, -beta, -alpha, -color)
            board.pop()
            max_eval = max(max_eval, eval)
            alpha = max(alpha, eval)
            if alpha >= beta:
                break
        
        return max_eval

    def get_best_move(self, max_depth, engine=None):
        best_move = None
        best_value = float('-inf')
        alpha = float('-inf')
        beta = float('inf')
        
        legal_moves = list(self.board.legal_moves)
        color = 1 if self.board.turn == chess.WHITE else -1  # Determine the current player's color

        
        for move in legal_moves:
            self.board.push(move)
            if engine == 'mini':
                board_value = self.minimax(self.board, max_depth - 1, alpha, beta, False, color)
            elif engine == 'nega':
                board_value = self.negamax(self.board, max_depth - 1, alpha, beta, color)
            else:
                print('fuck')
                board_value = self.negamax(self.board, max_depth - 1, alpha, beta, color)
            self.board.pop()

            if board_value > best_value:
                best_value = board_value
                best_move = move
        
        return best_move 
    
    def print_board_fancy(self, board):
        unicode_pieces = {
            'r': '♜', 'n': '♞', 'b': '♝', 'q': '♛', 'k': '♚', 'p': '♟',
            'R': '♖', 'N': '♘', 'B': '♗', 'Q': '♕', 'K': '♔', 'P': '♙'
        }
        print("  a b c d e f g h")
        print(" +-----------------+")
        for rank in range(8, 0, -1):
            print(f"{rank}|", end=" ")
            for file in range(1, 9):
                piece = board.piece_at(chess.square(file - 1, rank - 1))
                if piece:
                    print(unicode_pieces[piece.symbol()], end=" ")
                else:
                    print(".", end=" ")
            print(f"|{rank}")
        print(" +-----------------+")
        print("  a b c d e f g h")
        
    def visualize_evaluations(self, max_depth, engine='nega'):
        current_board = self.board.copy()
        move_path = []
        ai_evaluations = []
        stockfish_evaluations = []

        for _ in range(max_depth):
            best_move = self.get_best_move(max_depth, engine)
            if best_move is None:
                break
            
            # AI evaluation
            self.board.push(best_move)
            ai_evaluation = self.evaluate_board_CNN(self.board)
            ai_evaluations.append(ai_evaluation)
            
            # Stockfish evaluation
            stock = StockFishEvalBoard(self.board.fen())
            stockfish_evaluation = stock.stockfish_evaluation()
            stockfish_evaluations.append(stockfish_evaluation)
            
            # Move path
            move_path.append(self.board.fen())
            
            # Print the board
            self.print_board_fancy(self.board)

        # Reset the board to the original state
        self.board = current_board
        
        # Create a DataFrame for visualization
        df = pd.DataFrame({
            'Move Number': range(1, len(move_path) + 1),
            'AI Evaluation': ai_evaluations,
            'Stockfish Evaluation': stockfish_evaluations
        })

        # Plotting the evaluations
        plt.figure(figsize=(14, 7))
        sns.lineplot(x='Move Number', y='AI Evaluation', data=df, marker='o', label='AI Evaluation', color='blue')
        sns.lineplot(x='Move Number', y='Stockfish Evaluation', data=df, marker='o', label='Stockfish Evaluation', color='red')

        plt.title('AI Evaluation vs Stockfish Evaluation of Path of Moves')
        plt.xlabel('Move Number')
        plt.ylabel('Evaluation (Centipawn Score)')
        plt.axhline(0, color='gray', linewidth=0.8)  # Add a horizontal line at y=0
        plt.legend()
        plt.grid(True)
        plt.show()
    

    def play_stock_fish(self):
        max_iter = 256
        i = 0

        board = self.board
        who_goes_first = random.randint(0, 1)
        print('stockfish White - Conv Net 50k Black' if who_goes_first else 'Conv Net 50k White - stockfish Black')

        centipawn_losses = []

        while not board.is_game_over() and i < max_iter:
            # self.print_board_fancy(board)

            if who_goes_first:
                stock = StockFishEvalBoard(board)
                initial_score = stock.stockfish_evaluation()

                # print(f"initial_score_stock: {initial_score}")
                move = stock.stockfish_next_move()
                board.push(move)
            else:
                initial_score = self.evaluate_board_CNN(board)

                # print(f"initial_score_CNN: {initial_score}")
                move = self.get_best_move(3, self.evaluate_board_CNN, 'nega')
                board.push(move)

            who_goes_first = 0 if who_goes_first else 1

            if initial_score:
                centipawn_loss = abs(initial_score)
                centipawn_losses.append(centipawn_loss)
                # print(f"Centipawn loss: {centipawn_loss}")
            else:
                centipawn_losses.append(1000)

            

            i += 1

        return centipawn_losses




    


