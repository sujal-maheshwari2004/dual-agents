#!/bin/sh
sed -i "s|PROMETHEUS_URL_PLACEHOLDER|${PROMETHEUS_URL}|g" /etc/grafana/provisioning/datasources/prometheus.yaml
exec /run.sh