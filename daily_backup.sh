#!/bin/bash
# ================= 設定區 =================
# --- SSH 連線 (dev -> prod) ---
BACKUP_ENV="/home/ubuntu/.backup.env"
if [ -f "$BACKUP_ENV" ]; then
    set -a
    . "$BACKUP_ENV"
    set +a
else
    echo "Error: backup env not found at $BACKUP_ENV"
    exit 1
fi
SSH_OPTS="-i $PEM_KEY"

# --- 遠端 (tbia-prod) 路徑與資料庫 ---
PROD_PROJECT_DIR="/home/ubuntu/tbia-portal"        # prod 上的專案路徑 (含 .env)
PROD_MEDIA_DIR="/home/ubuntu/tbia-volumes/media/"  # prod 上的 media 來源
PORTAL_CONTAINER="tbia-db-prod-container"
PORTAL_DB="tbia"
DATAHUB_CONTAINER="tbia-datahub-db-container"
DATAHUB_DB="tbiadata"
DATAHUB_TABLE="dataset"

# --- 本地 (tbia-dev) 存放路徑 ---
LOCAL_BACKUP_DIR="/home/ubuntu/tbia-volumes/prod_backups"
LOCAL_MEDIA_DIR="${LOCAL_BACKUP_DIR}/media"

# --- dev 本地 arklet 資料庫 (只有 dev 有、只備份 dev) ---
ARKLET_PROJECT_DIR="/home/ubuntu/tbia-arklet"   # ← 請改成 dev 上 arklet 專案實際路徑 (含 .env)
ARKLET_CONTAINER="arklet_db"
PROD_ARKLET_BACKUP_DIR="/home/ubuntu/tbia-volumes/arklet_backups"

# --- datahub_bucket dump (dev -> prod) ---
LOCAL_DATAHUB_DUMP_DIR="/home/ubuntu/tbia-volumes/datahub_bucket/dump/"
PROD_DATAHUB_DUMP_DIR="/home/ubuntu/tbia-volumes/datahub_bucket/dump"

# --- 其他 ---
RETENTION_DAYS=7
DATE=$(date +%Y%m%d_%H%M%S)
# ==========================================

mkdir -p "$LOCAL_BACKUP_DIR" "$LOCAL_MEDIA_DIR"

echo "=== [1/5] Backing up PROD databases (remote dump -> dev) at $DATE ==="

# Portal DB (整庫)：在 prod 上 dump，壓縮後串流回 dev
echo "Backing up Portal DB ($PORTAL_DB)..."
PORTAL_FILENAME="portal_${PORTAL_DB}_${DATE}.sql.gz"
ssh $SSH_OPTS "$PROD_SSH" "
    set -eo pipefail
    export \$(grep -v '^#' '$PROD_PROJECT_DIR/.env' | xargs)
    docker exec -e PGPASSWORD=\"\$POSTGRES_PASSWORD\" $PORTAL_CONTAINER \
        pg_dump -U postgres -d $PORTAL_DB | gzip
" > "$LOCAL_BACKUP_DIR/$PORTAL_FILENAME"
if [ $? -eq 0 ]; then echo "Portal DB backup OK."; else echo "Error: Portal DB backup failed!"; fi

# Datahub DB (單一 table)
echo "Backing up Datahub DB Table ($DATAHUB_TABLE)..."
DATAHUB_FILENAME="datahub_${DATAHUB_DB}_${DATAHUB_TABLE}_${DATE}.sql.gz"
ssh $SSH_OPTS "$PROD_SSH" "
    set -eo pipefail
    export \$(grep -v '^#' '$PROD_PROJECT_DIR/.env' | xargs)
    docker exec -e PGPASSWORD=\"\$DATAHUB_POSTGRES_PASSWORD\" $DATAHUB_CONTAINER \
        pg_dump -U postgres -d $DATAHUB_DB -t $DATAHUB_TABLE | gzip
" > "$LOCAL_BACKUP_DIR/$DATAHUB_FILENAME"
if [ $? -eq 0 ]; then echo "Datahub DB backup OK."; else echo "Error: Datahub DB backup failed!"; fi

echo "=== [2/5] Backing up DEV-local arklet DB ==="
if [ -f "$ARKLET_PROJECT_DIR/.env" ]; then
    # 用 subshell 載入 arklet 帳密，避免變數外洩污染
    (
        set -a
        . "$ARKLET_PROJECT_DIR/.env"
        set +a
        ARKLET_FILENAME="arklet_${POSTGRES_DB}_${DATE}.sql.gz"
        echo "Backing up arklet DB ($POSTGRES_DB)..."
        docker exec -e PGPASSWORD="$POSTGRES_PASSWORD" "$ARKLET_CONTAINER" \
            pg_dump -U "$POSTGRES_USER" -d "$POSTGRES_DB" | gzip \
            > "$LOCAL_BACKUP_DIR/$ARKLET_FILENAME"

        if [ $? -eq 0 ]; then
            echo "Arklet DB backup OK."
            # 推送 arklet 備份到 prod 異地留存
            echo "Pushing arklet backup to prod..."
            ssh $SSH_OPTS "$PROD_SSH" "mkdir -p $PROD_ARKLET_BACKUP_DIR"
            rsync -avz -e "ssh $SSH_OPTS" \
                "$LOCAL_BACKUP_DIR/$ARKLET_FILENAME" \
                "$PROD_SSH:$PROD_ARKLET_BACKUP_DIR/"
            if [ $? -eq 0 ]; then echo "Arklet push OK."; else echo "Error: Arklet push failed!"; fi

            # 清理 prod 端過期的 arklet 備份
            echo "Cleaning up old arklet backups on prod..."
            ssh $SSH_OPTS "$PROD_SSH" \
                "find $PROD_ARKLET_BACKUP_DIR -maxdepth 1 -type f -name '*.sql.gz' -mtime +$RETENTION_DAYS -delete"
        else
            echo "Error: Arklet DB backup failed!"
        fi
    )
else
    echo "Error: arklet .env not found at $ARKLET_PROJECT_DIR"
fi

echo "=== [3/5] Syncing Media Files (prod -> dev) ==="
rsync -avz -e "ssh $SSH_OPTS" \
    --include='/download/' \
    --include='/download/storage/' \
    --include='/download/storage/**' \
    --exclude='*' \
    "$PROD_SSH:$PROD_MEDIA_DIR" "$LOCAL_MEDIA_DIR/"
if [ $? -eq 0 ]; then echo "Media sync OK."; else echo "Error: Media sync failed!"; fi

echo "=== [4/5] Syncing datahub_bucket dump (dev -> prod) ==="
ssh $SSH_OPTS "$PROD_SSH" "mkdir -p $PROD_DATAHUB_DUMP_DIR"
rsync -avz -e "ssh $SSH_OPTS" \
    "$LOCAL_DATAHUB_DUMP_DIR" "$PROD_SSH:$PROD_DATAHUB_DUMP_DIR/"
if [ $? -eq 0 ]; then echo "Datahub dump sync OK."; else echo "Error: Datahub dump sync failed!"; fi

echo "=== [5/5] Cleaning up old backups (dev, older than $RETENTION_DAYS days) ==="
find "$LOCAL_BACKUP_DIR" -maxdepth 1 -type f -name "*.sql.gz" -mtime +$RETENTION_DAYS -delete
echo "All tasks finished."