from ingestion.rico.pipeline import run_pipeline


def lambda_handler(event, context):
    run_pipeline()
