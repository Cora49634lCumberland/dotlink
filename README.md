# dotlink

A simple dotfile manager that tracks symlinks and syncs configs across machines via a git repo.

---

## Installation

```bash
pip install dotlink
```

Or install from source:

```bash
git clone https://github.com/yourname/dotlink.git && cd dotlink && pip install .
```

---

## Usage

Initialize a new dotlink repo in your home directory:

```bash
dotlink init ~/dotfiles
```

Track a config file by adding it to your dotlink repo:

```bash
dotlink add ~/.bashrc
dotlink add ~/.config/nvim/init.lua
```

This moves the file into `~/dotfiles`, creates a symlink in its original location, and stages the change in git.

Sync your dotfiles on a new machine:

```bash
git clone https://github.com/yourname/dotfiles.git ~/dotfiles
dotlink sync
```

`dotlink sync` reads the tracked manifest and recreates all symlinks automatically.

Check the status of tracked files:

```bash
dotlink status
```

---

## Commands

| Command         | Description                              |
|-----------------|------------------------------------------|
| `init <path>`   | Initialize a new dotlink repository      |
| `add <file>`    | Track a file and create a symlink        |
| `sync`          | Restore all symlinks from the manifest   |
| `status`        | Show tracked files and symlink health    |
| `remove <file>` | Untrack a file and restore it in place   |

---

## License

MIT © [yourname](https://github.com/yourname)