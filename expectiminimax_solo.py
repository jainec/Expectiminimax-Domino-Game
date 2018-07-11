from collections import namedtuple
import random
from utils import argmax, vector_add
import time

infinity = float('inf')
GameState = namedtuple('GameState', 'to_move,pedras,pedras_restantes, ponta1, ponta2, moves, utility')

class Game:
    """A game has a utility for each
    state and a terminal test. To create a game, subclass this class and implement actions,
    result, utility, and terminal_test. You may override display and
    successors or you can inherit their default methods. You will also
    need to set the .initial attribute to the initial state; this can
    be done in the constructor."""

    def actions(self, state, turn):
        """Return a list of the allowable moves at this point."""
        raise NotImplementedError

    def result(self, state, turn):
        """Return the state that results from making a move from a state."""
        raise NotImplementedError

    def utility(self, state, player):
        """Return the value of this final state to player."""
        raise NotImplementedError

    def terminal_test(self, state):
        """Return True if this is a final state for the game."""
        return not self.actions(state)

    def to_move(self, state):
        """Return the player whose move it is in this state."""
        return state.to_move

    def display(self, state):
        """Print or otherwise display the state."""
        print(state)

    def __repr__(self):
        return '<{}>'.format(self.__class__.__name__)

    def play_game(self, *players):
        """Play an n-person, move-alternating game."""
        state = self.initial
        while True:
            for player in players:
                move = player(self, state)
                state = self.result(state, move)
                if self.terminal_test(state):
                    self.display(state)
                    return self.utility(state, self.to_move(self.initial))

class StochasticGame(Game):
    """A stochastic game includes uncertain events which influence
    the moves of players at each state. To create a stochastic game, subclass
    this class and implement chances and outcome along with the other
    unimplemented game class methods."""

    def chances(self, state):
        """Return a list of all possible uncertain events at a state."""
        raise NotImplementedError

    def outcome(self, state, chance):
        """Return the state which is the outcome of a chance trial."""
        raise NotImplementedError

    def probability(self, chance):
        """Return the probability of occurence of a chance."""
        raise NotImplementedError

    def play_game(self, *players):
        """Play an n-person, move-alternating stochastic game."""
        state = self.initial
        while True:
            for player in players:
                chance = random.choice(self.chances(state))
                state = self.outcome(state, chance)
                move = player(self, state)
                state = self.result(state, move)
                if self.terminal_test(state):
                    self.display(state)
                    return self.utility(state, self.to_move(self.initial))


def random_player(game, state):
    """A player that chooses a legal move at random."""
    return random.choice(game.actions(state))

def expectiminimax(game,state):
    """Return the best move for a player after dice are thrown. The game tree
	includes chance nodes along with min and max nodes. [Figure 5.11]"""
    player = game.to_move(state)
    d = 0
    n = len(state.pedras)
    if n == 7 or n == 6:
        d = 7
    elif n == 5 or n == 4:
        d = 5
    else:
        d = 9

    def max_value(state, depth):
        v = -infinity
        if depth >= d:
            return game.eval(state, player)
        for acao in game.actions(state):
            v = max(v, chance_node(state, acao, depth))
        return v

    def min_value(state, depth):
        if depth >= d:
            return game.eval(state, player)
        v = infinity
        for acao in game.actions(state):
            v = min(v, chance_node(state, acao, depth))
        return v

    def chance_node(state, action, depth):
        res_state = game.result(state, action, player)
        if game.terminal_test(res_state):
            return game.utility(res_state, player)
        if depth >= d:
            return game.eval(state, player)
        sum_chances = 0
        chances = game.chances(res_state)
        num_chances = len(chances)
        for chance in chances:
            res_state = game.outcome(res_state, chance)
            util = 0
            if res_state.to_move == player:
                util = max_value(res_state, depth+1)
            else:
                util = min_value(res_state, depth+1)
            sum_chances += util * game.probability(chance)
        return sum_chances / num_chances

    # Body of expectiminimax:
    return argmax(game.actions(state),
                  key=lambda a: chance_node(state, a, 1))

class Pedra:

    def __init__(self, a, b,position):
        self.valor = (a, b)
        self.position = position

    def __eq__(self, other):
        return (self.valor[0] == other.valor[0] and self.valor[1] == other.valor[1]) or (self.valor[0] == other.valor[1] and self.valor[1] == other.valor[0])

    def igual(self, p):
        if p.position == -1:
            if self.valor[0] == p.valor[0] or self.valor[1] == p.valor[1] or self.valor[1] == p.valor[0] or self.valor[1] == p.valor[0]:
                return True
        if p.position == 0:
            if self.valor[1] == p.valor[0] or self.valor[0] == p.valor[0]:
                return True
        if p.position == 1:
            if self.valor[1] == p.valor[1] or self.valor[0] == p.valor[1]:
                return True
        return False

    def getValor(self):
        return self.valor[0] + self.valor[1]

    def __str__(self):
        if self.position != 1:
            return "(" + str(self.valor[0]) + ", " + str(self.valor[1]) + ")"
        else:
            return "(" + str(self.valor[1]) + ", " + str(self.valor[0]) + ")"


def imprimestate(res_state):
    print("To move: ", res_state.to_move)
    print("Ponta 1 = ", res_state.ponta1, " Ponta 2 = ", res_state.ponta2)
    print("Pedras")
    for i in res_state.pedras:
        print(i)
    print("Restantes")
    for i in res_state.pedras_restantes:
        print(i)
    print("Moves")
    for i in res_state.moves:
        print("(", i[0], ", ponta=", i[1], ")")

class Domino(StochasticGame):

    def __init__(self):
        self.pedras = self.cria_domino()
        self.jogadores = self.escolhe_pedras()
        pedras_restantes = []
        for i in range(1, 4):
            pedras_restantes += self.jogadores[i]
        self.initial = GameState(to_move=0, pedras=list(self.jogadores[0]), pedras_restantes=pedras_restantes, ponta1=None,ponta2=None,
                                 moves=self.moves(0,self.jogadores[0], pedras_restantes, None, None, 0), utility=0)

    def cria_domino(self):
        pedras = []
        for i in range(7):
            for j in range(7):
                if i >= j:
                    pedras.append(Pedra(i, j, -1))
        return pedras

    def escolhe_pedras(self):
        pedras = list(self.pedras)
        n = len(self.pedras)
        jogadores = [[] for i in range(4)]
        for j in range(4):
            for k in range(7):
                pos = random.randint(0, n)
                jogadores[j].append(pedras.pop(pos-1))
                n -= 1

        return jogadores

    def actions(self, state):
        return state.moves

    def buchas(self, pedras):
        res = 0
        for pedra in pedras:
            if pedra.valor[0] == pedra.valor[1]:
                if pedra.valor[0] != 0:
                    res += pedra.valor[0]
                else:
                    res += 1
        return res
    
    def soma_pedras_max(self, state):
        soma = 0
        for pedra in state.pedras:
            soma += pedra.getValor()
        return soma
    
    def checa_diversidade_max(self, state):
        nipes = [False] * 7;
        res = 0
        for pedra in state.pedras:
            if 0 == pedra.valor[0] or 0 == pedra.valor[1]:
                nipes[0] = True
            if 1 == pedra.valor[0] or 1 == pedra.valor[1]:
                nipes[1] = True
            if 2 == pedra.valor[0] or 2 == pedra.valor[1]:
                nipes[2] = True
            if 3 == pedra.valor[0] or 3 == pedra.valor[1]:
                nipes[3] = True
            if 4 == pedra.valor[0] or 4 == pedra.valor[1]:
                nipes[4] = True
            if 5 == pedra.valor[0] or 5 == pedra.valor[1]:
                nipes[5] = True
            if 6 == pedra.valor[0] or 6 == pedra.valor[1]:
                nipes[6] = True
        for e in nipes:
            if e == True:
                res = res + 1
        return res
    
    def eval_0(self, state, player):
        n = len(state.pedras)
        m = len(state.pedras_restantes)/3
        buchas = self.buchas(state.pedras)
        soma_pedras = self.soma_pedras_max(state)   
        delta = m - n
        return -0.9*buchas - 0.2*n + 0.7*delta - 0.4*soma_pedras
        
    def eval_1(self, state, player):
        movimentos = self.moves(player, state.pedras, state.pedras_restantes, state.ponta1, state.ponta2, player)
        diversidade = self.checa_diversidade_max(state)
        return 0.5*movimentos + 0.6*diversidade
    
    def eval_2(self, state, player):
        n = len(state.pedras)
        m = len(state.pedras_restantes)/3
        buchas = self.buchas(state.pedras)
        n_pedras = n
        delta = m - n
        movimentos = self.moves(player, state.pedras, state.pedras_restantes, state.ponta1, state.ponta2, player)
        soma_pedras = self.soma_pedras_max(state)
        diversidade = self.checa_diversidade_max(state)
        return -0.9*buchas - 0.2*n_pedras + 0.7*delta + 0.5*len(movimentos) - 0.4*soma_pedras + 0.6*diversidade

    def eval(self, state, player):      #Para testes
        n = len(state.pedras)
        m = len(state.pedras_restantes)/3
        buchas = self.buchas(state.pedras)
        n_pedras = n
        delta = m - n
        movimentos = self.moves(player, state.pedras, state.pedras_restantes, state.ponta1, state.ponta2, player)
        soma_pedras = self.soma_pedras_max(state)
        diversidade = self.checa_diversidade_max(state)
        if player == 0:
            return -0.9*buchas - 0.2*n + 0.7*delta - 0.4*soma_pedras
        elif player == 1:
            return 0.5*len(movimentos) + 0.6*diversidade
        elif player == 2:
            return -0.9*buchas - 0.2*n_pedras + 0.7*delta + 0.5*len(movimentos) - 0.4*soma_pedras + 0.6*diversidade
   

    def moves(self,to_move,pedras, pedras_restantes, ponta1, ponta2, player):
        moves = []
        i = 0
        if to_move == player:

            for pedra in pedras:
                if ponta1 is not None:
                    if pedra.igual(ponta1):
                        i += 1
                        moves.append((pedra, 0))
                    elif pedra.igual(ponta2):
                        i += 1
                        moves.append((pedra, 1))
                else:
                    moves.append((pedra, -1))
        else:
            for pedra in pedras_restantes:
                if ponta1 is not None:
                    if pedra.igual(ponta1):
                        i += 1
                        moves.append((pedra, 0))
                    elif pedra.igual(ponta2):
                        i += 1
                        moves.append((pedra, 1))
                else:
                    moves.append((pedra, -1))

        if i == 0:
            moves.append((Pedra(-1, -1, -1), -1))
        return moves


    def compute_utility(self, to_move, pedras, pedras_restantes, ponta1, ponta2, move,player):
        if move[0].valor[0] == -1 and ponta1 is not None:
            for p in pedras_restantes:
                if p.igual(ponta1) or p.igual(ponta2):
                    return 0
            for p in pedras:
                if p.igual(ponta1) or p.igual(ponta2):
                    return 0
            total = len(pedras)
            soma = 0
            for pedra in pedras:
                soma += pedra.getValor()
            pedras_restantes.sort(key=lambda x: (x.valor[0] + x.valor[1]))
            soma_res = 0
            for i in range(min([total, len(pedras_restantes)])):
                soma_res += pedras_restantes[i].getValor()
            if soma < soma_res:
                if to_move != player:
                    return -1
                else:
                    return 4
            else:
                if to_move != player:
                    return -1
                else:
                    return 4
                
        elif move[0].valor[0] != -1:
            if to_move == player:
                if len(pedras) == 1:
                    return 4
                else:
                    return 0
            else:
                if len(pedras_restantes) == 3:
                    return -1
                else:
                    return 0
        else:
            return -1


    def soma_pedras(self,i):
        res = 0
        for pedra in self.jogadores[i]:
            res += pedra.getValor()
        return res


    def menor_soma(self):
        return argmax([0, 1, 2, 3],
               key=lambda a: -self.soma_pedras(a))


    def utility(self, state, player):
        """Return the value to player; 1 for win, -1 for loss, 0 otherwise."""
        return state.utility


    def terminal_test(self, state):
        """A state is terminal if it is won or there are no empty squares."""
        return state.utility != 0


    def display(self, state):
        imprimestate(state)


    def pode_jogar(self, i, state):
        if state.ponta1 is not None:
            for pedra in self.jogadores[i]:
                if pedra.igual(state.ponta1) or pedra.igual(state.ponta2):
                    return True
            return False
        else:
            return True


    def vitoria(self, state):
        for i in range(4):
            if len(self.jogadores[i]) == 0:
                return i
        for i in range(4):
            if self.pode_jogar(i, state):
                return -1
        return self.menor_soma()


    def result(self, state, move,player):
        pedras = list(state.pedras)
        pedras_restantes = list(state.pedras_restantes)
        ponta1 = state.ponta1
        ponta2 = state.ponta2
        utility = self.compute_utility(state.to_move, state.pedras, state.pedras_restantes, state.ponta1,state.ponta2, move, player)

        if move[0].valor[0] != -1:
            if state.ponta1 is not None:
                if move[1] == 0:
                    if move[0].valor[0] == state.ponta1.valor[0] or move[0].valor[0] == state.ponta1.valor[1]:
                        move[0].position = 1
                        if state.ponta1.position == -1:
                            state.ponta1.position = 1
                    elif move[0].valor[1] == state.ponta1.valor[0] or move[0].valor[1] == state.ponta1.valor[1]:
                        move[0].position = 0
                        if state.ponta1.position == -1:
                            state.ponta1.position = 1
                    ponta1 = move[0]
                elif move[1] == 1:
                    if move[0].valor[0] == state.ponta2.valor[0] or move[0].valor[0] == state.ponta2.valor[1]:
                        move[0].position = 1
                    elif move[0].valor[1] == state.ponta2.valor[0] or move[0].valor[1] == state.ponta2.valor[1]:
                        move[0].position = 0
                    ponta2 = move[0]

            else:
                move[0].position = -1
                ponta1 = move[0]
                ponta2 = move[0]
            if state.to_move == player:
                pedras.remove(move[0])
            else:
                pedras_restantes.remove(move[0])

        to_move = (state.to_move + 1) % 4
        new_state = GameState(to_move=to_move, pedras=pedras, pedras_restantes=pedras_restantes, ponta1=ponta1,
                              ponta2=ponta2, moves=self.moves(to_move, pedras, pedras_restantes, ponta1, ponta2, player), utility=utility)
        return new_state


    def ponta1(self, move):
        return move[1] == 0


    def ponta2(self, move):
        return move[1] == 1


    def chances(self, state):
        n_moves = len(state.moves)
        lista = []
        if state.to_move != 0:
            n = len(state.pedras_restantes)

            p1 = (1, list(filter(self.ponta1, state.moves)), n_moves, n)
            if len(p1[1]) > 0:
                lista.append(p1)
            p2 = (2, list(filter(self.ponta2, state.moves)), n_moves, n)
            if len(p2[1]) > 0:
                lista.append(p2)
            pi = (-1, [(Pedra(-1, -1, -1), -1)], n_moves, n)
            lista.append(pi)

            return lista
        else:
            return [(0, state.moves, n_moves, len(state.pedras))]


    def probability(self, chance):
        if chance[0] == 1 or chance[0] == 2:
            return len(chance[1])/chance[3]
        elif chance[0] == -1:
            return 1 - (chance[2]/chance[3])
        else:
            return 1


    def imprime_jogadores(self):
        i = 0
        for jogador in self.jogadores:
            print("Jogador ", i)
            i+=1
            for pedra in jogador:
                print(pedra)


    def outcome(self, state, chance):
        return GameState(to_move=state.to_move, pedras=state.pedras, pedras_restantes=state.pedras_restantes, ponta1=state.ponta1,
                         ponta2=state.ponta2, moves=chance[1], utility=state.utility)


    def play_game(self, *players):
        """Play an n-person, move-alternating game."""
        state = self.initial
        inicio = time.time()
        k = 0
        while True:
            print("Rodada: ", k)
            k += 1
            for player in players:
                move = player(self, state)
                self.imprime_jogadores()
                print("To_move: ", state.to_move)
                print("Pontas: ", state.ponta1, " ", state.ponta2)
                print("Move: ", move[0], ", ", move[1])
                if move[0].valor[0] != -1:
                    self.jogadores[state.to_move].remove(move[0])

                state_res = self.result(state, move, state.to_move)
                vencedor = self.vitoria(state_res)
                if vencedor != -1:
                    fim = time.time()
                    print("Jogador Vencedor: ")
                    print(vencedor)
                    return vencedor
                ponta1 = state_res.ponta1
                ponta2 = state_res.ponta2
                to_move = state_res.to_move
                pedras_restantes = []
                for i in range(4):
                    if i != to_move:
                        pedras_restantes += self.jogadores[i]
                state = GameState(to_move=to_move, pedras=list(self.jogadores[to_move]), pedras_restantes=pedras_restantes, ponta1=ponta1, ponta2=ponta2,
                                  moves=self.moves(to_move, self.jogadores[to_move], pedras_restantes, ponta1, ponta2, to_move),
                                  utility=self.compute_utility(to_move, self.jogadores[to_move], pedras_restantes, ponta1, ponta2, move,to_move))

get_ipython().run_line_magic('matplotlib', 'inline')
import matplotlib.pyplot as plt

def graph_winrates(no_of_iterations, *agents):
    graphs = {agent:[] for agent in [0,1,2,3]}
    wins = [0,0,0,0]
    for iteration in range(1,no_of_iterations+1):
        d = Domino()
        vencedor = d.play_game(*agents)
        wins[vencedor] += 1
        print(iteration)            
        for agent in [0,1,2,3]:
            graphs[agent].append((iteration, wins[agent]))
    for agent, value in graphs.items():
        state_x, state_y = zip(*value)
        plt.plot(state_x, state_y, label=str(agent))
    plt.ylim([0,no_of_iterations])
    plt.legend(loc='lower right')
    plt.xlabel('Iterations')
    plt.ylabel('Wins')

                
if __name__ == "__main__":
    graph_winrates(5, expectiminimax, expectiminimax, expectiminimax, random_player)
   
