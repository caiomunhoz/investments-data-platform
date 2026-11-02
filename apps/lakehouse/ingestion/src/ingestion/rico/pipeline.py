import dlt
from dlt.sources.rest_api import RESTAPIConfig, rest_api_resources

from .auth import get_access_token
from .pdf_parser import parse_note


@dlt.source(name="outlook_inbox")
def outlook_inbox_source(
    client_id: str = dlt.secrets.value,
    email_account: str = dlt.secrets.value,
    secret_id: str = dlt.config.value,
    pdf_password: str = dlt.secrets.value,
):
    config: RESTAPIConfig = {
        "client": {
            "base_url": "https://graph.microsoft.com/v1.0/me",
            "auth": {
                "type": "bearer",
                "token": get_access_token(client_id, email_account, secret_id),
            },
        },
        "resource_defaults": {
            "primary_key": "id",
        },
        "resources": [
            {
                "name": "messages",
                "selected": False,
                "endpoint": {
                    "path": "mailFolders/inbox/messages",
                    "params": {
                        "$top": 50,
                        "$select": "id,receivedDateTime",
                        "$filter": (
                            "from/emailAddress/address eq 'noreply@rico.com.vc' "
                            "and subject eq 'Rico | Nota de Negociação' "
                            "and hasAttachments eq true "
                            "and receivedDateTime gt {incremental.start_value}"
                        ),
                    },
                    "incremental": {
                        "cursor_path": "receivedDateTime",
                        "initial_value": "1970-01-01T00:00:00Z",
                    },
                    "paginator": {
                        "type": "json_link",
                        "next_url_path": "['@odata.nextLink']",
                    },
                },
            },
            {
                "name": "negotiation_notes",
                "parallelized": True,
                "endpoint": {
                    "path": "messages/{resources.messages.id}/attachments",
                    "params": {
                        "$filter": (
                            "isInline eq false "
                            "and contentType eq 'application/pdf' "
                            "and startsWith(name, 'NotaNegociacao')"
                        ),
                    },
                    "paginator": "single_page",
                },
                "processing_steps": [
                    {"map": lambda record: parse_note(record, pdf_password)},
                ],
            },
        ],
    }

    yield from rest_api_resources(config)


def run_pipeline():
    pipeline = dlt.pipeline(
        pipeline_name="rico_pipeline",
        destination="filesystem",
        dataset_name="rico",
    )

    pipeline.run(outlook_inbox_source())
