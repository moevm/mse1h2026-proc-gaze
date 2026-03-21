#!/bin/bash

failed=0

while IFS= read -r status; do
  if [[ $status != Up* ]]; then
    echo -e "Container not running:\n  $status"
    failed=1
  fi
done < <(docker compose ps -a --format "{{.Status}}: {{.Name}}")

if [[ $failed == 1 ]]; then
  echo "Containers:"
  docker ps -a
  echo "Logs:"
  docker compose logs
fi