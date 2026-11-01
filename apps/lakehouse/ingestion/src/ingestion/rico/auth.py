import msal
import boto3


def get_access_token(client_id: str, email_account: str, secret_id: str) -> str:
    secrets_client = boto3.client("secretsmanager")
    cache = msal.SerializableTokenCache()
    cache.deserialize(
        secrets_client.get_secret_value(SecretId=secret_id)["SecretString"]
    )

    app = msal.ConfidentialClientApplication(
        client_id,
        authority="https://login.microsoftonline.com/consumers",
        token_cache=cache,
    )

    accounts = app.get_accounts(email_account)

    result = app.acquire_token_silent(
        ["https://outlook.office.com/IMAP.AccessAsUser.All"], account=accounts[0]
    )

    if cache.has_state_changed:
        secrets_client.put_secret_value(
            SecretId=secret_id, SecretString=cache.serialize()
        )

    return result["access_token"]
