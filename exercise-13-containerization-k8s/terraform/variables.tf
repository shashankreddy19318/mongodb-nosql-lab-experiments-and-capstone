# terraform/variables.tf

variable "atlas_public_key" {
  description = "MongoDB Atlas Programmatic Public API Key"
  type        = string
  default     = ""
}

variable "atlas_private_key" {
  description = "MongoDB Atlas Programmatic Private API Key"
  type        = string
  sensitive   = true
  default     = ""
}

variable "atlas_org_id" {
  description = "MongoDB Atlas Organization ID (found in Atlas Settings)"
  type        = string
  default     = "650000000000000000000000"
}

variable "project_name" {
  description = "Atlas Project Name"
  type        = string
  default     = "NoSQL Labs - Training"
}

variable "cluster_name" {
  description = "Name of the Atlas cluster"
  type        = string
  default     = "training-cluster"
}

variable "atlas_region" {
  description = "Cloud region for deployment (e.g. AP_SOUTH_1 for Mumbai, US_EAST_1 for Virginia)"
  type        = string
  default     = "AP_SOUTH_1"
}

variable "db_username" {
  description = "Database username for application access"
  type        = string
  default     = "lab_user"
}

variable "atlas_user_password" {
  description = "Password for the lab database user"
  type        = string
  sensitive   = true
  default     = "SecurePass123!Atlas"
}

variable "allowed_cidr" {
  description = "CIDR block permitted to connect to cluster"
  type        = string
  default     = "0.0.0.0/0"
}
