output "eks_cluster_name" {
  value = module.eks.cluster_name
}

output "eks_cluster_endpoint" {
  value     = module.eks.cluster_endpoint
  sensitive = true
}

output "rds_endpoint" {
  value     = aws_db_instance.postgres.endpoint
  sensitive = true
}

output "redis_endpoint" {
  value     = aws_elasticache_replication_group.redis.primary_endpoint_address
  sensitive = true
}

output "ecr_api_gateway_url" {
  value = aws_ecr_repository.api_gateway.repository_url
}

output "ecr_orchestrator_url" {
  value = aws_ecr_repository.orchestrator.repository_url
}

output "ecr_frontend_url" {
  value = aws_ecr_repository.frontend.repository_url
}

output "s3_artifacts_bucket" {
  value = aws_s3_bucket.artifacts.bucket
}
