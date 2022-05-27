from pathlib import Path
import requests
import time
import pandas as pd
import chess

TOTAL_GAMES_THRESHOLD = 100
OPENING_LEN = 10
OPENINGS_CSV = Path(f'openings_{OPENING_LEN}_{TOTAL_GAMES_THRESHOLD}.csv')


def get_openings_df():
    if OPENINGS_CSV.exists():
        df = pd.read_csv(OPENINGS_CSV)
        df['san_moves'] = df['san_moves'].apply(eval)
        return df
    else:
        return pd.DataFrame(columns=[
            'san_moves',
            'fen',
            'white_wins',
            'black_wins',
            'draws',
        ])


def fetch_lichess_fen(fen):
    url = f'https://explorer.lichess.ovh/masters?variant=standard' \
          f'&fen={fen}' \
          f'&play=&since=1952&until=2022'
    res = requests.get(url)
    time.sleep(1)
    return res.json()


def scrape_lichess(depth):
    openings_df = get_openings_df()
    seen_san_moves = set(openings_df['san_moves'].apply(eval))
    csv_cols = openings_df.columns
    return helper(chess.Board(), (), seen_san_moves, csv_cols, depth)


def helper(board, san_moves, seen_san_moves, csv_cols, depth):
    if san_moves in seen_san_moves:
        print(f'Skipping {san_moves} due to completed tree...')
        return [()]
    seen_san_moves.add(san_moves)
    if len(san_moves) == depth:
        return [()]
    res_data = fetch_lichess_fen(board.fen())
    openings = []
    for move in res_data['moves']:
        total_games = move['white'] + move['black'] + move['draws']
        if total_games >= TOTAL_GAMES_THRESHOLD:
            board.push_san(move['san'])
            new_san_moves = san_moves + (move['san'],)
            if new_san_moves not in seen_san_moves:
                print(f'Playing move {move["san"]}:\n{board}')
                next_openings = helper(board, new_san_moves, seen_san_moves,
                                       csv_cols, depth)
                append_to_openings_csv(new_san_moves, board, move, csv_cols)
                for next_opening in next_openings:
                    openings.append((move,) + next_opening)
            board.pop()
            print(f'Undoing move {move["san"]}:\n{board}')
        else:
            print(f'Skipping opening {san_moves + (move["san"],)} due to too few games ({total_games})')
    return openings


def append_to_openings_csv(san_moves, board, move, expected_cols):
    data = {
        'san_moves': san_moves,
        'fen': board.fen(),
        'white_wins': move['white'],
        'black_wins': move['black'],
        'draws': move['draws'],
    }
    new_row = pd.DataFrame([data])
    assert (new_row.columns == expected_cols).all()
    write_header = not OPENINGS_CSV.exists()
    new_row.to_csv(OPENINGS_CSV, mode='a', header=write_header, index=False)


def prune_openings_csv():
    openings_df = get_openings_df()
    print(f'Original length: {len(openings_df)}')
    total_games = openings_df['white_wins'] + openings_df['black_wins'] + openings_df['draws']
    openings_df = openings_df[total_games >= TOTAL_GAMES_THRESHOLD]
    openings_df['san_moves'] = openings_df['san_moves'].apply(eval)
    openings_df = openings_df[openings_df['san_moves'].apply(len) == OPENING_LEN]
    pruned_openings_csv = Path('pruned_openings.csv')
    openings_df.to_csv(pruned_openings_csv, index=False)
    print(f'Pruned length: {len(openings_df)}')
