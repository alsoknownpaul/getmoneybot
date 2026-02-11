# Terraform variables for Yandex Cloud

# variable "yc_token" {
#   description = "Yandex Cloud OAuth token or IAM token"
#   type        = string
#   sensitive   = true
# }

variable "yc_cloud_id" {
  description = "Yandex Cloud ID"
  type        = string
}

variable "yc_folder_id" {
  description = "Yandex Cloud Folder ID"
  type        = string
}

variable "zone" {
  description = "Yandex Cloud zone"
  type        = string
  default     = "ru-central1-a"
}

variable "ssh_public_key_path" {
  description = "Path to SSH public key file"
  type        = string
  default     = "~/.ssh/getmoney.pub"
}
