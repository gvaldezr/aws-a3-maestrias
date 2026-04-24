"""CDK Stack — Pipeline Orchestrator (Step Functions)."""
from __future__ import annotations

import aws_cdk as cdk
from aws_cdk import (
    aws_iam as iam,
    aws_lambda as lambda_,
    aws_stepfunctions as sfn,
    aws_stepfunctions_tasks as tasks,
)
from constructs import Construct


class OrchestratorStack(cdk.Stack):
    def __init__(self, scope: Construct, construct_id: str, env_name: str,
                 scholar_arn: str, di_arn: str, content_arn: str,
                 qa_function_name: str, canvas_function_name: str,
                 staff_topic_arn: str, **kwargs) -> None:
        super().__init__(scope, construct_id, **kwargs)

        cdk.Tags.of(self).add("Project", "academic-pipeline")
        cdk.Tags.of(self).add("Unit", "orchestrator")
        cdk.Tags.of(self).add("Environment", env_name)

        # Shared layer
        shared_layer = lambda_.LayerVersion(self, "SharedLayer",
            code=lambda_.Code.from_asset("lambda-layer"),
            compatible_runtimes=[lambda_.Runtime.PYTHON_3_11],
        )

        lambda_env = {
            "SCHOLAR_RUNTIME_ARN": scholar_arn,
            "DI_RUNTIME_ARN": di_arn,
            "CONTENT_RUNTIME_ARN": content_arn,
            "QA_GATE_FUNCTION_NAME": qa_function_name,
            "CANVAS_PUBLISHER_FUNCTION_NAME": canvas_function_name,
            "STAFF_NOTIFICATIONS_TOPIC_ARN": staff_topic_arn,
        }

        # Lambda for each orchestration step
        scholar_lambda = self._create_lambda("ScholarStep", "invoke_agent.invoke_scholar", lambda_env, shared_layer, env_name, timeout=600)
        di_lambda = self._create_lambda("DIStep", "invoke_agent.invoke_di", lambda_env, shared_layer, env_name, timeout=480)
        content_lambda = self._create_lambda("ContentStep", "invoke_agent.invoke_content", lambda_env, shared_layer, env_name, timeout=600)
        qa_lambda = self._create_lambda("QAStep", "invoke_agent.invoke_qa_gate", lambda_env, shared_layer, env_name, timeout=60)
        canvas_lambda = self._create_lambda("CanvasStep", "invoke_agent.invoke_canvas_publisher", lambda_env, shared_layer, env_name, timeout=300)

        # Grant AgentCore invoke permissions
        for fn in [scholar_lambda, di_lambda, content_lambda]:
            fn.add_to_role_policy(iam.PolicyStatement(
                actions=["bedrock-agentcore:InvokeAgentRuntime"],
                resources=["*"],
            ))

        # Grant Lambda invoke for QA and Canvas
        for fn in [qa_lambda, canvas_lambda]:
            fn.add_to_role_policy(iam.PolicyStatement(
                actions=["lambda:InvokeFunction"],
                resources=[
                    f"arn:aws:lambda:us-east-1:{self.account}:function:{qa_function_name}",
                    f"arn:aws:lambda:us-east-1:{self.account}:function:{canvas_function_name}",
                ],
            ))

        # Step Functions tasks
        step_scholar = tasks.LambdaInvoke(self, "InvokeScholar",
            lambda_function=scholar_lambda,
            payload_response_only=True,
            result_path="$.scholar",
        )

        step_di = tasks.LambdaInvoke(self, "InvokeDI",
            lambda_function=di_lambda,
            payload_response_only=True,
            result_path="$.di",
        )

        step_content = tasks.LambdaInvoke(self, "InvokeContent",
            lambda_function=content_lambda,
            payload_response_only=True,
            result_path="$.content",
        )

        step_qa = tasks.LambdaInvoke(self, "InvokeQAGate",
            lambda_function=qa_lambda,
            payload_response_only=True,
            result_path="$.qa",
        )

        # Wait for human approval (callback pattern)
        wait_for_approval = sfn.Wait(self, "WaitForHumanApproval",
            time=sfn.WaitTime.duration(cdk.Duration.seconds(1)),
        )

        # Check approval status
        check_approval = sfn.Choice(self, "CheckApprovalStatus")

        step_canvas = tasks.LambdaInvoke(self, "InvokeCanvasPublisher",
            lambda_function=canvas_lambda,
            output_path="$.Payload",
            result_path="$.canvas",
        )

        # Success and failure states
        pipeline_complete = sfn.Succeed(self, "PipelineComplete",
            comment="Course published to Canvas LMS",
        )

        qa_failed = sfn.Fail(self, "QAFailed",
            cause="QA Gate validation failed after retries",
            error="QA_FAILED",
        )

        pending_approval = sfn.Pass(self, "PendingHumanApproval",
            comment="Waiting for Staff approval via Checkpoint API",
        )

        # Chain: Scholar → DI → Content → QA → (branch)
        # QA passes → Pending Approval (human reviews via API)
        # QA fails → Fail state
        definition = (
            step_scholar
            .next(step_di)
            .next(step_content)
            .next(step_qa)
            .next(
                check_approval
                .when(sfn.Condition.string_equals("$.qa.qa_status", "PENDING_APPROVAL"), pending_approval)
                .when(sfn.Condition.string_equals("$.qa.qa_status", "QA_FAILED"), qa_failed)
                .otherwise(pending_approval)
            )
        )

        # State Machine
        self.state_machine = sfn.StateMachine(self, "PipelineStateMachine",
            state_machine_name=f"academic-pipeline-orchestrator-{env_name}",
            definition_body=sfn.DefinitionBody.from_chainable(definition),
            timeout=cdk.Duration.hours(2),
            tracing_enabled=True,
        )

        # Output
        cdk.CfnOutput(self, "StateMachineArn", value=self.state_machine.state_machine_arn)
        cdk.CfnOutput(self, "StateMachineName", value=self.state_machine.state_machine_name)

    def _create_lambda(self, name: str, handler: str, env: dict,
                       layer: lambda_.LayerVersion, env_name: str,
                       timeout: int = 300) -> lambda_.Function:
        return lambda_.Function(self, name,
            function_name=f"academic-pipeline-orch-{name.lower()}-{env_name}",
            runtime=lambda_.Runtime.PYTHON_3_11,
            handler=handler,
            code=lambda_.Code.from_asset("src/orchestrator"),
            timeout=cdk.Duration.seconds(timeout),
            memory_size=512,
            environment=env,
            layers=[layer],
        )
