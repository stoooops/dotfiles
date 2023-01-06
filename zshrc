################################################################################
# Environment Variables
################################################################################

export LANG=en_US.UTF-8

export EDITOR=vim
export P4EDITOR=vim
export OVERRIDE_EDITOR=vim

export HISTSIZE=16000 # spots for duplicates/uniques
export SAVEHIST=15000 # unique events guaranteed



###############################################################################
# ANSI color codes
###############################################################################

RED="\033[0;31m"
BRIGHT_RED="\033[1;31m"
GREEN="\033[0;32m"
YELLOW="\033[0;33m"
YELLOWISH="\033[38;5;220m"
BLUE="\033[0;34m"
MAGENTA="\033[0;35m"
CYAN="\033[0;36m"
WHITE="\033[0;37m"
ENDC="\033[0m"
# 256 colors
# https://jonasjacek.github.io/colors/
ORANGE="\033[38;5;166m"
PURPLE="\033[38;5;141m"
PINK="\033[38;5;217m"
BROWN="\033[38;5;130m"
LIME="\033[38;5;154m"
BRIGHT_GREEN="\033[38;5;118m"
TURQUOISE="\033[38;5;45m"
LIGHT_BLUE="\033[38;5;39m"



###############################################################################
# UNIX commands aliases
###############################################################################

alias ls="ls -Fh"
alias ll="ls -Flv"
alias lla="ls -aFlv"

alias cp="cp -i"
alias mv="mv -i"
alias rm="rm -i"



###############################################################################
# Git aliases
###############################################################################
alias g="git"

# add
alias ga="git a"

# branch
alias gb="git b"
alias gbm="git bm"

# commit
alias gc="git c"
alias gca="git ca"
alias gcm="git cm"
alias gcam="git cam"
alias gcamd="git camd"
alias gacamd="git caamd"
alias gamcamd="git camamd"

# checkout
alias gco="git co"

# cherry-pick
alias gcp="git cp"

# diff
alias gd="git d"
alias gdc="git dc"
alias gdcc="git dcc"
alias gdh="git dh"
alias gdnr="git dnr"
alias gdw="git dw"
alias gdwnr="git dwnr"

# fetch
alias gf="git f"

# init
alias gi="git i"

# log
alias gl="git l"
alias gld="git ld"
alias gldag="git ldag"
alias glg="git lg"
alias glga="git lga"
alias glgd="git lgd"
alias gll="git ll"
alias glld="git lld"
alias gls="git ls"

# merge
alias gm="git m"

# pull
alias gpl="git pl"

# push
alias gpu="git pu"
alias gpuf="git puf"
alias gpuu="git puu"

# status
alias gss="git ss"
# check if in repo and run ls if not run `git status`
gst() {
    # check if in a git repo
    # git rev-parse --git-dir 2>/dev/null ||
    if [ "$(git rev-parse --is-inside-work-tree 2>/dev/null)" ]; then
        git status
    else
        echo "📁 $(pwd)"
        ls --color=auto -Fh --group-directories-first
        echo
    fi
}
alias gstu="git stu"
alias gsb="git sb"
# typo
alias gstg="git st"

# rebase
alias grb="git rb"
alias grbc="git rbc"
alias grbs="git rbs"

# reset
alias grs="git rs"
alias grss="git rss"
alias grss1="git rss1"
alias grss2="git rss2"
alias grss3="git rss3"



###############################################################################
# Options that enable or disable shell behavior:
###############################################################################

# Save command history with timestamps and duration
setopt extended_history

# Incrementally add new history lines
setopt inc_append_history

# Expire duplicates first when history is full
setopt hist_expire_dups_first

# Verify history expansion rather than executing immediately
setopt hist_verify

# Share history between all instances of the shell
setopt share_history

# Don't automatically change directories when entering a directory name
unsetopt autocd



###############################################################################
# Options that enable or disable shell prompts:
###############################################################################

# Enable prompt string substitution
setopt PROMPT_SUBST

#
# Options that enable or disable shell features:
#

# Enable spelling correction for commands
# setopt correct

# Enable automatic cd to directories without typing "cd"
# setopt autocd

#
# Options that control the history file:
#

# Append new history lines rather than replacing existing ones
# setopt hist_append

# Append history immediately rather than waiting until the session is terminated
# setopt immediate_history

# Don't save command history with timestamps and duration
# unsetopt extended_history

# Don't incrementally add new history lines
# unsetopt inc_append_history

# Don't expire duplicates first when history is full
# unsetopt hist_expire_dups_first

# Execute history expansion immediately rather than verifying first
# unsetopt hist_verify

# Don't share history between instances of the shell
# unsetopt share_history

# Disable prompt string substitution
# unsetopt PROMPT_SUBST



###############################################################################
# Configuring bindkey Utility
###############################################################################

# Set default command line editing mode to vi
# set editing-mode vi

# Set default keymap to vi-command
# set keymap vi-command

# Set bindkey utility to operate in vi command mode
bindkey -v

# Set key binding for Ctrl-Y to yank (copy) rest of line in vi insert mode
# bindkey -M viins '^Y' vi-yank-eol

# Set key binding for Ctrl-L to clear screen
# bindkey '^L' clear-screen

# Set key binding for Ctrl-D to delete character under cursor
# bindkey '^D' delete-char

# Set key binding for Ctrl-W to delete previous word
# bindkey '^W' backward-kill-word

# Set key binding for Ctrl-R to perform incremental search backward through command history
bindkey '^R' history-incremental-search-backward






###############################################################################
# PS1 prompt
###############################################################################

# Display the current git branch
parse_git_branch() {
    local branch_name="$(git symbolic-ref HEAD 2>/dev/null | cut -d"/" -f 3)"
    if [ ! "$branch_name" ]; then
        local git_sha="$(git rev-parse --short HEAD)"
        echo "%{$BRIGHT_RED%}($git_sha)%{$ENDC%}"
    else
        if [ "$branch_name" = "master" ]; then
            echo "%{$MAGENTA%}($branch_name)%{$ENDC%}"
        else
            echo "%{$PURPLE%}($branch_name)%{$ENDC%}"
        fi
    fi
}

# Display information about any uncommitted changes in the current git repository
parse_git_changes() {
    local num_untracked_files="$(git ls-files --others --exclude-standard | wc -l)"
    local num_modified_files="$(git diff --name-only | wc -l)"
    local num_deleted_files="$(git diff --diff-filter=D --name-only | wc -l)"
    local num_added_files="$(git diff --cached --name-only | wc -l)"
    if [ "$num_added_files" -gt 0 ]; then
        echo -n "%{$BRIGHT_GREEN%}+$num_added_files%{$ENDC%}"
    fi
    if [ "$num_untracked_files" -gt 0 ]; then
        echo -n "%{$CYAN%}+$num_untracked_files%{$ENDC%}"
    fi
    if [ "$num_modified_files" -gt 0 ]; then
        echo -n "%{$YELLOWISH%}~$num_modified_files%{$ENDC%}"
    fi
}

# Display the current git branch and any uncommitted changes
parse_git() {
    if ! git rev-parse --git-dir > /dev/null 2>&1; then
        # We are not in a Git repository
        return
    fi
    local branch="$(parse_git_branch)"
    local changes="$(parse_git_changes)"
    if [ "$branch" ] || [ "$changes" ]; then
        echo -n " $branch$changes"
    fi
}

# Function to determine whether the current user is root
parse_command_prompt() {
  if [[ $EUID -eq 0 ]]; then
    # Root user
    echo "%{$BRIGHT_RED%}#%{$ENDC%}"
  else
    # Non-root user
    echo "%{$WHITE%}$%{$ENDC%}"
  fi
}

# Format the home directory for display in the prompt
format_homedir() {
    local dir="$PWD"
    local home="$HOME"
    local home_len=${#home}
    local dir_len=${#dir}
    if [[ "$dir" == "$home" ]]; then
        # Current working directory is home
        echo -n "%{$BLUE%}~%{$ENDC%}"
    elif [[ "$dir" == "$home/"* ]]; then
        # Current working directory is subdirectory of home
        echo -n "%{$LIME%}~%{$ENDC%}%{$TURQUOISE%}${dir:$home_len}%{$ENDC%}"
    else
        # Current working directory is outside of home
        echo -n "%{$ORANGE%}$dir%{$ENDC%}"
    fi
}

# Set the prompt
PS1='$(format_homedir)$(parse_git) $(parse_command_prompt) '



################################################################################
# tmux
################################################################################

NEED_SET_PATH=
if [ -z "$TMUX" ]; then
    NEED_SET_PATH=true
fi
if [ ${NEED_SET_PATH} ]; then
    export PATH=/usr/bin:$HOME/bin:/usr/local/bin:$PATH
fi
unset NEED_SET_PATH



################################################################################
# X Server
#################################################################################

if grep -q icrosoft /proc/version; then
    echo "Ubuntu on Windows"
    export DISPLAY=$(cat /etc/resolv.conf | grep nameserver | awk '{print $2}'):0
else
    echo -e "${BLUE}Linux version $(uname -r)${NC}"
    #export DISPLAY=localhost:0.0
fi
echo "DISPLAY=${DISPLAY}"


################################################################################
# pyenv
################################################################################

# https://github.com/lablup/backend.ai/wiki/Install-Python-via-pyenv
PYENV_ROOT="${HOME}/.pyenv"
if [ -d ${PYENV_ROOT} ]; then
    echo -e "${GREEN}pyenv installed${NC}"

    export PYENV_ROOT

    if [ ${NEED_SET_PATH} ]; then
        export PATH="${PYENV_ROOT}/bin:$PATH"
    fi

    # Load pyenv automatically
    type pyenv && \
        eval "$(pyenv init -)" && \
        eval "$(pyenv init --path)" && \
        eval "$(pyenv virtualenv-init -)"
else
    echo -e "${YELLOW}pyenv not installed${NC}"
fi


################################################################################
# go
################################################################################

if [ -d /usr/local/go ]; then
    echo -e "${GREEN}go installed${NC}"
    if [ ${NEED_SET_PATH} ]; then
        export PATH=$PATH:/usr/local/go/bin
    fi
else
    echo -e "${YELLOW}go not installed${NC}"
fi



###############################################################################
# Sublime Text
###############################################################################

# Run Sublime Text in another session
alias subl="setsid subl"



###############################################################################
# Custom functions
###############################################################################

# Copy standard input to clipboard and display on terminal.
ctrlc() {
    tee >(xclip -sel clip) "$@" && echo "\n📋 Copied to clipboard"
}
cntrlc() {
    ctrlc
}

# Trim trailing whitespace
ttws()
    cat $1 | sed -e 's/[[:blank:]]*$//'

# Extract file
extract() {
    if [ -f $1 ] ; then
        case $1 in
            *.tar.bz2)  tar xjf $1      ;;
            *.tar.gz)   tar xzf $1      ;;
            *.bz2)      bunzip2 $1      ;;
            *.rar)      rar x $1        ;;
            *.gz)       gunzip $1       ;;
            *.tar)      tar xf $1       ;;
            *.tbz2)     tar xjf $1      ;;
            *.tgz)      tar xzf $1      ;;
            *.zip)      unzip $1        ;;
            *.Z)        uncompress $1   ;;
            *)          echo "'$1' cannot be extracted via extract()" ;;
        esac
    else
        echo "'$1' is not a valid file"
    fi
}
