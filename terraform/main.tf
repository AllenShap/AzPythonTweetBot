variable "AZURE_ACCESS_KEY" {
  type      = string
  sensitive = true
}
variable "AZURE_STORAGE_ACCOUNT_NAME" {
  type      = string
  sensitive = true
}
variable "AZURE_CONTAINER_NAME" {
  type      = string
  sensitive = true
}


terraform {
  required_providers {
    azurerm = {
      source  = "hashicorp/azurerm"
      version = "~>3.94.0"
    }
  }
  backend "azurerm" {
    access_key = var.AZURE_ACCESS_KEY
    storage_account_name = var.AZURE_STORAGE_ACCOUNT_NAME
    container_name = var.AZURE_CONTAINER_NAME
    key = "terraform.tfstate"
}
  required_version = ">=1.1.0"
}

provider "azurerm" {
  features {
    resource_group {
      prevent_deletion_if_contains_resources = false
    }
  }
}
