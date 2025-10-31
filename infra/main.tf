resource "digitalocean_vpc" "lostfits" {
  name     = "lostfits-vpc"
  region   = var.region
  ip_range = "10.123.0.0/20"
}

resource "digitalocean_droplet" "app" {
  name      = "lostfits-droplet"
  region    = var.region
  size      = var.droplet_size
  image     = "docker-20-04"
  vpc_uuid  = digitalocean_vpc.lostfits.id
  ssh_keys  = var.ssh_key_ids
  tags      = ["lostfits", "app"]
}

resource "digitalocean_database_cluster" "pg" {
  name      = "lostfits-pg"
  engine    = "pg"
  version   = "16"
  size      = var.db_size
  region    = var.region
  num_nodes = 1
  tags      = ["lostfits", "db"]
  private_network_uuid = digitalocean_vpc.lostfits.id
}

resource "digitalocean_database_cluster" "redis" {
  name      = "lostfits-redis"
  engine    = "redis"
  version   = "7"
  size      = var.redis_size
  region    = var.region
  num_nodes = 1
  tags      = ["lostfits", "cache"]
  private_network_uuid = digitalocean_vpc.lostfits.id
}

resource "digitalocean_spaces_bucket" "backups" {
  name   = "lostfits-backups"
  region = var.region
  acl    = "private"
}

resource "digitalocean_firewall" "fw" {
  name = "lostfits-fw"
  droplet_ids = [digitalocean_droplet.app.id]

  inbound_rule { protocol = "tcp"; port_range = "22"; source_addresses = ["0.0.0.0/0", "::/0"] }
  inbound_rule { protocol = "tcp"; port_range = "80"; source_addresses = ["0.0.0.0/0", "::/0"] }
  inbound_rule { protocol = "tcp"; port_range = "443"; source_addresses = ["0.0.0.0/0", "::/0"] }

  outbound_rule { protocol = "tcp"; port_range = "1-65535"; destination_addresses = ["0.0.0.0/0", "::/0"] }
  outbound_rule { protocol = "udp"; port_range = "1-65535"; destination_addresses = ["0.0.0.0/0", "::/0"] }
}

resource "digitalocean_domain" "root" {
  name = var.domain
}

resource "digitalocean_record" "root_a" {
  domain = digitalocean_domain.root.name
  type   = "A"
  name   = "@"
  value  = digitalocean_droplet.app.ipv4_address
}

output "droplet_ip" {
  value = digitalocean_droplet.app.ipv4_address
}

output "postgres_uri_example" {
  value = "postgresql+psycopg://<user>:<pass>@${digitalocean_database_cluster.pg.private_host}:${digitalocean_database_cluster.pg.port}/${digitalocean_database_cluster.pg.database}"
  sensitive = true
}

output "redis_uri_example" {
  value = "redis://default:<pass>@${digitalocean_database_cluster.redis.private_host}:${digitalocean_database_cluster.redis.port}/0"
  sensitive = true
}
