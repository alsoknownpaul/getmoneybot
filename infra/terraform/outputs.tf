# Terraform outputs

output "static_public_ip" {
  description = "Static public IP address (persists across instance recreations)"
  value       = yandex_vpc_address.bot.external_ipv4_address[0].address
}

output "instance_external_ip" {
  description = "External IP address of the bot instance"
  value       = yandex_compute_instance.bot.network_interface[0].nat_ip_address
}

output "instance_internal_ip" {
  description = "Internal IP address of the bot instance"
  value       = yandex_compute_instance.bot.network_interface[0].ip_address
}

output "instance_id" {
  description = "Instance ID"
  value       = yandex_compute_instance.bot.id
}

output "ssh_command" {
  description = "SSH command to connect to the instance"
  value       = "ssh -i ~/.ssh/getmoney ubuntu@${yandex_vpc_address.bot.external_ipv4_address[0].address}"
}

# Output for Ansible inventory
output "ansible_inventory" {
  description = "Ansible inventory content"
  value       = <<-EOT
    all:
      hosts:
        bot:
          ansible_host: ${yandex_vpc_address.bot.external_ipv4_address[0].address}
          ansible_user: ubuntu
          ansible_ssh_private_key_file: ~/.ssh/getmoney
  EOT
}
