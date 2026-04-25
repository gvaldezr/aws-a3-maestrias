#!/bin/bash
# Add permissions to QA Gate and Checkpoint Lambda roles

POLICY_FILE="test-data/pipeline-data-access-policy.json"

# QA Gate role
QA_ROLE=$(aws lambda get-function --function-name academic-pipeline-qa-gate-dev --region us-east-1 --query "Configuration.Role" --output text | sed 's|.*/||')
echo "QA Gate Role: $QA_ROLE"
aws iam put-role-policy --role-name "$QA_ROLE" --policy-name "PipelineDataAccess" --policy-document "file://$POLICY_FILE"
echo "QA Gate permissions added"

# Checkpoint role
CHECKPOINT_ROLE=$(aws lambda get-function --function-name academic-pipeline-checkpoint-dev --region us-east-1 --query "Configuration.Role" --output text 2>/dev/null | sed 's|.*/||')
if [ -n "$CHECKPOINT_ROLE" ]; then
  echo "Checkpoint Role: $CHECKPOINT_ROLE"
  aws iam put-role-policy --role-name "$CHECKPOINT_ROLE" --policy-name "PipelineDataAccess" --policy-document "file://$POLICY_FILE"
  echo "Checkpoint permissions added"
else
  echo "Checkpoint Lambda not found, skipping"
fi

echo "Done"
