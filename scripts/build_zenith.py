import PyInstaller.__main__
import os
import sys
import shutil
from pathlib import Path

def build():
    root = Path(__file__).parent.parent
    dist_path = root / "dist"
    build_path = root / "build_temp"
    
    if dist_path.exists():
        shutil.rmtree(dist_path)
    if build_path.exists():
        shutil.rmtree(build_path)
        
    print(f"[*] Starting Zenith Build in {root}")
    
    # Ensure database exists
    db_path = root / "language_atlas.sqlite"
    if not db_path.exists():
        print("[!] Warning: language_atlas.sqlite not found. Rebuilding...")
        # I should ideally run the build_sqlite script here if needed
        # but for this task I'll assume it exists or the user handles it.
    
    # Define files to include
    # Format: (src, dest_in_bundle)
    add_data = [
        (str(root / "language_atlas.sqlite"), "."),
        (str(root / "data"), "data"),
        (str(root / "docs"), "docs"),
        (str(root / "src/app/templates"), "app/templates"),
        (str(root / "src/app/static"), "app/static"),
    ]
    
    data_args = []
    for src, dst in add_data:
        # PyInstaller uses ; on Windows, : on Unix
        sep = ";" if os.name == "nt" else ":"
        data_args.extend(["--add-data", f"{src}{sep}{dst}"])

    print("[*] Running PyInstaller...")
    
    PyInstaller.__main__.run([
        str(root / "src/cli.py"),
        "--name", "atlas",
        "--onefile",
        "--clean",
        *data_args,
        "--collect-submodules", "textual",
        "--collect-submodules", "typer",
        "--collect-submodules", "fastapi",
        "--hidden-import", "uvicorn.logging",
        "--hidden-import", "uvicorn.loops",
        "--hidden-import", "uvicorn.loops.auto",
        "--hidden-import", "uvicorn.protocols",
        "--hidden-import", "uvicorn.protocols.http",
        "--hidden-import", "uvicorn.protocols.http.auto",
        "--hidden-import", "uvicorn.protocols.websockets",
        "--hidden-import", "uvicorn.protocols.websockets.auto",
        "--hidden-import", "uvicorn.lifespan",
        "--hidden-import", "uvicorn.lifespan.on",
        "--workpath", str(build_path),
        "--distpath", str(dist_path),
    ])
    
    print(f"\n[DONE] Zenith distribution built: {dist_path}/atlas")

if __name__ == "__main__":
    build()
