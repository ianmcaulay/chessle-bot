# chessle-solver

This is a bot to solve daily Chessle puzzles at https://jackli.gg/chessle/.

## Setup:

Install requirements.txt, e.g. using virtualenv:
```
virtualenv -p python3.9 env
source env/bin/activate
pip install -r requirements.txt
```

## Usage:

Edit the `main()` function of `chessle.py`. 

### simulate_run

`simulate_run` shows the bot's guesses and results for a given opening if you already know the solution. It takes an opening as input, represented 
as a tuple of strings where each string is a move in chess notation. A single string with all 10 moves 
(such as given by chessle once finished) can be converted to an opening tuple with `opening_str_to_tuple`.

Example:
```
def main():
    opening_str = '1. e4 e5 2. Nc3 Nf6 3. Bc4 Nxe4 4. Qh5 Nd6 5. Bb3 Be7'
    opening = opening_str_to_tuple(opening_str)
    simulate_run(opening)
```
```
>>> python chessle.py
Solution: "1. e4 e5 2. Nc3 Nf6 3. Bc4 Nxe4 4. Qh5 Nd6 5. Bb3 Be7"
Remaining openings: 44829
Guessing: "1. e4 c5 2. Nf3 d6 3. d4 cxd4 4. Nxd4 Nf6 5. Nc3 a6" with outcome 🟩⬛⬛⬛⬛⬛⬛🟨🟨⬛
Remaining openings: 62
Guessing: "1. e4 e5 2. Bc4 Nf6 3. d3 Nc6 4. Nc3 Na5 5. Nge2 Nxc4" with outcome 🟩🟩🟨🟩⬛⬛🟨⬛⬛⬛
Remaining openings: 1
Guessing: "1. e4 e5 2. Nc3 Nf6 3. Bc4 Nxe4 4. Qh5 Nd6 5. Bb3 Be7" with outcome 🟩🟩🟩🟩🟩🟩🟩🟩🟩🟩
Found solution "1. e4 e5 2. Nc3 Nf6 3. Bc4 Nxe4 4. Qh5 Nd6 5. Bb3 Be7" in 3 guesses!
```

### run_interactively

`run_interactively` lets the bot play chessle one guess at a time, with the user inputting the guesses to chessle and telling the bot the result.
The bot will generate its next best guess given previous information, and wait for the user to reply with the outcome. The outcome should be a
string of length 10 composed of the characters `c`, `m`, and `i`. `c` indicates the move guessed at that index is correct (i.e. a green square),
`m` indicates it's misplaced (i.e. yellow square), and `i` indicates incorrect (i.e. black or gray square). For example:
  
🟩🟩🟨🟩⬛⬛🟨⬛⬛⬛ would
be coded as `ccmciimiii`.

```
def main():
    run_interactively()
```
```
>>> python chessle.py 
Remaining openings: 44829
Guess = ('e4', 'c5', 'Nf3', 'd6', 'd4', 'cxd4', 'Nxd4', 'Nf6', 'Nc3', 'a6')
Outcome?ciiiiiimmi
Remaining openings: 62
Guess = ('e4', 'e5', 'Bc4', 'Nf6', 'd3', 'Nc6', 'Nc3', 'Na5', 'Nge2', 'Nxc4')
Outcome?ccmciimiii
Remaining openings: 1
Guess = ('e4', 'e5', 'Nc3', 'Nf6', 'Bc4', 'Nxe4', 'Qh5', 'Nd6', 'Bb3', 'Be7')
Outcome?cccccccccc
Correct!
```
