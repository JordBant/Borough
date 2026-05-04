output "bronze_bucket_arn" {
  description = "ARN of the bronze-layer S3 bucket"
  value       = aws_s3_bucket.bronze_layer.arn
}

output "bronze_bucket_name" {
  description = "Name of the bronze-layer S3 bucket"
  value       = aws_s3_bucket.bronze_layer.id
}
