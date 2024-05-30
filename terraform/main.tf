terraform {
  required_providers {
    azurerm = {
      source  = "hashicorp/azurerm"
      version = "~>3.94.0"
    }
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


variable "TWITTER_CONSUMER_KEY" {
  type      = string
  sensitive = true
}
variable "TWITTER_CONSUMER_SECRET" {
  type      = string
  sensitive = true
}
variable "TWITTER_ACCESS_TOKEN" {
  type      = string
  sensitive = true
}
variable "TWITTER_ACCESS_TOKEN_SECRET" {
  type      = string
  sensitive = true
}


resource "azurerm_resource_group" "RG-USNYTPythonTwitterBot" {
  name     = "USNYTPythonTwitterBot"
  location = "eastus"
}

resource "azurerm_storage_account" "USNYTPythonTwitterBotSA" {
  name                     = "usnytpythontwitterbotsa"
  resource_group_name      = azurerm_resource_group.RG-USNYTPythonTwitterBot.name
  location                 = azurerm_resource_group.RG-USNYTPythonTwitterBot.location
  account_tier             = "Standard"
  account_replication_type = "LRS"

  depends_on = [azurerm_resource_group.RG-USNYTPythonTwitterBot]
}

resource "azurerm_storage_container" "USNYTPythonTwitterBotSAContainer" {
  name                  = "usnytpythontwittercont"
  storage_account_name  = azurerm_storage_account.USNYTPythonTwitterBotSA.name
  container_access_type = "private"

  depends_on = [azurerm_storage_account.USNYTPythonTwitterBotSA]
}


resource "azurerm_cognitive_account" "CA-USNYTPythonTwitterBot" {
  name                = "CA-USNYTPythonTwitterBot"
  location            = azurerm_resource_group.RG-USNYTPythonTwitterBot.location
  resource_group_name = azurerm_resource_group.RG-USNYTPythonTwitterBot.name
  kind                = "TextAnalytics"
  sku_name            = "S"

  custom_question_answering_search_service_id  = azurerm_search_service.Search-USNYTPythonTwitterBot.id
  custom_question_answering_search_service_key = azurerm_search_service.Search-USNYTPythonTwitterBot.primary_key


  depends_on = [azurerm_resource_group.RG-USNYTPythonTwitterBot]
}

resource "azurerm_search_service" "Search-USNYTPythonTwitterBot" {
  name                = "freenytimesaisearch"
  location            = azurerm_resource_group.RG-USNYTPythonTwitterBot.location
  resource_group_name = azurerm_resource_group.RG-USNYTPythonTwitterBot.name
  sku                 = "free"

  depends_on = [azurerm_resource_group.RG-USNYTPythonTwitterBot]
}



resource "azurerm_cosmosdb_account" "USNYTPythonTwitterBotCDBAccount" {
  depends_on          = [azurerm_storage_account.USNYTPythonTwitterBotSA]
  name                = "usnytpythontwitterbotcdb"
  location            = azurerm_resource_group.RG-USNYTPythonTwitterBot.location
  resource_group_name = azurerm_resource_group.RG-USNYTPythonTwitterBot.name
  offer_type          = "Standard"
  kind                = "GlobalDocumentDB"
  consistency_policy {
    consistency_level       = "Session"
    max_interval_in_seconds = 5
    max_staleness_prefix    = 100
  }
  geo_location {
    location          = azurerm_resource_group.RG-USNYTPythonTwitterBot.location
    failover_priority = 0
  }
  capabilities {
    name = "EnableServerless"
  }
  backup {
    type = "Continuous"
    tier = "Continuous7Days"
  }
}

resource "azurerm_cosmosdb_sql_database" "USNYTPythonTwitterBotCDB" {
  depends_on          = [azurerm_storage_account.USNYTPythonTwitterBotSA]
  name                = "USNYTPythonTwitterBot"
  resource_group_name = azurerm_resource_group.RG-USNYTPythonTwitterBot.name
  account_name        = azurerm_cosmosdb_account.USNYTPythonTwitterBotCDBAccount.name
}

resource "azurerm_cosmosdb_sql_container" "USNYTPythonTwitterBotCDBContainer" {
  depends_on          = [azurerm_storage_account.USNYTPythonTwitterBotSA]
  name                = "USNYTPythonTwitterBotContainer"
  resource_group_name = azurerm_resource_group.RG-USNYTPythonTwitterBot.name

  account_name          = azurerm_cosmosdb_account.USNYTPythonTwitterBotCDBAccount.name
  database_name         = azurerm_cosmosdb_sql_database.USNYTPythonTwitterBotCDB.name
  partition_key_path    = "/categoryId"
  partition_key_version = 2
  indexing_policy {
    indexing_mode = "consistent"

    included_path {
      path = "/*"
    }
    excluded_path {
      path = "/\"_etag\"/?"
    }
  }
}


resource "azurerm_service_plan" "ASP-USNYTPythonTwitterBot-617e" {
  name                = "ASP-USNYTPythonTwitterBot-617e"
  resource_group_name = azurerm_resource_group.RG-USNYTPythonTwitterBot.name
  location            = azurerm_resource_group.RG-USNYTPythonTwitterBot.location
  os_type             = "Linux"
  sku_name            = "Y1"
}

resource "azurerm_log_analytics_workspace" "LogAnalyticsWS-USNYTPythonTwitterBot" {
  name                = "workspace-USNYTPythonTwitterBot"
  location            = azurerm_resource_group.RG-USNYTPythonTwitterBot.location
  resource_group_name = azurerm_resource_group.RG-USNYTPythonTwitterBot.name
  sku                 = "PerGB2018"
  retention_in_days   = 30
}

resource "azurerm_application_insights" "AppInsights-USNYTPythonTwitterBot" {
  name                = "PythonTwitterBot-AppI"
  location            = azurerm_resource_group.RG-USNYTPythonTwitterBot.location
  resource_group_name = azurerm_resource_group.RG-USNYTPythonTwitterBot.name
  application_type    = "web"
  workspace_id        = azurerm_log_analytics_workspace.LogAnalyticsWS-USNYTPythonTwitterBot.id
}


resource "azurerm_linux_function_app" "USNYTPythonTwitterBotFA-PROD" {
  depends_on          = [azurerm_storage_account.USNYTPythonTwitterBotSA]
  name                = "USNYTPythonTwitterBotter"
  resource_group_name = azurerm_resource_group.RG-USNYTPythonTwitterBot.name
  location            = azurerm_resource_group.RG-USNYTPythonTwitterBot.location

  storage_account_name         = azurerm_storage_account.USNYTPythonTwitterBotSA.name
  storage_account_access_key   = azurerm_storage_account.USNYTPythonTwitterBotSA.primary_access_key
  service_plan_id              = azurerm_service_plan.ASP-USNYTPythonTwitterBot-617e.id
  content_share_force_disabled = true

  app_settings = {
    COGNITIVE_ENDPOINT        = azurerm_cognitive_account.CA-USNYTPythonTwitterBot.endpoint,
    COGNITIVE_KEY             = azurerm_cognitive_account.CA-USNYTPythonTwitterBot.primary_access_key,
    COGNITIVE_SEARCH_ENDPOINT = "https://${azurerm_search_service.Search-USNYTPythonTwitterBot.name}.search.windows.net"
    COGNITIVE_SEARCH_KEY      = azurerm_search_service.Search-USNYTPythonTwitterBot.primary_key,
    COSMOS_DB_ENDPOINT          = azurerm_cosmosdb_account.USNYTPythonTwitterBotCDBAccount.endpoint,
    COSMOS_DB_NAME              = azurerm_cosmosdb_sql_database.USNYTPythonTwitterBotCDB.name,
    COSMOS_DB_CONTAINER_NAME    = azurerm_cosmosdb_sql_container.USNYTPythonTwitterBotCDBContainer.name,
    COSMOS_DB_CREDENTIAL        = azurerm_cosmosdb_account.USNYTPythonTwitterBotCDBAccount.primary_key,
    TWITTER_CONSUMER_KEY        = var.TWITTER_CONSUMER_KEY,
    TWITTER_CONSUMER_SECRET     = var.TWITTER_CONSUMER_SECRET,
    TWITTER_ACCESS_TOKEN        = var.TWITTER_ACCESS_TOKEN,
    TWITTER_ACCESS_TOKEN_SECRET = var.TWITTER_ACCESS_TOKEN_SECRET,
  }

  sticky_settings {
    app_setting_names = ["TWITTER_CONSUMER_KEY", "TWITTER_CONSUMER_SECRET", "TWITTER_ACCESS_TOKEN", "TWITTER_ACCESS_TOKEN_SECRET", "COSMOS_DB_ENDPOINT", "COSMOS_DB_NAME", "COSMOS_DB_CONTAINER_NAME", "COSMOS_DB_CREDENTIAL", "FUNCTIONS_EXTENSION_VERSION", "AzureWebJobsStorage", "APPLICATIONINSIGHTS_CONNECTION_STRING", "APPINSIGHTS_INSTRUMENTATIONKEY", "FUNCTIONS_WORKER_RUNTIME", "AzureWebJobsDashboard", "COGNITIVE_ENDPOINT", "COGNITIVE_KEY", "COGNITIVE_SEARCH_ENDPOINT", "COGNITIVE_SEARCH_KEY"]
  }

  site_config {
    app_scale_limit                        = "1"
    application_insights_connection_string = azurerm_application_insights.AppInsights-USNYTPythonTwitterBot.connection_string
    application_insights_key               = azurerm_application_insights.AppInsights-USNYTPythonTwitterBot.instrumentation_key
    cors {
      allowed_origins = ["*"]
    }
    application_stack {
      python_version = 3.11
    }
  }
}


resource "azurerm_linux_function_app_slot" "USNYTPythonTwitterBotFA-DEV" {
  depends_on                   = [azurerm_storage_account.USNYTPythonTwitterBotSA]
  name                         = "dev"
  function_app_id              = azurerm_linux_function_app.USNYTPythonTwitterBotFA-PROD.id
  storage_account_name         = azurerm_storage_account.USNYTPythonTwitterBotSA.name
  storage_account_access_key   = azurerm_storage_account.USNYTPythonTwitterBotSA.primary_access_key
  content_share_force_disabled = true

  app_settings = {
    COGNITIVE_ENDPOINT        = azurerm_cognitive_account.CA-USNYTPythonTwitterBot.endpoint,
    COGNITIVE_KEY             = azurerm_cognitive_account.CA-USNYTPythonTwitterBot.primary_access_key,
    COGNITIVE_SEARCH_ENDPOINT = "https://${azurerm_search_service.Search-USNYTPythonTwitterBot.name}.search.windows.net"
    COGNITIVE_SEARCH_KEY      = azurerm_search_service.Search-USNYTPythonTwitterBot.primary_key,
    COSMOS_DB_ENDPOINT          = azurerm_cosmosdb_account.USNYTPythonTwitterBotCDBAccount.endpoint,
    COSMOS_DB_NAME              = azurerm_cosmosdb_sql_database.USNYTPythonTwitterBotCDB.name,
    COSMOS_DB_CONTAINER_NAME    = azurerm_cosmosdb_sql_container.USNYTPythonTwitterBotCDBContainer.name,
    COSMOS_DB_CREDENTIAL        = azurerm_cosmosdb_account.USNYTPythonTwitterBotCDBAccount.primary_key,
    TWITTER_CONSUMER_KEY        = var.TWITTER_CONSUMER_KEY,
    TWITTER_CONSUMER_SECRET     = var.TWITTER_CONSUMER_SECRET,
    TWITTER_ACCESS_TOKEN        = var.TWITTER_ACCESS_TOKEN,
    TWITTER_ACCESS_TOKEN_SECRET = var.TWITTER_ACCESS_TOKEN_SECRET,
  }

  site_config {
    app_scale_limit                        = "1"
    application_insights_connection_string = azurerm_application_insights.AppInsights-USNYTPythonTwitterBot.connection_string
    application_insights_key               = azurerm_application_insights.AppInsights-USNYTPythonTwitterBot.instrumentation_key
    cors {
      allowed_origins = ["*"]
    }
    application_stack {
      python_version = 3.11
    }
  }
}
