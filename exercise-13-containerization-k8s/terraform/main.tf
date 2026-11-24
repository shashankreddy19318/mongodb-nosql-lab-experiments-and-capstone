# Lab 13 - Terraform Configuration for MongoDB Atlas Free-Tier Cluster
# Provisioning: Project, M0 Free Cluster (AWS ap-south-1), Database User, IP Access List
# Reference: https://github.com/sujeetjagtap/NoSQL-Databases-using-MongoDB/blob/main/chapter-13/main.tf

terraform {
  required_version = ">= 1.5.0"
  required_providers {
    mongodbatlas = {
      source  = "mongodb/mongodbatlas"
      version = "~> 1.16"
    }
  }
}

provider "mongodbatlas" {
  public_key  = var.atlas_public_key
  private_key = var.atlas_private_key
}

# --- Atlas Project ---
resource "mongodbatlas_project" "nosql_labs" {
  name   = var.project_name
  org_id = var.atlas_org_id
}

# --- Free Tier Cluster (M0 Sandbox) ---
resource "mongodbatlas_cluster" "training" {
  project_id   = mongodbatlas_project.nosql_labs.id
  name         = var.cluster_name
  cluster_type = "REPLICASET"

  provider_name               = "TENANT"
  backing_provider_name       = "AWS"
  provider_region_name        = var.atlas_region # e.g. "AP_SOUTH_1" (Mumbai)
  provider_instance_size_name = "M0"

  serverless                   = false
  cloud_backup                 = false # Free tier has no cloud backup
  auto_scaling_disk_gb_enabled = false
  mongo_db_major_version       = "7.0"
}

# --- Database User ---
resource "mongodbatlas_database_user" "lab_user" {
  project_id         = mongodbatlas_project.nosql_labs.id
  username           = var.db_username
  password           = var.atlas_user_password
  auth_database_name = "admin"

  roles {
    role_name     = "readWriteAnyDatabase"
    database_name = "admin"
  }
}

# --- IP Access List (Whitelist) ---
resource "mongodbatlas_ip_access_list" "allow_all" {
  project_id = mongodbatlas_project.nosql_labs.id
  cidr_block = var.allowed_cidr
  comment    = "Training access list (replace with restricted CIDR in production)"
}

# --- Outputs ---
output "project_id" {
  value       = mongodbatlas_project.nosql_labs.id
  description = "MongoDB Atlas Project ID"
}

output "cluster_state" {
  value       = mongodbatlas_cluster.training.state_name
  description = "Current provisioning state of the cluster"
}

output "connection_string" {
  value       = mongodbatlas_cluster.training.connection_strings[0].standard_srv
  description = "MongoDB Atlas SRV connection string"
}

output "cluster_uri" {
  value       = "mongodb+srv://${var.db_username}:${var.atlas_user_password}@${mongodbatlas_cluster.training.connection_strings[0].standard_srv}/?retryWrites=true&w=majority"
  description = "Fully-qualified application connection URI"
  sensitive   = true
}
