#!/bin/bash
# Demo helper: generates CPU load against the load balancer so the Auto Scaling Group scales out.
# Usage: ./load_test.sh http://<ALB-DNS-NAME> [parallel_workers] [seconds]
URL="${1:?Usage: $0 http://<alb-dns> [workers] [seconds]}"
WORKERS="${2:-10}"
DURATION="${3:-120}"
END=$((SECONDS + DURATION))

worker() {
  while [ $SECONDS -lt $END ]; do
    curl -s -o /dev/null "$URL/cpu"
  done
}

echo "Sending load to $URL with $WORKERS workers for ${DURATION}s ..."
for _ in $(seq "$WORKERS"); do worker & done
wait
echo "Done."
