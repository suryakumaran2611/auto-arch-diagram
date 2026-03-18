variable "aws_region" {
  description = "AWS region"
  type        = string
  default     = "us-east-1"
}

variable "cluster_name" {
  description = "EKS cluster name"
  type        = string
  default     = "microservices-cluster"
}

variable "kubernetes_version" {
  description = "Kubernetes version"
  type        = string
  default     = "1.27"
}

variable "instance_type" {
  description = "EC2 instance type for worker nodes"
  type        = string
  default     = "t3.large"
}

variable "desired_size" {
  description = "Desired number of worker nodes"
  type        = number
  default     = 3
}

variable "min_size" {
  description = "Minimum number of worker nodes"
  type        = number
  default     = 2
}

variable "max_size" {
  description = "Maximum number of worker nodes"
  type        = number
  default     = 10
}

variable "microservices" {
  description = "List of microservices names"
  type        = list(string)
  default     = ["api-gateway", "user-service", "order-service", "payment-service", "notification-service", "inventory-service"]
}

variable "db_username" {
  description = "RDS master username"
  type        = string
  default     = "microservices"
  sensitive   = true
}

variable "db_password" {
  description = "RDS master password"
  type        = string
  default     = "MicroServices123!"
  sensitive   = true
}
