#!/bin/bash
# Deploy QA Gate and Checkpoint Lambda code directly

set -e

echo "=== Packaging QA Gate + Checkpoint ==="
rm -rf /tmp/qa_pkg /tmp/qa_pkg.zip /tmp/cp_pkg /tmp/cp_pkg.zip

# QA Gate
mkdir -p /tmp/qa_pkg
cp -r src/qa_checkpoint/* /tmp/qa_pkg/
cp -r src/infrastructure /tmp/qa_pkg/src_infrastructure_tmp
mkdir -p /tmp/qa_pkg/src/infrastructure
cp -r src/infrastructure/observability /tmp/qa_pkg/src/infrastructure/
cp -r src/infrastructure/state /tmp/qa_pkg/src/infrastructure/
cp -r src/infrastructure/schema /tmp/qa_pkg/src/infrastructure/
touch /tmp/qa_pkg/src/__init__.py
touch /tmp/qa_pkg/src/infrastructure/__init__.py
cd /tmp/qa_pkg
zip -r /tmp/qa_pkg.zip . -x "*.pyc" "__pycache__/*" "src_infrastructure_tmp/*"
cd -
rm -rf /tmp/qa_pkg/src_infrastructure_tmp

echo "Deploying QA Gate..."
aws lambda update-function-code \
  --function-name academic-pipeline-qa-gate-dev \
  --zip-file fileb:///tmp/qa_pkg.zip \
  --region us-east-1 \
  --output text \
  --query "FunctionName" 2>&1
echo "QA Gate deployed"

# Checkpoint
mkdir -p /tmp/cp_pkg
cp -r src/qa_checkpoint/* /tmp/cp_pkg/
mkdir -p /tmp/cp_pkg/src/infrastructure
cp -r src/infrastructure/observability /tmp/cp_pkg/src/infrastructure/
cp -r src/infrastructure/state /tmp/cp_pkg/src/infrastructure/
cp -r src/infrastructure/schema /tmp/cp_pkg/src/infrastructure/
touch /tmp/cp_pkg/src/__init__.py
touch /tmp/cp_pkg/src/infrastructure/__init__.py
cd /tmp/cp_pkg
zip -r /tmp/cp_pkg.zip . -x "*.pyc" "__pycache__/*"
cd -

echo "Deploying Checkpoint..."
aws lambda update-function-code \
  --function-name academic-pipeline-checkpoint-dev \
  --zip-file fileb:///tmp/cp_pkg.zip \
  --region us-east-1 \
  --output text \
  --query "FunctionName" 2>&1
echo "Checkpoint deployed"

echo "=== Done ==="
