import chess
import chess.engine
import random
import math

"""
Monte Carlo Tree Search
"""


class MCTSNode:
    def __init__(self, board, parent=None):
        self.board = board
        self.parent = parent
        self.children = []
        self.visits = 0
        self.value = 0

    def select_child(self):
        best_child = None
        best_ucb1 = -float('inf')
        
        for child in self.children:
            exploitation = child.value / child.visits if child.visits > 0 else 0
            exploration = math.sqrt(2 * math.log(self.visits) / child.visits) if child.visits > 0 else float('inf')
            ucb1 = exploitation + exploration
            if ucb1 > best_ucb1:
                best_ucb1 = ucb1
                best_child = child
        
        return best_child

    def expand(self):
        legal_moves = list(self.board.legal_moves)
        for move in legal_moves:
            next_board = self.board.copy()
            next_board.push(move)
            child_node = MCTSNode(next_board, parent=self)
            self.children.append(child_node)

    def simulate(self):
        current_board = self.board.copy()
        while not current_board.game_is_over():
            legal_moves = list(current_board.legal_moves)
            move = random.choice(legal_moves)
            current_board.push(move)
        return current_board.get_reward()

    def backpropagate(self, result):
        node = self
        while node is not None:
            node.visits += 1
            node.value += result
            node = node.parent


class MCTS:
    def __init__(self, board):
        self.root = MCTSNode(board)

    def run(self, iterations):
        for _ in range(iterations):
            node = self.root
            while node.children:
                node = node.select_child()
            if not node.board.game_is_over:
                node.expand()
                result = node.simulate()
                node.backpropagate(result)

    def best_move(self):
        best_child = max(self.root.children, key=lambda child: child.visits)
        return best_child.board.peek()

# Example usage
# mcts = MCTS(board)
# mcts.run(iterations=1000)
# best_move = mcts.best_move()
