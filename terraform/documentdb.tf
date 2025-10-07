# DocumentDB Cluster
resource "aws_docdb_cluster" "main" {
  cluster_identifier      = "${var.cluster_name}-docdb"
  engine                  = "docdb"
  master_username         = "administrator"
  master_password        = random_password.docdb.result
  backup_retention_period = 7
  preferred_backup_window = "02:00-04:00"
  skip_final_snapshot    = false
  final_snapshot_identifier = "${var.cluster_name}-final-snapshot"
  
  vpc_security_group_ids = [aws_security_group.docdb.id]
  db_subnet_group_name   = aws_docdb_subnet_group.main.name

  tags = {
    Environment = var.environment
    Terraform   = "true"
  }
}

# DocumentDB Instances
resource "aws_docdb_cluster_instance" "main" {
  count              = 2
  identifier         = "${var.cluster_name}-docdb-${count.index + 1}"
  cluster_identifier = aws_docdb_cluster.main.id
  instance_class     = "db.r6g.large"

  tags = {
    Environment = var.environment
    Terraform   = "true"
  }
}

# DocumentDB Subnet Group
resource "aws_docdb_subnet_group" "main" {
  name       = "${var.cluster_name}-docdb-subnet-group"
  subnet_ids = module.vpc.private_subnets

  tags = {
    Environment = var.environment
    Terraform   = "true"
  }
}

# Security Group for DocumentDB
resource "aws_security_group" "docdb" {
  name        = "${var.cluster_name}-docdb-sg"
  description = "Security group for DocumentDB cluster"
  vpc_id      = module.vpc.vpc_id

  ingress {
    from_port       = 27017
    to_port         = 27017
    protocol        = "tcp"
    security_groups = [module.eks.cluster_security_group_id]
  }

  tags = {
    Environment = var.environment
    Terraform   = "true"
  }
}

# Generate random password for DocumentDB
resource "random_password" "docdb" {
  length  = 16
  special = false
}

# Store DocumentDB credentials in Secrets Manager
resource "aws_secretsmanager_secret" "docdb" {
  name = "${var.cluster_name}-docdb-credentials"
  
  tags = {
    Environment = var.environment
    Terraform   = "true"
  }
}

resource "aws_secretsmanager_secret_version" "docdb" {
  secret_id = aws_secretsmanager_secret.docdb.id
  secret_string = jsonencode({
    username = aws_docdb_cluster.main.master_username
    password = random_password.docdb.result
    host     = aws_docdb_cluster.main.endpoint
    port     = 27017
    dbname   = "hospital_token_db"
  })
}