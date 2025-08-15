#!/bin/sh
source ./.deploy_config.sh

echo "Syncing project to $REMOTE_USER@$REMOTE_HOST:$REMOTE_PATH..."
echo " Warning: all remote files that not exist locally will be removed on server!"
rsync -avz --delete --filter='dir-merge /.rsync-filter' -e "ssh -p $REMOTE_PORT" ./ "$REMOTE_USER@$REMOTE_HOST:$REMOTE_PATH"

echo "Sync complete."
