resource "aws_ecr_repository" "lambda" {
  for_each = local.lambda_functions

  name                 = "investments-data-platform/lambda-${each.key}"
  image_tag_mutability = "IMMUTABLE_WITH_EXCLUSION"

  image_tag_mutability_exclusion_filter {
    filter_type = "WILDCARD"
    filter      = "latest"
  }

  image_scanning_configuration {
    scan_on_push = true
  }
}

data "aws_ecr_image" "lambda" {
  for_each = aws_ecr_repository.lambda

  repository_name = each.value.name
  most_recent     = true
}
