# azure-functions-demo

# Login to Azure
az login

# List subscriptions
az account list --output table

# Set active subscription
az account set --subscription "YOUR_SUBSCRIPTION_ID"



Part 1: Create Azure Resources
Create Resource Group
bashaz group create --name serverless-demo-rg --location eastus
Create Storage Account
bash# Create storage account with short name
STORAGE_NAME="svrless${RANDOM}"
az storage account create \
  --name $STORAGE_NAME \
  --resource-group serverless-demo-rg \
  --location eastus \
  --sku Standard_LRS

echo "Storage Account Name: $STORAGE_NAME"
Create Function App
bash# Create function app
FUNC_APP_NAME="funcdemo${RANDOM}"
az functionapp create \
  --name $FUNC_APP_NAME \
  --resource-group serverless-demo-rg \
  --storage-account $STORAGE_NAME \
  --consumption-plan-location eastus \
  --runtime python \
  --runtime-version 3.11 \
  --functions-version 4 \
  --os-type Linux

echo "Function App Name: $FUNC_APP_NAME"
```

## Part 2: Create GitHub Repository

### Create repository on GitHub
1. Go to GitHub.com
2. Click New repository
3. Name: azure-functions-demo
4. Visibility: Public
5. Add README file
6. Create repository

### Create function files in GitHub repository

#### File: requirements.txt
```
azure-functions
requests
File: host.json
json{
  "version": "2.0",
  "extensionBundle": {
    "id": "Microsoft.Azure.Functions.ExtensionBundle",
    "version": "[4.*, 5.0.0)"
  }
}
File: HttpTriggerDemo/function.json
json{
  "scriptFile": "__init__.py",
  "bindings": [
    {
      "authLevel": "anonymous",
      "type": "httpTrigger",
      "direction": "in",
      "name": "req",
      "methods": ["get", "post"]
    },
    {
      "type": "http",
      "direction": "out",
      "name": "$return"
    }
  ]
}
File: HttpTriggerDemo/init.py
pythonimport azure.functions as func
import json
import logging

def main(req: func.HttpRequest) -> func.HttpResponse:
    logging.info('HTTP trigger function processed a request.')

    name = req.params.get('name')
    if not name:
        try:
            req_body = req.get_json()
            name = req_body.get('name')
        except ValueError:
            pass

    if name:
        response_data = {
            "message": f"Hello, {name}! Welcome to Azure Serverless Functions!",
            "status": "success",
            "timestamp": "2026-01-02"
        }
        return func.HttpResponse(
            json.dumps(response_data),
            mimetype="application/json",
            status_code=200
        )
    else:
        return func.HttpResponse(
            json.dumps({"error": "Please pass a name in query string"}),
            mimetype="application/json",
            status_code=400
        )
File: BlobTriggerDemo/function.json
json{
  "scriptFile": "__init__.py",
  "bindings": [
    {
      "name": "myblob",
      "type": "blobTrigger",
      "direction": "in",
      "path": "uploads/{name}",
      "connection": "AzureWebJobsStorage"
    }
  ]
}
File: BlobTriggerDemo/init.py
pythonimport azure.functions as func
import logging

def main(myblob: func.InputStream):
    logging.info(f"Blob trigger function processed blob \n"
                 f"Name: {myblob.name}\n"
                 f"Blob Size: {myblob.length} bytes")
    
    content = myblob.read()
    logging.info(f"Blob content (first 100 chars): {content[:100]}")
File: TimerTriggerDemo/function.json
json{
  "scriptFile": "__init__.py",
  "bindings": [
    {
      "name": "mytimer",
      "type": "timerTrigger",
      "direction": "in",
      "schedule": "0 */5 * * * *"
    }
  ]
}
File: TimerTriggerDemo/init.py
pythonimport azure.functions as func
import logging
import datetime

def main(mytimer: func.TimerRequest) -> None:
    utc_timestamp = datetime.datetime.utcnow().replace(
        tzinfo=datetime.timezone.utc).isoformat()

    if mytimer.past_due:
        logging.info('The timer is past due!')

    logging.info(f'Timer trigger function ran at {utc_timestamp}')
    logging.info('This function runs every 5 minutes!')
File: .github/workflows/deploy-functions.yml
yamlname: Deploy Azure Functions

on:
  push:
    branches:
      - main
  workflow_dispatch:

env:
  AZURE_FUNCTIONAPP_NAME: 'YOUR_FUNC_APP_NAME'
  AZURE_FUNCTIONAPP_PACKAGE_PATH: '.'
  PYTHON_VERSION: '3.11'

jobs:
  build-and-deploy:
    runs-on: ubuntu-latest
    steps:
    - name: 'Checkout GitHub Action'
      uses: actions/checkout@v3

    - name: Setup Python ${{ env.PYTHON_VERSION }}
      uses: actions/setup-python@v4
      with:
        python-version: ${{ env.PYTHON_VERSION }}

    - name: 'Resolve Project Dependencies'
      shell: bash
      run: |
        pushd './${{ env.AZURE_FUNCTIONAPP_PACKAGE_PATH }}'
        python -m pip install --upgrade pip
        pip install -r requirements.txt --target=".python_packages/lib/site-packages"
        popd

    - name: 'Run Azure Functions Action'
      uses: Azure/functions-action@v1
      with:
        app-name: ${{ env.AZURE_FUNCTIONAPP_NAME }}
        package: ${{ env.AZURE_FUNCTIONAPP_PACKAGE_PATH }}
        publish-profile: ${{ secrets.AZURE_FUNCTIONAPP_PUBLISH_PROFILE }}
        scm-do-build-during-deployment: true
        enable-oryx-build: true
Part 3: Setup GitHub Actions
Get publish profile
bash# Get publish profile
az functionapp deployment list-publishing-profiles \
  --name $FUNC_APP_NAME \
  --resource-group serverless-demo-rg \
  --xml > publish-profile.xml

# Display content
cat publish-profile.xml
Add secret to GitHub

Go to GitHub repository
Settings > Secrets and variables > Actions
New repository secret
Name: AZURE_FUNCTIONAPP_PUBLISH_PROFILE
Value: Paste entire XML content
Add secret

Update workflow file

Edit .github/workflows/deploy-functions.yml
Replace YOUR_FUNC_APP_NAME with actual function app name
Commit changes

Part 4: Test Functions
Test HTTP Trigger
bash# Get function URL
HTTP_URL=$(az functionapp function show \
  --name $FUNC_APP_NAME \
  --resource-group serverless-demo-rg \
  --function-name HttpTriggerDemo \
  --query "invokeUrlTemplate" -o tsv)

echo "HTTP Function URL: $HTTP_URL"

# Test with curl
curl "${HTTP_URL}?name=DevOps"

# Test in browser
echo "Open in browser: ${HTTP_URL}?name=YourName"
Test Blob Trigger
bash# Assign storage permissions
USER_ID=$(az ad signed-in-user show --query id -o tsv)

az role assignment create \
  --role "Storage Blob Data Contributor" \
  --assignee $USER_ID \
  --scope /subscriptions/$(az account show --query id -o tsv)/resourceGroups/serverless-demo-rg/providers/Microsoft.Storage/storageAccounts/$STORAGE_NAME

# Wait for permissions
sleep 30

# Create container
az storage container create \
  --name uploads \
  --account-name $STORAGE_NAME \
  --auth-mode login

# Upload test file
echo "Hello from Azure Functions!" > test.txt
az storage blob upload \
  --account-name $STORAGE_NAME \
  --container-name uploads \
  --name test.txt \
  --file test.txt \
  --auth-mode login

# Check logs
az webapp log tail \
  --name $FUNC_APP_NAME \
  --resource-group serverless-demo-rg
Monitor Functions
bash# View function app in portal
echo "Portal URL: https://portal.azure.com/#@/resource/subscriptions/$(az account show --query id -o tsv)/resourceGroups/serverless-demo-rg/providers/Microsoft.Web/sites/$FUNC_APP_NAME"

# List all functions
az functionapp function list \
  --name $FUNC_APP_NAME \
  --resource-group serverless-demo-rg \
  --output table
Part 5: Cleanup
Delete all resources
bash# Delete resource group and all resources
az group delete --name serverless-demo-rg --yes --no-wait

# Verify deletion
az group list --output table
Terraform and Azure DevOps Infrastructure as Code Demo
Part 1: Setup Backend Storage
Create resource group for Terraform state
bashaz group create \
  --name terraform-state-rg \
  --location eastus
Create storage account for state
bash# Create storage with short name
STATE_STORAGE="tfstate$(date +%s | tail -c 10)"
az storage account create \
  --name $STATE_STORAGE \
  --resource-group terraform-state-rg \
  --location eastus \
  --sku Standard_LRS \
  --encryption-services blob

echo "State Storage Account: $STATE_STORAGE"
Get storage key and create container
bash# Get storage key
STORAGE_KEY=$(az storage account keys list \
  --account-name $STATE_STORAGE \
  --resource-group terraform-state-rg \
  --query "[0].value" -o tsv)

# Create container
az storage container create \
  --name tfstate \
  --account-name $STATE_STORAGE \
  --account-key $STORAGE_KEY

echo "Terraform backend storage ready"
Part 2: Create Azure DevOps Organization
Create organization and project via UI

Go to https://dev.azure.com
Sign in with Azure account
Create new organization
Create new project: terraform-iac-demo
Set visibility to Private

Part 3: Create Service Connection
Create service connection via UI

Project Settings > Service connections
New service connection
Azure Resource Manager > Next
App registration (automatic) > Next
Workload identity federation
Scope level: Subscription
Select your subscription
Service connection name: Azure-Terraform-Connection
Grant access to all pipelines
Save

Alternative: Create service principal manually
bash# Get subscription ID
SUBSCRIPTION_ID=$(az account show --query id -o tsv)

# Create service principal
az ad sp create-for-rbac \
  --name "azure-devops-terraform-sp" \
  --role Contributor \
  --scopes /subscriptions/$SUBSCRIPTION_ID \
  --sdk-auth
Part 4: Create GitHub Repository
Create repository structure
Create repository: azure-terraform-iac
Add these files to the repository:
File: backend.tf
hclterraform {
  backend "azurerm" {
    resource_group_name  = "terraform-state-rg"
    storage_account_name = "REPLACE_WITH_YOUR_STORAGE_NAME"
    container_name       = "tfstate"
    key                  = "terraform.tfstate"
  }
}
File: provider.tf
hclterraform {
  required_version = ">= 1.0"
  required_providers {
    azurerm = {
      source  = "hashicorp/azurerm"
      version = "~> 3.0"
    }
    random = {
      source  = "hashicorp/random"
      version = "~> 3.0"
    }
  }
}

provider "azurerm" {
  features {
    resource_group {
      prevent_deletion_if_contains_resources = false
    }
  }
}
File: variables.tf
hclvariable "resource_group_name" {
  description = "Name of the resource group"
  type        = string
  default     = "terraform-demo-rg"
}

variable "location" {
  description = "Azure region"
  type        = string
  default     = "East US"
}

variable "vm_size" {
  description = "Size of the virtual machine"
  type        = string
  default     = "Standard_B1s"
}

variable "admin_username" {
  description = "Admin username for VM"
  type        = string
  default     = "azureadmin"
}

variable "admin_password" {
  description = "Admin password for VM"
  type        = string
  sensitive   = true
  default     = "P@ssw0rd1234!"
}
File: main.tf
hclresource "random_string" "suffix" {
  length  = 6
  special = false
  upper   = false
}

resource "azurerm_resource_group" "main" {
  name     = var.resource_group_name
  location = var.location

  tags = {
    Environment = "Demo"
    ManagedBy   = "Terraform"
    Project     = "IaC-Demo"
  }
}

resource "azurerm_virtual_network" "main" {
  name                = "vnet-${random_string.suffix.result}"
  address_space       = ["10.0.0.0/16"]
  location            = azurerm_resource_group.main.location
  resource_group_name = azurerm_resource_group.main.name

  tags = azurerm_resource_group.main.tags
}

resource "azurerm_subnet" "main" {
  name                 = "subnet-internal"
  resource_group_name  = azurerm_resource_group.main.name
  virtual_network_name = azurerm_virtual_network.main.name
  address_prefixes     = ["10.0.1.0/24"]
}

resource "azurerm_network_security_group" "main" {
  name                = "nsg-${random_string.suffix.result}"
  location            = azurerm_resource_group.main.location
  resource_group_name = azurerm_resource_group.main.name

  security_rule {
    name                       = "SSH"
    priority                   = 1001
    direction                  = "Inbound"
    access                     = "Allow"
    protocol                   = "Tcp"
    source_port_range          = "*"
    destination_port_range     = "22"
    source_address_prefix      = "*"
    destination_address_prefix = "*"
  }

  tags = azurerm_resource_group.main.tags
}

resource "azurerm_public_ip" "main" {
  name                = "pip-${random_string.suffix.result}"
  location            = azurerm_resource_group.main.location
  resource_group_name = azurerm_resource_group.main.name
  allocation_method   = "Static"
  sku                 = "Standard"

  tags = azurerm_resource_group.main.tags
}

resource "azurerm_network_interface" "main" {
  name                = "nic-${random_string.suffix.result}"
  location            = azurerm_resource_group.main.location
  resource_group_name = azurerm_resource_group.main.name

  ip_configuration {
    name                          = "internal"
    subnet_id                     = azurerm_subnet.main.id
    private_ip_address_allocation = "Dynamic"
    public_ip_address_id          = azurerm_public_ip.main.id
  }

  tags = azurerm_resource_group.main.tags
}

resource "azurerm_network_interface_security_group_association" "main" {
  network_interface_id      = azurerm_network_interface.main.id
  network_security_group_id = azurerm_network_security_group.main.id
}

resource "azurerm_storage_account" "main" {
  name                     = "storage${random_string.suffix.result}"
  resource_group_name      = azurerm_resource_group.main.name
  location                 = azurerm_resource_group.main.location
  account_tier             = "Standard"
  account_replication_type = "LRS"

  tags = azurerm_resource_group.main.tags
}

resource "azurerm_linux_virtual_machine" "main" {
  name                = "vm-demo-${random_string.suffix.result}"
  resource_group_name = azurerm_resource_group.main.name
  location            = azurerm_resource_group.main.location
  size                = var.vm_size
  admin_username      = var.admin_username
  admin_password      = var.admin_password
  disable_password_authentication = false

  network_interface_ids = [
    azurerm_network_interface.main.id,
  ]

  os_disk {
    caching              = "ReadWrite"
    storage_account_type = "Standard_LRS"
  }

  source_image_reference {
    publisher = "Canonical"
    offer     = "0001-com-ubuntu-server-jammy"
    sku       = "22_04-lts-gen2"
    version   = "latest"
  }

  tags = azurerm_resource_group.main.tags
}
File: outputs.tf
hcloutput "resource_group_name" {
  description = "Name of the resource group"
  value       = azurerm_resource_group.main.name
}

output "virtual_network_name" {
  description = "Name of the virtual network"
  value       = azurerm_virtual_network.main.name
}

output "storage_account_name" {
  description = "Name of the storage account"
  value       = azurerm_storage_account.main.name
}

output "vm_public_ip" {
  description = "Public IP address of the VM"
  value       = azurerm_public_ip.main.ip_address
}

output "vm_name" {
  description = "Name of the virtual machine"
  value       = azurerm_linux_virtual_machine.main.name
}

output "admin_username" {
  description = "Admin username for SSH"
  value       = azurerm_linux_virtual_machine.main.admin_username
}
File: azure-pipelines.yml
yamltrigger:
  branches:
    include:
      - main

pool:
  vmImage: 'ubuntu-latest'

variables:
  - name: backendServiceArm
    value: 'Azure-Terraform-Connection'
  - name: backendAzureRmResourceGroupName
    value: 'terraform-state-rg'
  - name: backendAzureRmStorageAccountName
    value: 'REPLACE_WITH_YOUR_STORAGE_NAME'
  - name: backendAzureRmContainerName
    value: 'tfstate'
  - name: backendAzureRmKey
    value: 'terraform.tfstate'
  - name: TF_VERSION
    value: '1.6.6'

stages:
  - stage: Validate
    displayName: 'Terraform Validate'
    jobs:
      - job: ValidateTerraform
        displayName: 'Validate Terraform Configuration'
        steps:
          - task: AzureCLI@2
            displayName: 'Install Terraform & Validate'
            inputs:
              azureSubscription: $(backendServiceArm)
              scriptType: 'bash'
              scriptLocation: 'inlineScript'
              inlineScript: |
                wget -q https://releases.hashicorp.com/terraform/$(TF_VERSION)/terraform_$(TF_VERSION)_linux_amd64.zip
                unzip -q terraform_$(TF_VERSION)_linux_amd64.zip
                sudo mv terraform /usr/local/bin/
                terraform version
                
                export ARM_ACCESS_KEY=$(az storage account keys list \
                  --resource-group $(backendAzureRmResourceGroupName) \
                  --account-name $(backendAzureRmStorageAccountName) \
                  --query '[0].value' -o tsv)
                
                terraform init \
                  -backend-config="resource_group_name=$(backendAzureRmResourceGroupName)" \
                  -backend-config="storage_account_name=$(backendAzureRmStorageAccountName)" \
                  -backend-config="container_name=$(backendAzureRmContainerName)" \
                  -backend-config="key=$(backendAzureRmKey)"
                
                terraform validate

  - stage: Plan
    displayName: 'Terraform Plan'
    dependsOn: Validate
    jobs:
      - job: PlanInfrastructure
        displayName: 'Plan Infrastructure Changes'
        steps:
          - task: AzureCLI@2
            displayName: 'Terraform Plan'
            inputs:
              azureSubscription: $(backendServiceArm)
              scriptType: 'bash'
              scriptLocation: 'inlineScript'
              inlineScript: |
                wget -q https://releases.hashicorp.com/terraform/$(TF_VERSION)/terraform_$(TF_VERSION)_linux_amd64.zip
                unzip -q terraform_$(TF_VERSION)_linux_amd64.zip
                sudo mv terraform /usr/local/bin/
                
                export ARM_ACCESS_KEY=$(az storage account keys list \
                  --resource-group $(backendAzureRmResourceGroupName) \
                  --account-name $(backendAzureRmStorageAccountName) \
                  --query '[0].value' -o tsv)
                
                terraform init \
                  -backend-config="resource_group_name=$(backendAzureRmResourceGroupName)" \
                  -backend-config="storage_account_name=$(backendAzureRmStorageAccountName)" \
                  -backend-config="container_name=$(backendAzureRmContainerName)" \
                  -backend-config="key=$(backendAzureRmKey)"
                
                terraform plan -out=tfplan

  - stage: Apply
    displayName: 'Terraform Apply'
    dependsOn: Plan
    condition: succeeded()
    jobs:
      - deployment: DeployInfrastructure
        displayName: 'Deploy Infrastructure'
        environment: 'production'
        strategy:
          runOnce:
            deploy:
              steps:
                - checkout: self

                - task: AzureCLI@2
                  displayName: 'Terraform Apply'
                  inputs:
                    azureSubscription: $(backendServiceArm)
                    scriptType: 'bash'
                    scriptLocation: 'inlineScript'
                    inlineScript: |
                      wget -q https://releases.hashicorp.com/terraform/$(TF_VERSION)/terraform_$(TF_VERSION)_linux_amd64.zip
                      unzip -q terraform_$(TF_VERSION)_linux_amd64.zip
                      sudo mv terraform /usr/local/bin/
                      
                      export ARM_ACCESS_KEY=$(az storage account keys list \
                        --resource-group $(backendAzureRmResourceGroupName) \
                        --account-name $(backendAzureRmStorageAccountName) \
                        --query '[0].value' -o tsv)
                      
                      terraform init \
                        -backend-config="resource_group_name=$(backendAzureRmResourceGroupName)" \
                        -backend-config="storage_account_name=$(backendAzureRmStorageAccountName)" \
                        -backend-config="container_name=$(backendAzureRmContainerName)" \
                        -backend-config="key=$(backendAzureRmKey)"
                      
                      terraform apply -auto-approve
File: destroy-pipeline.yml
yamltrigger: none

pool:
  vmImage: 'ubuntu-latest'

variables:
  - name: backendServiceArm
    value: 'Azure-Terraform-Connection'
  - name: backendAzureRmResourceGroupName
    value: 'terraform-state-rg'
  - name: backendAzureRmStorageAccountName
    value: 'REPLACE_WITH_YOUR_STORAGE_NAME'
  - name: backendAzureRmContainerName
    value: 'tfstate'
  - name: backendAzureRmKey
    value: 'terraform.tfstate'
  - name: TF_VERSION
    value: '1.6.6'

stages:
  - stage: Destroy
    displayName: 'Destroy Infrastructure'
    jobs:
      - deployment: DestroyInfrastructure
        displayName: 'Destroy All Resources'
        environment: 'production'
        strategy:
          runOnce:
            deploy:
              steps:
                - checkout: self

                - task: AzureCLI@2
                  displayName: 'Terraform Destroy'
                  inputs:
                    azureSubscription: $(backendServiceArm)
                    scriptType: 'bash'
                    scriptLocation: 'inlineScript'
                    inlineScript: |
                      wget -q https://releases.hashicorp.com/terraform/$(TF_VERSION)/terraform_$(TF_VERSION)_linux_amd64.zip
                      unzip -q terraform_$(TF_VERSION)_linux_amd64.zip
                      sudo mv terraform /usr/local/bin/
                      
                      export ARM_ACCESS_KEY=$(az storage account keys list \
                        --resource-group $(backendAzureRmResourceGroupName) \
                        --account-name $(backendAzureRmStorageAccountName) \
                        --query '[0].value' -o tsv)
                      
                      terraform init \
                        -backend-config="resource_group_name=$(backendAzureRmResourceGroupName)" \
                        -backend-config="storage_account_name=$(backendAzureRmStorageAccountName)" \
                        -backend-config="container_name=$(backendAzureRmContainerName)" \
                        -backend-config="key=$(backendAzureRmKey)"
                      
                      terraform destroy -auto-approve
Part 5: Update Azure DevOps Files
Update backend.tf

In Azure DevOps Repos > Files
Edit backend.tf
Replace storage_account_name with your actual storage name
Commit

Update azure-pipelines.yml

Edit azure-pipelines.yml
Replace backendAzureRmStorageAccountName with your storage name
Commit

Update destroy-pipeline.yml

Edit destroy-pipeline.yml
Replace backendAzureRmStorageAccountName with your storage name
Commit

Part 6: Create Pipelines
Create main pipeline

Pipelines > New pipeline
Azure Repos Git
Select repository
Existing Azure Pipelines YAML file
Path: /azure-pipelines.yml
Run pipeline

Create destroy pipeline

Pipelines > New pipeline
Azure Repos Git
Select repository
Existing Azure Pipelines YAML file
Path: /destroy-pipeline.yml
Save only

Part 7: Run and Monitor
Run apply pipeline
Pipeline will execute stages:

Validate: Check Terraform syntax
Plan: Show what will be created
Apply: Create infrastructure
Outputs: Display created resources

Verify resources
bash# List resources in resource group
az resource list \
  --resource-group terraform-demo-rg \
  --output table

# Get VM public IP
az vm list-ip-addresses \
  --resource-group terraform-demo-rg \
  --output table
Run destroy pipeline

Pipelines > Terraform-Destroy
Run pipeline
Confirm and wait for completion

Part 8: Complete Cleanup
Delete all resource groups
bash# Delete Terraform demo resources
az group delete --name terraform-demo-rg --yes --no-wait

# Delete Terraform state storage
az group delete --name terraform-state-rg --yes --no-wait

# Delete Functions demo resources
az group delete --name serverless-demo-rg --yes --no-wait

# Verify all deleted
az group list --output table
Check for remaining resources
bash# List all resources in subscription
az resource list --output table

# Check current costs
az consumption usage list --output table
Summary
What was accomplished
Azure Functions Demo

Created serverless HTTP API endpoint
Implemented blob storage trigger
Setup timer-based scheduled function
Configured GitHub Actions CI/CD
Deployed to Azure automatically

Terraform Infrastructure as Code

Created VM, VNet, Storage, NSG with Terraform
Setup remote state in Azure Storage
Built Azure DevOps pipeline with stages
Automated infrastructure deployment
Created destroy pipeline for cleanup

Benefits achieved

Pay only for execution time
Auto-scaling infrastructure
Version controlled infrastructure
Automated deployments
Repeatable infrastructure creation

Cost optimization

Deleted all resources after demos
Used consumption-based pricing
Leveraged free tiers where possible
Saved remaining Azure credits
