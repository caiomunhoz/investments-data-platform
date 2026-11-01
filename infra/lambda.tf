locals {
  lambda_functions = {
    "ingest-binance-trades" = {
      timeout     = 60
      memory_size = 128
      environment = {}
    }
    "ingest-negotiation-notes" = {
      timeout     = 60
      memory_size = 256
      environment = {
        SOURCES__OUTLOOK_INBOX__SECRET_ID = data.aws_secretsmanager_secret.outlook_cached_token.arn
      }
    }
  }
}

data "aws_secretsmanager_secret" "outlook_cached_token" {
  name = "dlt/sources/outlook_inbox/cached_token"
}

data "aws_iam_policy_document" "lambda_assume_role" {
  statement {
    effect = "Allow"

    principals {
      type        = "Service"
      identifiers = ["lambda.amazonaws.com"]
    }

    actions = ["sts:AssumeRole"]
  }
}

data "aws_iam_policy_document" "lambda_ingestion_policy" {
  statement {
    effect = "Allow"
    actions = [
      "s3:PutObject",
      "s3:GetObject",
      "s3:DeleteObject",
      "s3:GetObjectAttributes",
      "s3:ListBucket"
    ]
    resources = [
      aws_s3_bucket.data_lakehouse_bucket.arn,
      "${aws_s3_bucket.data_lakehouse_bucket.arn}/*"
    ]
  }

  statement {
    effect    = "Allow"
    actions   = ["ecr:BatchGetImage", "ecr:GetDownloadUrlForLayer"]
    resources = values(aws_ecr_repository.lambda)[*].arn
  }

  statement {
    effect    = "Allow"
    actions   = ["logs:CreateLogGroup", "logs:CreateLogStream", "logs:PutLogEvents"]
    resources = ["arn:aws:logs:*:*:*"]
  }

  statement {
    effect    = "Allow"
    actions   = ["secretsmanager:GetSecretValue"]
    resources = ["arn:aws:secretsmanager:*:*:secret:dlt/*"]
  }

  statement {
    effect    = "Allow"
    actions   = ["secretsmanager:ListSecrets"]
    resources = ["*"]
  }

  statement {
    effect    = "Allow"
    actions   = ["secretsmanager:PutSecretValue"]
    resources = [data.aws_secretsmanager_secret.outlook_cached_token.arn]
  }
}

resource "aws_iam_role" "lambda_ingestion_role" {
  name               = "investmentsDataPlatformLambdaIngestionRole"
  assume_role_policy = data.aws_iam_policy_document.lambda_assume_role.json
}

resource "aws_iam_role_policy" "lambda_ingestion_role_policy" {
  name   = "investmentsDataPlatformLambdaIngestionPolicy"
  role   = aws_iam_role.lambda_ingestion_role.id
  policy = data.aws_iam_policy_document.lambda_ingestion_policy.json
}

resource "aws_lambda_function" "lambda" {
  for_each = local.lambda_functions

  function_name = "investments-data-platform-${each.key}"
  package_type  = "Image"
  timeout       = each.value.timeout
  memory_size   = each.value.memory_size
  image_uri     = "${aws_ecr_repository.lambda[each.key].repository_url}@${data.aws_ecr_image.lambda[each.key].image_digest}"
  role          = aws_iam_role.lambda_ingestion_role.arn
  publish       = true

  dynamic "environment" {
    for_each = length(each.value.environment) > 0 ? [each.value.environment] : []

    content {
      variables = environment.value
    }
  }
}
