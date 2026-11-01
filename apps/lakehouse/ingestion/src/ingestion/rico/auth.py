import msal
import boto3


def get_access_token(
    client_id: str,
    email_account: str,
    secret_id: str,
    cached_token: str,
) -> str:
    cache = msal.SerializableTokenCache()
    cache.deserialize(cached_token)

    app = msal.ConfidentialClientApplication(
        client_id,
        authority="https://login.microsoftonline.com/consumers",
        token_cache=cache,
    )

    accounts = app.get_accounts(email_account)

    result = app.acquire_token_silent(
        ["https://outlook.office.com/IMAP.AccessAsUser.All"], account=accounts[0]
    )

    _update_cached_token(secret_id, cache)

    return result["access_token"]


def _update_cached_token(secret_id: str, cache: msal.SerializableTokenCache) -> None:
    if cache.has_state_changed:
        boto3.client("secretsmanager").put_secret_value(
            SecretId=secret_id, SecretString=cache.serialize()
        )
