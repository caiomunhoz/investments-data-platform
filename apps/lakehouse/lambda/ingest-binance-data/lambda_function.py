from ingestion.binance.pipeline import run_pipeline


def lambda_handler(event, context):
    run_pipeline(
        symbols=[
            "BTCBRL",
            "ETHBRL",
            "SOLBRL",
        ]
    )
