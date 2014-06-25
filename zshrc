# Read Oh-My-Zsh
if [ -f ~/.zsh.oh-my-zsh ]; then
  source ~/.zsh.oh-my-zsh
fi

# Read aliases
if [ -f ~/.aliases ]; then
  source ~/.aliases
fi

# Read environment variables
if [ -f ~/.zsh.env ]; then
  source ~/.zsh.env
fi

# Read custom functions
if [ -f ~/.zsh.functions ]; then
  source ~/.zsh.functions
fi

# Read local zshrc, if present
if [ -f ~/.zshrc.local ]; then
  source ~/.zshrc.local
fi

