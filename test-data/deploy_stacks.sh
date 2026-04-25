#!/bin/bash
# Deploy CDK stacks with correct python path
set -e

# Temporarily set the python path in cdk.json
python3 -c "
import json
with open('cdk.json') as f: cfg = json.load(f)
cfg['app'] = '/Library/Frameworks/Python.framework/Versions/3.11/bin/python3 app.py'
with open('cdk.json', 'w') as f: json.dump(cfg, f, indent=2)
"

echo "Deploying QA Checkpoint stack..."
npx cdk deploy AcademicPipeline-QACheckpoint-dev --require-approval never 2>&1 | tail -5

echo "Deploying Web Interface stack..."
npx cdk deploy AcademicPipeline-WebInterface-Dev --require-approval never 2>&1 | tail -5

# Restore cdk.json
python3 -c "
import json
with open('cdk.json') as f: cfg = json.load(f)
cfg['app'] = 'python3 app.py'
with open('cdk.json', 'w') as f: json.dump(cfg, f, indent=2)
"

echo "Done"
