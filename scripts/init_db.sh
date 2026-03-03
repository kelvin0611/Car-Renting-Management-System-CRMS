#!/usr/bin/env bash
set -e

PROJECT_ROOT="$(cd "$(dirname "${BASH_SOURCE[0]}")/.." && pwd)"
DB_NAME_DEFAULT="p2p_car_rental"

RESET=0
if [ "${1:-}" = "--reset" ]; then
  RESET=1
fi

if ! command -v mysql >/dev/null 2>&1; then
  echo "ERROR: mysql command not found in PATH."
  echo "Tips: On macOS (official installer), try:"
  echo "  export PATH=\"/usr/local/mysql/bin:\$PATH\""
  exit 127
fi

echo "==> Loading DB config from backend/.env (if exists)..."
if [ -f "$PROJECT_ROOT/backend/.env" ]; then
  # 將 .env 內容匯入為環境變數
  set -a
  # shellcheck disable=SC1091
  source "$PROJECT_ROOT/backend/.env"
  set +a
else
  echo "    backend/.env not found, using default values."
fi

DB_HOST="${DB_HOST:-127.0.0.1}"
DB_PORT="${DB_PORT:-3306}"
DB_USER="${DB_USER:-root}"
DB_PASSWORD="${DB_PASSWORD:-}"
DB_NAME="${DB_NAME:-$DB_NAME_DEFAULT}"

echo "==> Connecting to MySQL: ${DB_USER}@${DB_HOST}:${DB_PORT}"

MYSQL_CMD=(mysql -h"$DB_HOST" -P"$DB_PORT" -u"$DB_USER")
if [ -n "$DB_PASSWORD" ]; then
  # 簡單起見，直接用 -p 參數（可能會有 warning 但在本地開發可以接受）
  MYSQL_CMD+=(-p"$DB_PASSWORD")
fi

DB_EXISTS="$("${MYSQL_CMD[@]}" -N -e "SELECT SCHEMA_NAME FROM INFORMATION_SCHEMA.SCHEMATA WHERE SCHEMA_NAME='${DB_NAME}';" 2>/dev/null || true)"
if [ "$RESET" -eq 0 ] && [ "$DB_EXISTS" = "$DB_NAME" ]; then
  echo "==> Database '${DB_NAME}' already exists. Skipping init."
  echo "    If you want to reset (DROP + recreate), run:"
  echo "      ./scripts/init_db.sh --reset"
  exit 0
fi

if [ "$RESET" -eq 1 ]; then
  echo "==> Reset mode: dropping database '${DB_NAME}'..."
  "${MYSQL_CMD[@]}" -e "DROP DATABASE IF EXISTS \`${DB_NAME}\`;"
fi

echo "==> Creating schema (createTable.sql)..."
"${MYSQL_CMD[@]}" < "$PROJECT_ROOT/database/createTable.sql"

echo "==> Inserting seed data (insertData.sql)..."
"${MYSQL_CMD[@]}" < "$PROJECT_ROOT/database/insertData.sql"

echo "==> Database init completed."

