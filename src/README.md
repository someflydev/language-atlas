# Language Atlas Source

This directory contains the core logic for the Language Atlas project, including the Web UI and the CLI tool.

## Structure

- `app/`: The FastAPI web application, templates, and static assets.
- `cli.py`: Command-line interface for exploring the language data.
- `app/core/`: Shared data loading logic.

## Web Application

The web application provides a visual interface for exploring the evolution of programming languages.

### Features

- **Interactive Atlas:** Explore a grid of language cards with primary paradigm and cluster badges.
- **Advanced Filtering:**
    - **Cluster Filter:** Multi-select checkboxes for domains like 'Systems', 'Web', or 'Cloud'.
    - **Paradigm Filter:** Filter by 'Functional', 'Object-Oriented', and more.
    - **Year Range Slider:** Double-ended slider with instant updates (1930 - 2024).
- **Immersive Profiles:** Detailed language pages featuring:
    - **Vital Statistics:** Quick-access sidebar for creators, paradigms, and established dates.
    - **Markdown Rendering:** Beautifully styled technical documentation and discovery missions.
- **Deep Exploration:** Clickable paradigm and cluster tags that open dedicated, descriptive view pages with their own sorting controls.
- **Modern Styling:** Built with Tailwind CSS for a professional, responsive, and framework-free experience.

### Setup & Run

1. **Install `uv`** (if not already installed):
   Follow the instructions at [astral.sh/uv](https://astral.sh/uv) to install `uv` on your system.

2. **Create a virtual environment and install dependencies**:
   From the project root, use `uv` to create a synced environment:
   ```bash
   uv venv --python 3.12
   source .venv/bin/activate  # On Windows: .venv\Scripts\activate
   uv pip install -r src/app/requirements.txt
   ```

3. **Start the server**:
   ```bash
   python3 src/app/app.py
   ```
   The application will be available at `http://localhost:8000`.

## CLI Tool

The CLI tool allows for quick querying and filtering of language data directly from the terminal.

### Usage

To run the CLI tool from the project root, ensure the `src` directory is in your `PYTHONPATH`:

```bash
export PYTHONPATH=$PYTHONPATH:$(pwd)/src
python3 src/cli.py list
```

#### Commands:
- `list`: List all languages.
- `list --cluster <name>`: Filter by cluster (e.g., scientific, systems).
- `list --gen <name>`: Filter by generation (e.g., early, renaissance).
- `show <language_name>`: Show detailed information for a specific language.
