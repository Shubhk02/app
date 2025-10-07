# DevOps Setup Guide

## Local Development with Docker

### Prerequisites
- Docker
- Docker Compose
- Git

### Quick Start
1. Clone the repository
```bash
git clone https://github.com/Shubhk02/app.git
cd app
```

2. Create environment files from templates
```bash
cp .env.template .env
```

3. Start the application using Docker Compose
```bash
docker-compose up -d
```

The application will be available at:
- Frontend: http://localhost:3000
- Backend API: http://localhost:8000
- API Documentation: http://localhost:8000/docs

### Development Workflow
- Frontend hot-reload is enabled for development
- Backend changes will trigger automatic reload
- MongoDB data persists in a Docker volume

## CI/CD Pipeline

The application uses GitHub Actions for continuous integration and deployment:

1. **Test Stage**
   - Runs Python backend tests
   - Runs frontend unit tests
   - Uses MongoDB service container for integration tests

2. **Build Stage**
   - Builds Docker images for frontend and backend
   - Pushes images to Docker Hub registry

3. **Deploy Stage**
   - Configurable for different environments (staging/production)
   - Can be extended for Kubernetes deployment

### Required Secrets
Set these in GitHub repository settings:
- `DOCKER_HUB_USERNAME`
- `DOCKER_HUB_TOKEN`

## Deployment

### Production Setup Requirements
- MongoDB instance (Atlas recommended)
- Kubernetes cluster or similar container orchestration
- SSL certificates for HTTPS
- Proper environment variables setup

### Environment Variables
Production environment should set:
- `MONGO_URL`: MongoDB connection string
- `DB_NAME`: Database name
- `JWT_SECRET_KEY`: Strong secret key for JWT
- `CORS_ORIGINS`: Allowed frontend origins
- `REACT_APP_API_URL`: Backend API URL

### Health Monitoring
- Backend health check: GET /health
- Frontend health check: GET /
- MongoDB connection status monitored
- Container health checks configured

### Scaling Considerations
- Frontend is stateless and can be scaled horizontally
- Backend API can be scaled with proper session management
- MongoDB should be properly clustered for production

## Backup and Recovery
- MongoDB data persists in Docker volumes
- Implement regular database backups
- Document recovery procedures

## Security Notes
- All secrets should be managed via environment variables
- Production deployments should use HTTPS
- Regular security updates for dependencies
- Proper network security groups configuration

## Monitoring and Logging
- Application exposes health check endpoints
- Container logs available via docker logs
- Consider adding application monitoring (e.g., Prometheus/Grafana)
- Set up log aggregation for production