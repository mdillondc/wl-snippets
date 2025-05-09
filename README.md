# wl-snippets

A minimalist text snippet manager for Wayland with fuzzy search, dark mode (Nord theme), and keyboard-centric navigation. Copy text snippets to your clipboard quickly with a lightweight interface that works seamlessly in Wayland environments.

## Features

- 🔍 Fuzzy search for quick snippet finding
- 🌙 Nord theme (modify if you want)
- 📋 Works with Wayland via wl-clipboard
- ⌨️ Keyboard-friendly navigation

## Installation

### System Dependencies

First, install the required system packages:

```bash
sudo apt install python3-gi python3-gi-cairo gir1.2-gtk-3.0 wl-clipboard
```

### Setup with Conda

1. Create a conda environment:
```bash
conda create -n wl-snippets python=3.10 -y
```

2. Activate the environment:
```bash
conda activate wl-snippets
cd wl-snippets
```

3. Install the required dependencies within the conda environment:
```bash
conda install -c conda-forge pygobject gtk3 -y
pip install -r requirements.txt
```

### Running wl-snippets

1. Create a snippets directory (default: `~/Sync/scripts/wl-snippets/snippets/`)
2. Add text files to this directory - each file will be available as a snippet
3. Run the application:
```bash
conda activate wl-snippets
./wl-snippets.py
```

## Customization

To change the snippets directory, modify the `snippets_dir` variable in `wl-snippets.py`.

## Keybinding

Bind whatever you want to `~/miniconda3/envs/wl-snippets/bin/python ~/Sync/scripts/wl-snippets/wl-snippets.py`.