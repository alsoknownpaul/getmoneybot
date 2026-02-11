# Terraform configuration for Yandex Cloud
# GetMoney Bot Infrastructure

terraform {
  required_version = ">= 1.0"

  required_providers {
    yandex = {
      source  = "yandex-cloud/yandex"
      version = "~> 0.100"
    }
  }
}

provider "yandex" {
  cloud_id  = var.yc_cloud_id
  folder_id = var.yc_folder_id
  zone      = var.zone
}

# Get latest Ubuntu 22.04 LTS image
data "yandex_compute_image" "ubuntu" {
  family = "ubuntu-2204-lts"
}

# VPC Network
resource "yandex_vpc_network" "main" {
  name = "getmoney-network"
}

# Subnet
resource "yandex_vpc_subnet" "main" {
  name           = "getmoney-subnet"
  zone           = var.zone
  network_id     = yandex_vpc_network.main.id
  v4_cidr_blocks = ["10.0.1.0/24"]
}

# Security Group
resource "yandex_vpc_security_group" "bot" {
  name        = "getmoney-sg"
  description = "Security group for GetMoney bot"
  network_id  = yandex_vpc_network.main.id

  # SSH
  ingress {
    protocol       = "TCP"
    port           = 22
    v4_cidr_blocks = ["0.0.0.0/0"]
    description    = "SSH access"
  }

  # HTTP (for webhook if needed)
  # ingress {
  #   protocol       = "TCP"
  #   port           = 80
  #   v4_cidr_blocks = ["0.0.0.0/0"]
  #   description    = "HTTP"
  # }

  # HTTPS (for webhook if needed)
  ingress {
    protocol       = "TCP"
    port           = 443
    v4_cidr_blocks = ["0.0.0.0/0"]
    description    = "HTTPS"
  }

  # Allow all outbound traffic
  egress {
    protocol       = "ANY"
    v4_cidr_blocks = ["0.0.0.0/0"]
    description    = "Allow all outbound"
  }
}

# Static Public IP Address
resource "yandex_vpc_address" "bot" {
  name = "getmoney-public-ip"

  external_ipv4_address {
    zone_id = var.zone
  }

  labels = {
    project = "getmoney"
  }
}

# Compute Instance
resource "yandex_compute_instance" "bot" {
  name        = "getmoney-bot"
  platform_id = "standard-v3"
  zone        = var.zone

  resources {
    cores         = 2
    memory        = 2
    core_fraction = 20  # Burstable instance for cost savings
  }

  scheduling_policy {
    preemptible = false
  }

  boot_disk {
    initialize_params {
      image_id = data.yandex_compute_image.ubuntu.id
      size     = 20
      type     = "network-ssd"
    }
  }

  network_interface {
    subnet_id          = yandex_vpc_subnet.main.id
    nat                = true
    nat_ip_address     = yandex_vpc_address.bot.external_ipv4_address[0].address
    security_group_ids = [yandex_vpc_security_group.bot.id]
  }

  metadata = {
    ssh-keys = "ubuntu:${file(var.ssh_public_key_path)}"
  }

  labels = {
    project = "getmoney"
    env     = "production"
  }
}

# Daily snapshot schedule
resource "yandex_compute_snapshot_schedule" "daily" {
  name = "getmoney-daily-snapshots"

  schedule_policy {
    expression = "0 3 * * *"  # Every day at 3:00 AM
  }

  snapshot_count = 7  # Keep last 7 snapshots

  snapshot_spec {
    description = "Daily automatic snapshot"
    labels = {
      project = "getmoney"
      type    = "automatic"
    }
  }

  disk_ids = [yandex_compute_instance.bot.boot_disk[0].disk_id]
}
