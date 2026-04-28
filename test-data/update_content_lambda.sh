#!/bin/bash
# Update Content step Lambda with S3 bucket env var and new code
set -e

# Add SUBJECTS_BUCKET_NAME to env vars
aws lambda update-function-configuration \
  --function-name academic-pipeline-orch-contentstep-dev \
  --environment "Variables={CANVAS_PUBLISHER_FUNCTION_NAME=academic-pipeline-canvas-publisher-dev,CONTENT_RUNTIME_ARN=arn:aws:bedrock-agentcore:us-east-1:254508868459:runtime/AcademicPipelineContentDev-fX2AEsCaMw,STAFF_NOTIFICATIONS_TOPIC_ARN=arn:aws:sns:us-east-1:254508868459:academic-pipeline-staff-dev,DI_RUNTIME_ARN=arn:aws:bedrock-agentcore:us-east-1:254508868459:runtime/AcademicPipelineDIDev-Rp1Oj57gGL,QA_GATE_FUNCTION_NAME=academic-pipeline-qa-gate-dev,SCHOLAR_RUNTIME_ARN=arn:aws:bedrock-agentcore:us-east-1:254508868459:runtime/AcademicPipelineScholarDev-7S4W3RBBi0,SUBJECTS_BUCKET_NAME=academic-pipeline-subjects-254508868459-us-east-1-dev}" \
  --region us-east-1 \
  --output text \
  --query "FunctionName" 2>&1

echo "Env vars updated"

# Update code
sleep 10
rm -rf /tmp/orch_pkg /tmp/orch_pkg.zip
mkdir -p /tmp/orch_pkg
cp src/orchestrator/*.py /tmp/orch_pkg/
mkdir -p /tmp/orch_pkg/src/infrastructure
cp -r src/infrastructure/observability /tmp/orch_pkg/src/infrastructure/
cp -r src/infrastructure/state /tmp/orch_pkg/src/infrastructure/
cp -r src/infrastructure/schema /tmp/orch_pkg/src/infrastructure/
touch /tmp/orch_pkg/src/__init__.py /tmp/orch_pkg/src/infrastructure/__init__.py
cd /tmp/orch_pkg
zip -r /tmp/orch_pkg.zip . -x "*.pyc" "__pycache__/*"
cd -

# Update all orchestrator Lambdas with the new code
for FN in academic-pipeline-orch-contentstep-dev academic-pipeline-orch-scholarstep-dev academic-pipeline-orch-distep-dev academic-pipeline-orch-persistscholarf-dev academic-pipeline-orch-persistdifn-dev academic-pipeline-orch-persistcontentf-dev academic-pipeline-orch-qastep-dev academic-pipeline-orch-warmupstep-dev; do
  echo "Updating $FN..."
  aws lambda update-function-code --function-name "$FN" --zip-file fileb:///tmp/orch_pkg.zip --region us-east-1 --output text --query "FunctionName" 2>&1 || echo "  (skipped)"
done

echo "Done"
