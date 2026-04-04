#!/bin/bash
# scripts/atlas-fuzzy.sh
# Fuzzy-search the atlas and launch TUI or Info view

# Ensure we are in the project root
cd "$(dirname "$0")/.." || exit

DB_PATH="language_atlas.sqlite"

if [ ! -f "$DB_PATH" ]; then
    echo "Error: Database not found at $DB_PATH"
    exit 1
fi

if ! command -v fzf &> /dev/null; then
    echo "Error: fzf is not installed. Please install it to use this script."
    exit 1
fi

# Get languages and years
LANGS=$(sqlite3 "$DB_PATH" "SELECT name || ' (' || year || ')' FROM languages ORDER BY year;")

# Use fzf for selection
# ENTER: Launch TUI
# CTRL-I: Launch Info
# We use --expect to capture which key was pressed
RESULT=$(echo "$LANGS" | fzf \
    --prompt="Living Atlas > " \
    --header="ENTER: TUI | CTRL-I: Info | ESC: Exit" \
    --expect=ctrl-i,enter \
    --height=40% \
    --border)

# fzf with --expect returns the key on the first line and the selection on the second
KEY=$(echo "$RESULT" | head -n 1)
SELECTED=$(echo "$RESULT" | sed -n '2p')

if [ -n "$SELECTED" ]; then
    # Extract language name (text before the last ' (')
    # Python (1991) -> Python
    LANG_NAME=$(echo "$SELECTED" | sed 's/ ([0-9]*)$//')
    
    if [ "$KEY" == "ctrl-i" ]; then
        python3 src/cli.py info "$LANG_NAME"
    else
        # Default is TUI
        python3 src/tui.py "$LANG_NAME"
    fi
fi
