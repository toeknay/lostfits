# LostFits Infra (Terraform on DigitalOcean)

This Terraform sets up:
- VPC
- Droplet (Docker Compose host)
- Firewall (80/443/22)
- Managed PostgreSQL (single node)
- Managed Redis (single node)
- Spaces bucket (for nightly `pg_dump`)
- DNS A record for **lostfits.com** pointing to the Droplet's public IP

## Prereqs
- Terraform installed
- DigitalOcean token exported:
  ```bash
  export DIGITALOCEAN_TOKEN="do_pat_token_here"
  ```
- For Spaces access (if you plan to upload dumps from Droplet), create Spaces keys in DO console.

## Usage
```bash
cd infra
terraform init
terraform plan -var="domain=lostfits.com"
terraform apply -var="domain=lostfits.com"
```

Outputs include the Droplet IP and connection info.
