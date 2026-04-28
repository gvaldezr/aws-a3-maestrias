#!/bin/bash
# Activate Canvas Publisher in real mode
set -e

echo "Switching Canvas Publisher to REAL mode..."
aws lambda update-function-configuration \
  --function-name academic-pipeline-canvas-publisher-dev \
  --environment "Variables={CANVAS_MOCK_MODE=false,CANVAS_BASE_URL=https://anahuacmerida.instructure.com,CANVAS_SECRET_ARN=arn:aws:secretsmanager:us-east-1:254508868459:secret:academic-pipeline/dev/canvas-oauth-token-YrcByg,SUBJECTS_BUCKET_NAME=academic-pipeline-subjects-254508868459-us-east-1-dev,SUBJECTS_TABLE_NAME=academic-pipeline-subjects-dev}" \
  --region us-east-1 \
  --output text \
  --query "FunctionName" 2>&1

echo "Done. Canvas Publisher is now in REAL mode."
echo "Canvas URL: https://anahuacmerida.instructure.com"
