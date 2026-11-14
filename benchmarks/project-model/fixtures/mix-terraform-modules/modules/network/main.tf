terraform {
  required_providers {
    random = {
      source  = "hashicorp/random"
      version = ">= 3.5"
    }
  }
}

variable "name" {
  type = string
}

resource "random_pet" "network" {
  prefix = var.name
}

output "name" {
  value = random_pet.network.id
}
