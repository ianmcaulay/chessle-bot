from collections import Counter
import random
from pathlib import Path
import pickle
import chess
import chess.polyglot

OPENINGS_PICKLE_FILE = Path('openings.pkl')


class Info:

    def __init__(self, known_idxs=None, known_moves=None, non_idxs=None, non_moves=None):
        """
        known_idxs: {idx: move} We know move is at idx.
        known_moves: [move] We know these moves are somewhere in the solution.
                     Moves in known_idxs are not included.
                     May contain duplicates if that move is played multiple times.
        non_idxs: {idx: {move}} We know idx is not any of the moves in its set.
        non_moves: {move} We know these moves are not in the solution.
        """
        self.known_idxs = known_idxs or {}
        self.known_moves = known_moves or []
        self.non_idxs = non_idxs or {}
        self.non_moves = non_moves or set()
        self.all_openings = get_all_openings()
        self.openings = self.all_openings.copy()

    def prune(self):
        self.openings = [opening for opening in self.all_openings if self.is_valid_opening(opening)]

    def add_known_idx(self, idx, move):
        self.known_idxs[idx] = move
        self.prune()

    def add_known_move(self, move):
        self.known_moves.append(move)
        self.prune()

    def add_non_idx(self, idx, move):
        if idx in self.non_idxs:
            self.non_idxs[idx].add(move)
        else:
            self.non_idxs[idx] = {move}
        self.prune()

    def add_non_move(self, move):
        self.non_moves.add(move)
        self.prune()

    def is_valid_opening(self, opening):
        for idx, move in self.known_idxs.items():
            if opening[idx] != move:
                return False
        # TODO: this doesn't work for copies of a move in known_moves.
        if not set(self.known_moves) <= set(opening):
            return False
        for idx, move in enumerate(opening):
            if move in self.non_idxs.get(idx, set()):
                return False
        # TODO: not sure how accurate this is.
        remaining_opening = ['_' if self.known_idxs.get(i, None) == move else move
                             for i, move in enumerate(opening)]
        if set(remaining_opening) & set(self.non_moves):
            return False
        return True

    def choose_next_guess(self):
        assert self.openings
        move_counts = get_move_counts(self.openings)
        max_openings = []
        max_score = None
        for opening in self.openings:
            score = get_opening_moves_score(opening, move_counts)
            if max_score is None or score > max_score:
                max_score = score
                max_openings.append(opening)
        # Arbitrarily choose the first one.
        return max_openings[0]

    def parse_outcome(self, guess, outcome):
        # outcome is a list the same length as guess which contains "c", "i", and "m".
        # "c" means the move at that position is correct, "i" means incorrect, and "m" means misplaced.
        assert len(guess) == len(outcome)
        assert set(outcome) <= {'c', 'i', 'm'}
        # TODO: should only prune once at the end of this.
        for i, move in enumerate(outcome):
            if move == 'c':
                self.add_known_idx(i, guess[i])
            elif move == 'i':
                self.add_non_move(guess[i])
            elif move == 'm':
                self.add_known_move(guess[i])
                self.add_non_idx(i, guess[i])


def get_openings_from_position(reader, board, remaining_moves):
    if remaining_moves == 0:
        return [()]
    openings = []
    for entry in reader.find_all(board):
        san_move = board.san(entry.move)
        board.push(entry.move)
        if san_move == 'd4' and remaining_moves == 10:
            import pdb; pdb.set_trace()
        next_openings = get_openings_from_position(
            reader, board, remaining_moves - 1)
        board.pop()
        # TODO: not sure if this works when there are no moves left.
        for next_opening in next_openings:
            openings.append((san_move,) + next_opening)
    return openings


def get_all_openings(regenerate=False):
    if regenerate or not OPENINGS_PICKLE_FILE.exists():
        openings = gen_all_openings()
        with open(OPENINGS_PICKLE_FILE, 'wb') as f:
            pickle.dump(openings, f)
    else:
        with open(OPENINGS_PICKLE_FILE, 'rb') as f:
            openings = pickle.load(f)
    return openings


def gen_all_openings():
    opening_book_path = Path('Human.bin')
    assert opening_book_path.exists()
    board = chess.Board()
    opening_len = 10
    with chess.polyglot.open_reader(opening_book_path) as reader:
        openings = get_openings_from_position(reader, board, opening_len)
    # Some openings may be too short.
    openings = [opening for opening in openings if len(opening) == opening_len]
    return openings


def get_move_counts(openings):
    moves = {}
    for opening in openings:
        # TODO: should maybe deal with duplicate letters here, or maybe not.
        for move in opening:
            moves[move] = moves.get(move, 0) + 1
    return moves


def get_opening_moves_score(opening, move_counts):
    score = 0
    # This is a very simple scoring system, there's probably something much better.
    for move in set(opening):
        score += move_counts[move]
    return score


def get_guess_outcome(guess, solution):
    assert len(guess) == len(solution)
    # Start by assuming every move is incorrect.
    outcome = ['i'] * len(guess)
    for i in range(len(guess)):
        if guess[i] == solution[i]:
            outcome[i] = 'c'
            solution = solution[:i] + ('_',) + solution[i+1:]
    solution_counts = Counter(solution)
    for i in range(len(guess)):
        if outcome[i] == 'i' and solution_counts[guess[i]] > 0:
            outcome[i] = 'm'
            solution_counts[guess[i]] -= 1
    return outcome


def simulate_run(solution):
    info = Info()
    #opening_strs = [['_'.join(move) for move in opening] for opening in info.openings]
    #assert '_'.join(solution) in opening_strs
    assert solution in info.openings
    guess = None
    num_guesses = 0
    print(f'Solution: {solution}')
    while guess != solution:
        guess = info.choose_next_guess()
        num_guesses += 1
        outcome = get_guess_outcome(guess, solution)
        print(f'Guessing {guess} with outcome {outcome}')
        info.parse_outcome(guess, outcome)
    print(f'Found solution {solution} in {num_guesses} guesses!')
    return num_guesses


def simulate_runs(n=100):
    all_num_guesses = []
    openings = get_all_openings()
    while n > 0:
        solution = random.choice(openings)
        num_guesses = simulate_run(solution)
        all_num_guesses.append(num_guesses)
        n -= 1
    return all_num_guesses


def main():
    ...
    from pprint import pprint
    openings = get_all_openings()
    info = Info()
    import pdb; pdb.set_trace()
    simulate_runs(1)


if __name__ == '__main__':
    main()
