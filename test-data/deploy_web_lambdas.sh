#!/bin/bash
# Deploy web interface Lambda code (upload, ingestion, dashboard)
set -e

echo "=== Packaging web interface Lambdas ==="
rm -rf /tmp/web_pkg /tmp/web_pkg.zip

mkdir -p /tmp/web_pkg
cp src/web_interface/backend/*.py /tmp/web_pkg/
mkdir -p /tmp/web_pkg/src/infrastructure
cp -r src/infrastructure/observability /tmp/web_pkg/src/infrastructure/
cp -r src/infrastructure/state /tmp/web_pkg/src/infrastructure/
cp -r src/infrastructure/schema /tmp/web_pkg/src/infrastructure/
touch /tmp/web_pkg/src/__init__.py
touch /tmp/web_pkg/src/infrastructure/__init__.py
cd /tmp/web_pkg
zip -r /tmp/web_pkg.zip . -x "*.pyc" "__pycache__/*"
cd -

for FN in academic-pipeline-ingestion-dev academic-pipeline-dashboard-dev academic-pipeline-upload-dev; do
  echo "Deploying $FN..."
  aws lambda update-function-code --function-name "$FN" --zip-file fileb:///tmp/web_pkg.zip --region us-east-1 --output text --query "FunctionName" 2>&1
done

echo "=== Done ==="
