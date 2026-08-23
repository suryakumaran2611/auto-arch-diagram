variable "project" {
  description = "Project name prefix for all resources (used in naming and tags)"
  type        = string
  default     = "mlops-aiops-demo"
}

variable "environment" {
  description = "Deployment environment (dev, staging, prod)"
  type        = string
  default     = "prod"
  validation {
    condition     = contains(["dev", "staging", "prod"], var.environment)
    error_message = "Environment must be dev, staging, or prod."
  }
}

variable "region" {
  description = "AWS region"
  type        = string
  default     = "us-east-1"
}

variable "db_password" {
  description = "Aurora master password (use Secrets Manager in production)"
  type        = string
  sensitive   = true
  default     = "ChangeMe123!ChangeMe123!"
}

variable "alert_email" {
  description = "Email for AIOps alerts (SNS subscription)"
  type        = string
  default     = "ml-ops@example.com"
}
