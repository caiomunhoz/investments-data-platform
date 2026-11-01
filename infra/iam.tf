data "aws_iam_policy_document" "gh_actions_oidc_assume_role_policy" {
  statement {
    actions = ["sts:AssumeRoleWithWebIdentity"]

    principals {
      type        = "Federated"
      identifiers = [aws_iam_openid_connect_provider.github_openid_provider.arn]
    }

    condition {
      test     = "StringEquals"
      variable = "token.actions.githubusercontent.com:aud"
      values   = ["sts.amazonaws.com"]
    }

    condition {
      test     = "StringLike"
      variable = "token.actions.githubusercontent.com:sub"
      values = [
        "repo:caiomunhoz*/investments-data-platform*:ref:refs/heads/main",
        "repo:caiomunhoz*/investments-data-platform*:environment:terraform-apply"
      ]
    }
  }
}

data "aws_iam_policy_document" "ecr_push_policy" {
  statement {
    effect = "Allow"
    actions = [
      "ecr:BatchCheckLayerAvailability",
      "ecr:BatchGetImage",
      "ecr:GetDownloadUrlForLayer",
      "ecr:PutImage",
      "ecr:InitiateLayerUpload",
      "ecr:UploadLayerPart",
      "ecr:CompleteLayerUpload"
    ]
    resources = values(aws_ecr_repository.lambda)[*].arn
  }

  statement {
    effect    = "Allow"
    actions   = ["ecr:GetAuthorizationToken"]
    resources = ["*"]
  }
}

data "aws_iam_policy_document" "terraform_ci_policy" { # TODO: Restrict actions and resources for Terraform CI role
  statement {
    effect    = "Allow"
    actions   = ["*"]
    resources = ["*"]
  }
}

resource "aws_iam_openid_connect_provider" "github_openid_provider" {
  url            = "https://token.actions.githubusercontent.com"
  client_id_list = ["sts.amazonaws.com"]
}

resource "aws_iam_role" "ecr_push_role" {
  name               = "InvestmentsDataPlatformECRPushRole"
  assume_role_policy = data.aws_iam_policy_document.gh_actions_oidc_assume_role_policy.json
}

resource "aws_iam_role_policy" "ecr_push_role_policy" {
  name   = "InvestmentsDataPlatformECRPushPolicy"
  role   = aws_iam_role.ecr_push_role.id
  policy = data.aws_iam_policy_document.ecr_push_policy.json
}

resource "aws_iam_role" "terraform_ci" {
  name               = "InvestmentsDataPlatformTerraformCIRole"
  assume_role_policy = data.aws_iam_policy_document.gh_actions_oidc_assume_role_policy.json
}

resource "aws_iam_role_policy" "terraform_ci_role_policy" {
  name   = "InvestmentsDataPlatformTerraformCIPolicy"
  role   = aws_iam_role.terraform_ci.id
  policy = data.aws_iam_policy_document.terraform_ci_policy.json
}