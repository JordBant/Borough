terraform {
  required_version = ">= 1.5"

  required_providers {
    aws = {
      source  = "hashicorp/aws"
      version = "~> 5.0"
    }
  }
}

provider "aws" {
  region = var.aws_region
}

resource "aws_s3_bucket" "bronze_layer" {
  bucket = "${var.bronze_bucket_name}-${var.environment}"

  tags = {
    Project     = "borough"
    Environment = var.environment
    Layer       = "bronze"
  }
}

resource "aws_s3_bucket_versioning" "bronze_layer_versioning" {
  bucket = aws_s3_bucket.bronze_layer.id

  versioning_configuration {
    status = "Enabled"
  }
}

resource "aws_s3_bucket_public_access_block" "bronze_layer_private" {
  bucket = aws_s3_bucket.bronze_layer.id

  block_public_acls       = true
  block_public_policy     = true
  ignore_public_acls      = true
  restrict_public_buckets = true
}

resource "aws_s3_bucket_policy" "bronze_layer_policy" {
  bucket = aws_s3_bucket.bronze_layer.id

  policy = jsonencode({
    Version = "2012-10-17"
    Statement = [
      {
        Sid       = "DenyInsecureTransport"
        Effect    = "Deny"
        Principal = "*"
        Action    = "s3:*"
        Resource = [
          aws_s3_bucket.bronze_layer.arn,
          "${aws_s3_bucket.bronze_layer.arn}/*",
        ]
        Condition = {
          Bool = {
            "aws:SecureTransport" = "false"
          }
        }
      }
    ]
  })
}
