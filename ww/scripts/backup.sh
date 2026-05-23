#!/bin/bash
#
# backup.sh — Backup MacBook Pro to Ubuntu machine (192.168.1.36)
# Run on the MacBook:  bash ~/backup.sh
#
# Destination: /mnt/data/wuhuarong/macbook-backup/ on the Ubuntu machine
#

set -e

REMOTE_USER="lzw"
REMOTE_HOST="192.168.1.36"
REMOTE_DIR="/mnt/data/wuhuarong/macbook-backup"
TIMESTAMP=$(date +%Y%m%d_%H%M%S)
LOG_FILE="$HOME/backup_${TIMESTAMP}.log"

GREEN='\033[0;32m'
YELLOW='\033[1;33m'
RED='\033[0;31m'
NC='\033[0m'

log()  { echo -e "${GREEN}[$(date +%H:%M:%S)]${NC} $1" | tee -a "$LOG_FILE"; }
warn() { echo -e "${YELLOW}[WARN]${NC} $1" | tee -a "$LOG_FILE"; }
err()  { echo -e "${RED}[ERROR]${NC} $1" | tee -a "$LOG_FILE"; }

# ---- Step 0: Pre-checks ----
log "========================================="
log "  MacBook Backup — Starting"
log "  Target: ${REMOTE_USER}@${REMOTE_HOST}:${REMOTE_DIR}"
log "========================================="

# Test SSH key auth
if ! ssh -o ConnectTimeout=5 -o BatchMode=yes -o StrictHostKeyChecking=no \
     ${REMOTE_USER}@${REMOTE_HOST} "echo OK" &>/dev/null; then
    err "SSH key auth failed to ${REMOTE_USER}@${REMOTE_HOST}"
    err "Make sure your SSH public key is in ~/.ssh/authorized_keys on the target"
    exit 1
fi
log "SSH key auth: OK"

# Check rsync
if ! command -v rsync &>/dev/null; then
    err "rsync not found. Install: brew install rsync"
    exit 1
fi

SSH_OPT="-o StrictHostKeyChecking=no"

# ---- Create remote dirs ----
log "Creating remote directory structure..."
ssh ${SSH_OPT} ${REMOTE_USER}@${REMOTE_HOST} "mkdir -p ${REMOTE_DIR}/{ssh,config,shell,projects,desktop,documents,downloads,personal,joplin,openclaw,wechat,docker,maven,token}"

# ---- Helper ----
backup_item() {
    local src="$1"
    local dest_sub="$2"
    local desc="$3"

    if [ ! -e "$src" ]; then
        warn "SKIP (not found): $src"
        return
    fi

    log ">> $desc"
    rsync -avh --progress --partial \
        -e "ssh ${SSH_OPT}" \
        "$src" \
        ${REMOTE_USER}@${REMOTE_HOST}:${REMOTE_DIR}/${dest_sub}/ \
        2>&1 | tee -a "$LOG_FILE" | tail -1

    if [ ${PIPESTATUS[0]} -eq 0 ]; then
        log "   OK: $desc"
    else
        err "   FAIL: $desc (see log)"
    fi
}

# ============================================================
#  PHASE 1: Critical — SSH, Git, Shell configs
# ============================================================
log "========================================="
log "  PHASE 1: Critical (SSH, Git, Shell)"
log "========================================="

backup_item "$HOME/.ssh/id_rsa"        "ssh"    "SSH private key"
backup_item "$HOME/.ssh/id_rsa.pub"    "ssh"    "SSH public key"
backup_item "$HOME/.ssh/known_hosts"   "ssh"    "SSH known_hosts"
backup_item "$HOME/.gitconfig"         "config" "Git config"
backup_item "$HOME/.npmrc"             "config" "NPM config (.npmrc)"
backup_item "$HOME/.yarnrc"            "config" "Yarn config (.yarnrc)"
backup_item "$HOME/.zshrc"             "shell"  "Zsh config"
backup_item "$HOME/.bash_profile"      "shell"  "Bash profile"
backup_item "$HOME/.bashrc"            "shell"  "Bashrc"
backup_item "$HOME/.profile"           "shell"  "Profile"
backup_item "$HOME/.zsh_history"       "shell"  "Zsh history"
backup_item "$HOME/.bash_history"      "shell"  "Bash history"
backup_item "$HOME/.viminfo"           "shell"  "Vim info"

# ============================================================
#  PHASE 2: Projects (biggest — 27GB)
# ============================================================
log "========================================="
log "  PHASE 2: Projects (~27GB, be patient)"
log "========================================="

backup_item "$HOME/Projects"           "projects" "All projects"

# ============================================================
#  PHASE 3: Personal files
# ============================================================
log "========================================="
log "  PHASE 3: Personal files"
log "========================================="

backup_item "$HOME/Desktop"            "desktop"    "Desktop"
backup_item "$HOME/Documents"          "documents"  "Documents"
backup_item "$HOME/Downloads"          "downloads"  "Downloads"
backup_item "$HOME/个人资料"           "personal"   "个人资料"
backup_item "$HOME/照片整理"           "personal"   "照片整理"
backup_item "$HOME/Pictures"           "personal"   "Pictures"

# ============================================================
#  PHASE 4: App data & configs
# ============================================================
log "========================================="
log "  PHASE 4: App configs & data"
log "========================================="

backup_item "$HOME/JoplinBackup"       "joplin"   "Joplin notes backup"
backup_item "$HOME/.openclaw"          "openclaw" "OpenClaw config + data"
backup_item "$HOME/WeChatProjects"     "wechat"   "WeChat mini projects"
backup_item "$HOME/.docker/config.json" "docker"  "Docker config"
backup_item "$HOME/.docker/daemon.json" "docker"  "Docker daemon"
backup_item "$HOME/.m2"                "maven"    "Maven local repo"
backup_item "$HOME/.token"             "token"    "Token files"

# ============================================================
#  PHASE 5: Generate manifest
# ============================================================
log "========================================="
log "  Generating manifest..."
log "========================================="

ssh ${SSH_OPT} ${REMOTE_USER}@${REMOTE_HOST} "
cd ${REMOTE_DIR}
echo '# Backup manifest — ${TIMESTAMP}' > MANIFEST.txt
echo '# Source: MacBook Pro (wuhuarong@192.168.1.49)' >> MANIFEST.txt
echo '' >> MANIFEST.txt
for dir in */; do
    size=\$(du -sh \"\$dir\" 2>/dev/null | cut -f1)
    echo \"\${dir}  \${size}\" >> MANIFEST.txt
done
echo '' >> MANIFEST.txt
total=\$(du -sh . 2>/dev/null | cut -f1)
echo \"TOTAL: \${total}\" >> MANIFEST.txt
cat MANIFEST.txt
"

# ============================================================
#  DONE
# ============================================================
log "========================================="
log "  BACKUP COMPLETE!"
log "========================================="
log "Log:       $LOG_FILE"
log "Location:  ${REMOTE_USER}@${REMOTE_HOST}:${REMOTE_DIR}"
log ""
log "Verify on Ubuntu machine:"
log "  ls -la /mnt/data/wuhuarong/macbook-backup/"
log "  cat /mnt/data/wuhuarong/macbook-backup/MANIFEST.txt"
