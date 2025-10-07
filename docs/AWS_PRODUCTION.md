# AWS Production Setup Guide

## Infrastructure Overview

The application is deployed on AWS with the following components:

- **Amazon EKS (Kubernetes)**
  - Production-grade container orchestration
  - Auto-scaling capabilities
  - Multi-AZ deployment

- **Amazon DocumentDB**
  - MongoDB-compatible database
  - Fully managed, highly available
  - Automated backups and updates

- **Amazon ECR**
  - Private container registry
  - Image vulnerability scanning
  - Lifecycle policies for image management

- **Route53 & ACM**
  - DNS management
  - SSL/TLS certificates
  - Custom domain configuration

## Prerequisites

1. AWS CLI installed and configured
2. kubectl installed
3. Terraform installed
4. Domain name registered in Route53

## Initial Setup

1. Configure AWS credentials:
```bash
aws configure
```

2. Initialize Terraform:
```bash
cd terraform
terraform init
```

3. Apply Terraform configuration:
```bash
terraform plan
terraform apply
```

## Infrastructure Details

### VPC Configuration
- Region: us-west-2
- 3 Availability Zones
- Private and Public subnets
- NAT Gateways for private subnet access

### EKS Cluster
- Kubernetes version: 1.28
- Node type: t3.medium
- Auto-scaling: 2-4 nodes
- Private networking with public endpoint

### DocumentDB
- 2 instances (1 primary, 1 replica)
- Instance class: db.r6g.large
- Automated backups
- Private subnet deployment

### Security
- Private subnets for workloads
- Security groups for access control
- SSL/TLS encryption in transit
- Encryption at rest for all services

## Deployment Process

1. Push code to main branch
2. GitHub Actions workflow:
   - Runs tests
   - Builds Docker images
   - Pushes to ECR
   - Deploys to EKS

## Environment Variables

Required AWS secrets in GitHub:
```
AWS_ACCESS_KEY_ID
AWS_SECRET_ACCESS_KEY
```

## Monitoring and Logging

### CloudWatch Integration
- Container logs
- Metrics monitoring
- Alerts and dashboards

### Health Checks
- EKS cluster health
- Pod health checks
- Database monitoring

## Backup and Disaster Recovery

### Database Backups
- Automated daily backups
- 7-day retention
- Point-in-time recovery

### Infrastructure
- Terraform state in S3
- Multi-AZ deployment
- Automated failover

## Cost Optimization

Estimated monthly costs:
- EKS: ~$73 (cluster) + ~$140 (2 nodes)
- DocumentDB: ~$400 (2 instances)
- Load Balancer: ~$20
- Data Transfer: Variable

## Scaling Considerations

### Horizontal Pod Autoscaling
```yaml
apiVersion: autoscaling/v2
kind: HorizontalPodAutoscaler
metadata:
  name: backend-hpa
spec:
  scaleTargetRef:
    apiVersion: apps/v1
    kind: Deployment
    name: backend
  minReplicas: 2
  maxReplicas: 10
  metrics:
  - type: Resource
    resource:
      name: cpu
      target:
        type: Utilization
        averageUtilization: 70
```

### Node Autoscaling
- Minimum: 2 nodes
- Maximum: 4 nodes
- Scale based on pod resource requests

## Troubleshooting

1. Check pod status:
```bash
kubectl get pods -n hospital-token-system
```

2. View pod logs:
```bash
kubectl logs -f deployment/backend -n hospital-token-system
```

3. Check DocumentDB connectivity:
```bash
kubectl exec -it deployment/backend -n hospital-token-system -- python -c "from pymongo import MongoClient; MongoClient('$MONGO_URL').admin.command('ping')"
```

## Security Best Practices

1. Network Security
   - Private subnets for workloads
   - Security groups for fine-grained access
   - VPC endpoints for AWS services

2. Authentication & Authorization
   - IAM roles for service accounts
   - Pod security policies
   - Network policies

3. Data Security
   - Encryption at rest
   - SSL/TLS for in-transit
   - Secrets management

## Maintenance

### Regular Tasks
1. Update EKS version
2. Rotate credentials
3. Review security patches
4. Monitor resource usage

### Backup Verification
1. Monthly backup restoration tests
2. Disaster recovery drills

## Support and Escalation

1. First Level: DevOps team
2. Second Level: AWS Support
3. Emergency: AWS Enterprise Support