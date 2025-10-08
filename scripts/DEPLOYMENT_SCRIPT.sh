#!/bin/bash
# Deployment script for insnrg custom component
# IMPORTANT: Only deploy the inner source directory, never the project root!
# Project root:      custom_components/insnrg/insnrg
# Deployment source: custom_components/insnrg/insnrg/custom_components/insnrg
# Deployment target: ../../docker/config/custom_components/insnrg



# Determine the directory where the script resides
SCRIPT_DIR="$(cd "$(dirname "${BASH_SOURCE[0]}")" && pwd)"

# Normalize and resolve absolute paths for SRC and DST
COMPONENT_SRC_REL="../custom_components/insnrg"
cd "$SCRIPT_DIR/$COMPONENT_SRC_REL" && SRC="$(pwd)" && cd "$SCRIPT_DIR"
if cd "$SCRIPT_DIR/../../../../docker/config/custom_components/insnrg" 2>/dev/null; then
  DST="$(pwd)"
  cd "$SCRIPT_DIR"
else
  echo "ERROR: Deployment target directory does not exist: $SCRIPT_DIR/../../../../docker/config/custom_components/insnrg" >&2
  exit 1
fi
DOCKER_DIR="$SCRIPT_DIR/../../../../docker"
HA_LOG="$DOCKER_DIR/config/home-assistant.log"

step() {
  echo -e "\n========== $1 =========="
}






SRC_REALPATH_OUTPUT=$(realpath "$SRC" 2>&1)
SRC_REALPATH_STATUS=$?
if [ $SRC_REALPATH_STATUS -ne 0 ] || [ -z "$SRC_REALPATH_OUTPUT" ]; then
  if [ -n "$SRC_REALPATH_OUTPUT" ]; then
    echo "$SRC_REALPATH_OUTPUT"
    echo "$SRC_REALPATH_OUTPUT" >&2
  fi
  echo "ERROR: Could not resolve real path for source: $SRC"
  echo "ERROR: Could not resolve real path for source: $SRC" >&2
  exit 1
fi
SRC_REALPATH="$SRC_REALPATH_OUTPUT"


# Diagnostic: print DST before realpath
echo "DEBUG: DST before realpath: '$DST'"

DST_REALPATH_OUTPUT=$(realpath "$DST" 2>&1)
DST_REALPATH_STATUS=$?
if [ $DST_REALPATH_STATUS -ne 0 ] || [ -z "$DST_REALPATH_OUTPUT" ]; then
  if [ -n "$DST_REALPATH_OUTPUT" ]; then
    echo "$DST_REALPATH_OUTPUT"
    echo "$DST_REALPATH_OUTPUT" >&2
  fi
  echo "ERROR: Could not resolve real path for destination: $DST"
  echo "ERROR: Could not resolve real path for destination: $DST" >&2
  exit 1
fi
DST_REALPATH="$DST_REALPATH_OUTPUT"

echo "Deployment source: $SRC_REALPATH"
echo "Deployment target: $DST_REALPATH"

summary=""




# --- IMPORTANT: Service vs Container Name ---
# - Use 'homeassistant' for all 'docker compose' commands (this is the service name in docker-compose.yml)
# - Use 'ha-dev' for all direct 'docker' commands (this is the container_name in docker-compose.yml)
echo "INFO: docker-compose service name is 'homeassistant', container name is 'ha-dev'"


step "1. Stopping Home Assistant container (service: homeassistant, container: ha-dev)"
cd "$DOCKER_DIR"
# Check if the container is running before trying to stop it
CONTAINER_STATUS=$(docker inspect --format '{{.State.Status}}' ha-dev 2>/dev/null)
if [ "$CONTAINER_STATUS" = "running" ]; then
  docker compose stop homeassistant && summary+="Stopped Home Assistant container (service: homeassistant, container: ha-dev).\n"

  # Wait for the container to be fully stopped (max 60s)
  step "1a. Waiting for ha-dev container to fully stop"
  WAIT_TIMEOUT=60
  WAIT_INTERVAL=2
  WAIT_ELAPSED=0
  while true; do
    STATUS=$(docker inspect --format '{{.State.Status}}' ha-dev 2>/dev/null)
    if [ "$STATUS" = "exited" ] || [ -z "$STATUS" ]; then
      echo "ha-dev container is fully stopped."
      summary+="ha-dev container fully stopped.\n"
      break
    fi
    if [ $WAIT_ELAPSED -ge $WAIT_TIMEOUT ]; then
      echo "ERROR: ha-dev container did not stop within $WAIT_TIMEOUT seconds." >&2
      echo "ERROR: ha-dev container did not stop within $WAIT_TIMEOUT seconds." >> "$HA_LOG" 2>/dev/null
      exit 1
    fi
    echo "Waiting for ha-dev container to stop... ($WAIT_ELAPSED/$WAIT_TIMEOUT s)"
    sleep $WAIT_INTERVAL
    WAIT_ELAPSED=$((WAIT_ELAPSED + WAIT_INTERVAL))
  done
else
  echo "ha-dev container is not running. Skipping stop."
  summary+="ha-dev container was not running. Skipped stop.\n"
fi


step "2. Deleting Home Assistant log file"
if [ -f "$HA_LOG" ]; then
  if rm -f "$HA_LOG"; then
    summary+="Deleted HA log file.\n"
  else
    echo "ERROR: Failed to delete HA log file: $HA_LOG" >&2
    ls -l "$HA_LOG" 2>&1
    summary+="ERROR: Failed to delete HA log file. See diagnostics above.\n"
  fi
else
  summary+="HA log file not found, skipping.\n"
fi


step "3. Ensuring deployment target directory exists"
if [ ! -d "$DST" ]; then
  echo "ERROR: Deployment target directory $DST does not exist. Aborting deployment." >&2
  exit 1
else
  summary+="Deployment target directory exists.\n"
fi




step "4. Deleting all files and directories in deployment target (with sudo)"
if sudo rm -rf "$DST"/* "$DST"/.[!.]* "$DST"/..?* 2>/dev/null; then
  summary+="Deleted all files and directories in deployment target (with sudo).\n"
else
  echo "WARNING: Some files or directories could not be deleted in $DST. Check permissions." >&2
  summary+="WARNING: Some files or directories could not be deleted in deployment target.\n"
fi



step "5. Deploying code via rsync"
# Trailing slash on SRC to copy contents, not the directory itself
rsync -av --exclude='__pycache__' --exclude='*.pyc' --delete "$SRC/" "$DST" && summary+="Deployed code to HA config.\n"





step "6. Starting Home Assistant container (service: homeassistant, container: ha-dev)"
# Use service name for docker compose
if docker compose start homeassistant; then
  # Wait for the container to be running (max 60s)
  START_TIMEOUT=60
  START_INTERVAL=2
  START_ELAPSED=0
  while true; do
    # Use container name for direct docker commands
    STATUS=$(docker inspect --format '{{.State.Status}}' ha-dev 2>/dev/null)
    if [ "$STATUS" = "running" ]; then
      echo "ha-dev container is running."
      summary+="Started ha-dev container.\n"
      break
    fi
    if [ $START_ELAPSED -ge $START_TIMEOUT ]; then
      echo "ERROR: ha-dev container did not start within $START_TIMEOUT seconds." >&2
      docker compose ps homeassistant
      summary+="ERROR: ha-dev container did not start. See diagnostics above.\n"
      exit 1
    fi
    echo "Waiting for ha-dev container to start... ($START_ELAPSED/$START_TIMEOUT s)"
    sleep $START_INTERVAL
    START_ELAPSED=$((START_ELAPSED + START_INTERVAL))
  done
else
  echo "ERROR: Failed to start ha-dev container." >&2
  docker compose ps homeassistant
  summary+="ERROR: Failed to start ha-dev container. See diagnostics above.\n"
  exit 1
fi





# Add a delay to allow Home Assistant to fully start up
DELAY_SECONDS=20
echo "Waiting $DELAY_SECONDS seconds for Home Assistant to fully start up..."
for ((i=1; i<=DELAY_SECONDS; i++)); do
  echo "  ... $i second(s) elapsed"
  sleep 1
done


step "7. Deployment Summary"
echo -e "\n========== DEPLOYMENT SUMMARY =========="
echo -e "$summary"
echo "Deployment complete. Home Assistant is restarting with the latest code."

# Show live Home Assistant log tail after deployment
echo -e "\n========== Tailing Home Assistant log (Ctrl+C to exit) =========="
tail -n 50 "$HA_LOG"
