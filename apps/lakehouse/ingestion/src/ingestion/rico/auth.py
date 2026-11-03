import boto3
import msal


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

    result = app.acquire_token_silent_with_error(
        ["https://graph.microsoft.com/Mail.Read"], account=accounts[0]
    )

    if cache.has_state_changed:
        secrets_client.put_secret_value(
            SecretId=secret_id, SecretString=cache.serialize()
        )

    if not result or "access_token" not in result:
        raise RuntimeError(
            f"Failed to acquire Graph token: {(result or {}).get('error_description', 'no cached account token')}"
        )

    return result["access_token"]
