"""End-to-end test: Upload document and trigger pipeline."""
import boto3
import json
import requests

TEST_CONTENT = (
    "Maestria en Innovacion y Gestion Tecnologica\n"
    "Universidad Anahuac Merida\n\n"
    "Perfil de Egreso:\n"
    "El egresado sera capaz de liderar proyectos de innovacion tecnologica en organizaciones, "
    "aplicando metodologias agiles y herramientas de inteligencia artificial para la toma de "
    "decisiones estrategicas.\n\n"
    "Asignatura: Inteligencia Artificial Aplicada a los Negocios\n"
    "Tipo: Concentracion\n\n"
    "Competencias:\n"
    "C1: Analizar el impacto de la inteligencia artificial en la estrategia empresarial\n"
    "C2: Disenar soluciones basadas en IA para problemas de negocio complejos\n"
    "C3: Evaluar la viabilidad tecnica y financiera de proyectos de transformacion digital\n\n"
    "Resultados de Aprendizaje:\n"
    "RA1: Analizar los fundamentos de machine learning y su aplicacion en contextos empresariales\n"
    "RA2: Evaluar herramientas de IA generativa para la automatizacion de procesos de negocio\n"
    "RA3: Disenar una estrategia de adopcion de IA para una organizacion real\n\n"
    "Temario:\n"
    "Semana 1: Fundamentos de IA y Machine Learning\n"
    "Semana 2: IA Generativa y Modelos de Lenguaje\n"
    "Semana 3: Casos de Uso Empresarial de IA\n"
    "Semana 4: Estrategia de Adopcion y Transformacion Digital\n"
)

def main():
    # Auth
    cognito = boto3.client("cognito-idp", region_name="us-east-1")
    auth = cognito.initiate_auth(
        ClientId="v8mnl80kg82gr2ejrvakdq6ju",
        AuthFlow="USER_PASSWORD_AUTH",
        AuthParameters={"USERNAME": "staff-admin", "PASSWORD": "Pipeline2026Edu!"},
    )
    token = auth["AuthenticationResult"]["IdToken"]
    headers = {"Authorization": token, "Content-Type": "application/json"}
    web_api = "https://z1px5977b8.execute-api.us-east-1.amazonaws.com/prod"

    # Step 1: Request upload URL
    print("=== Step 1: Request Upload URL ===")
    r = requests.post(
        f"{web_api}/api/upload",
        headers=headers,
        json={"file_name": "ia_negocios.pdf", "file_size_bytes": len(TEST_CONTENT), "content_type": "application/pdf"},
    )
    print(f"Status: {r.status_code}")
    data = r.json()
    subject_id = data.get("subject_id", "")
    upload_url = data.get("upload_url", "")
    print(f"Subject ID: {subject_id}")

    # Step 2: Upload to S3
    print("\n=== Step 2: Upload to S3 ===")
    r2 = requests.put(upload_url, data=TEST_CONTENT.encode("utf-8"), headers={"Content-Type": "application/pdf"})
    print(f"S3 Status: {r2.status_code}")

    # Step 3: Verify in S3
    print("\n=== Step 3: Verify S3 Object ===")
    s3 = boto3.client("s3", region_name="us-east-1")
    bucket = "academic-pipeline-subjects-254508868459-us-east-1-dev"
    key = f"uploads/{subject_id}/ia_negocios.pdf"
    try:
        obj = s3.head_object(Bucket=bucket, Key=key)
        print(f"Object: {key} ({obj['ContentLength']} bytes)")
    except Exception as e:
        print(f"Not found: {e}")

    # Step 4: Check ingestion Lambda logs
    print("\n=== Step 4: Check Ingestion Lambda ===")
    print(f"Subject ID: {subject_id}")
    print("The S3 event should trigger the ingestion Lambda automatically.")
    print("Check logs: aws logs tail /aws/lambda/academic-pipeline-ingestion-dev --since 2m")

    # Step 5: Check if JSON was created in S3
    print("\n=== Step 5: Check for Subject JSON ===")
    json_key = f"subjects/{subject_id}/subject.json"
    try:
        obj = s3.get_object(Bucket=bucket, Key=json_key)
        subject_json = json.loads(obj["Body"].read())
        print(f"Subject JSON found!")
        print(f"  State: {subject_json.get('pipeline_state', {}).get('current_state', 'N/A')}")
        print(f"  Subject: {subject_json.get('metadata', {}).get('subject_name', 'N/A')}")
        print(f"  Program: {subject_json.get('metadata', {}).get('program_name', 'N/A')}")
        print(f"  Type: {subject_json.get('metadata', {}).get('program_type', 'N/A')}")
    except s3.exceptions.NoSuchKey:
        print("Subject JSON not yet created (ingestion Lambda may still be processing)")
    except Exception as e:
        print(f"Error: {e}")

    # Step 6: Check DynamoDB
    print("\n=== Step 6: Check DynamoDB ===")
    ddb = boto3.client("dynamodb", region_name="us-east-1")
    try:
        resp = ddb.get_item(
            TableName="academic-pipeline-subjects-dev",
            Key={"subject_id": {"S": subject_id}, "SK": {"S": "STATE"}},
        )
        item = resp.get("Item")
        if item:
            print(f"DynamoDB record found!")
            print(f"  State: {item.get('current_state', {}).get('S', 'N/A')}")
            print(f"  Subject: {item.get('subject_name', {}).get('S', 'N/A')}")
        else:
            print("No DynamoDB record yet")
    except Exception as e:
        print(f"Error: {e}")


if __name__ == "__main__":
    main()
