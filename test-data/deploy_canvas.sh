#!/bin/bash
set -e
echo "=== Packaging Canvas Publisher ==="
rm -rf /tmp/canvas_pkg /tmp/canvas_pkg.zip
mkdir -p /tmp/canvas_pkg
cp -r src/canvas_publisher/*.py /tmp/canvas_pkg/
mkdir -p /tmp/canvas_pkg/src/infrastructure
cp -r src/infrastructure/observability /tmp/canvas_pkg/src/infrastructure/
cp -r src/infrastructure/state /tmp/canvas_pkg/src/infrastructure/
cp -r src/infrastructure/schema /tmp/canvas_pkg/src/infrastructure/
touch /tmp/canvas_pkg/src/__init__.py
touch /tmp/canvas_pkg/src/infrastructure/__init__.py
cd /tmp/canvas_pkg
zip -r /tmp/canvas_pkg.zip . -x "*.pyc" "__pycache__/*"
cd -
echo "Deploying..."
aws lambda update-function-code --function-name academic-pipeline-canvas-publisher-dev --zip-file fileb:///tmp/canvas_pkg.zip --region us-east-1 --output text --query "FunctionName" 2>&1
echo "Setting CANVAS_MOCK_MODE=true..."
aws lambda update-function-configuration --function-name academic-pipeline-canvas-publisher-dev --environment "Variables={CANVAS_MOCK_MODE=true,CANVAS_BASE_URL=https://anahuacmerida.instructure.com,SUBJECTS_BUCKET_NAME=academic-pipeline-subjects-254508868459-us-east-1-dev,SUBJECTS_TABLE_NAME=academic-pipeline-subjects-dev}" --region us-east-1 --output text --query "FunctionName" 2>&1
echo "=== Done ==="
