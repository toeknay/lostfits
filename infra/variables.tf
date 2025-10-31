variable "do_token" {
  type        = string
  description = "DigitalOcean API token (optional if set in env DIGITALOCEAN_TOKEN)"
  default     = ""
}

variable "region" {
  type        = string
  description = "DigitalOcean region"
  default     = "sfo3"
}

variable "domain" {
  type        = string
  description = "Root domain to configure A record for"
  default     = "lostfits.com"
}

variable "droplet_size" {
  type        = string
  default     = "s-1vcpu-2gb"
}

variable "db_size" {
  type        = string
  default     = "db-s-1vcpu-1gb"
}

variable "redis_size" {
  type        = string
  default     = "redis-s-1vcpu-1gb"
}

variable "ssh_key_ids" {
  type        = list(number)
  description = "List of DO SSH key IDs to add to the droplet"
  default     = []
}
