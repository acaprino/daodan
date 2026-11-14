module "label" {
  source  = "cloudposse/label/null"
  version = "0.25.0"

  namespace = "acme"
  stage     = var.stage
  name      = "shop"
}

module "network" {
  source = "./modules/network"

  name = module.label.id
}

resource "random_id" "suffix" {
  byte_length = 4
}
