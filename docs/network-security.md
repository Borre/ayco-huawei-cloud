# AYCO Huawei Cloud - Network Security Architecture

**Date:** May 4, 2026  
**Region:** la-north-2 (Mexico City 2)  
**VPC CIDR:** 172.16.0.0/16  
**Subnet CIDR:** 172.16.1.0/24

---

## Overview

The AYCO demo infrastructure uses a **single security group** (`ayco-sg`) with explicit ingress/egress rules to control network traffic. This document provides a complete reference for all security group rules and network flows.

---

## Security Group: `ayco-sg`

**Description:** AYCO demo security group  
**VPC:** `ayco-vpc` (172.16.0.0/16)  
**Attached Resources:**
- ECS `ayco-dify` (Dify + Streamlit Dashboard)
- ECS `ayco-web` (Landing page)
- ECS instances for other demo services

---

## Ingress Rules (Inbound Traffic)

### 1. SSH Access (Presenter Only)

```
Protocol: TCP
Port: 22
Source: var.presenter_ip (Your public IP)
Purpose: Administrative SSH access
```

**Security Note:** Restricted to presenter's IP only. Rotate if IP changes.

---

### 2. HTTPS (Public)

```
Protocol: TCP
Port: 443
Source: 0.0.0.0/0
Purpose: Dify web UI (demo requirement)
```

**Used By:** Dify web interface, API access over HTTPS

---

### 3. HTTP (Public)

```
Protocol: TCP
Port: 80
Source: 0.0.0.0/0
Purpose: Dify web UI (demo requirement)
```

**Used By:** Dify web interface, Streamlit dashboard proxy

---

### 4. Demo Service Ports (Presenter Only)

```
Protocol: TCP
Ports: 8000, 8001, 8002, 8443, 8501
Source: var.presenter_ip (Your public IP)
Purpose: Internal demo services
```

**Port Mappings:**
- **8000-8002:** Dify API, web services
- **8443:** Secure demo services
- **8501:** Streamlit dashboard (direct access)

**Security Note:** All restricted to presenter IP for demo isolation.

---

### 5. Internal VPC Communication

```
Protocol: TCP
Ports: 1-65535
Source: 172.16.0.0/16 (VPC CIDR)
Purpose: Internal service communication
```

**Used By:**
- Dify ↔ DWS (Data Warehouse)
- Dify ↔ DLI (Spark)
- ECS ↔ FunctionGraph
- All internal microservices

**Security Note:** Allows all TCP within VPC for demo flexibility.

---

## Egress Rules (Outbound Traffic)

### 1. HTTPS (External APIs)

```
Protocol: TCP
Port: 443
Destination: 0.0.0.0/0
Purpose: External API calls
```

**Used By:**
- Huawei Cloud SDK (API calls)
- DeepSeek MaaS (AI model)
- Langfuse (LLM observability)
- GitHub (Dify clone)

---

### 2. HTTP (Package Downloads)

```
Protocol: TCP
Port: 80
Destination: 0.0.0.0/0
Purpose: Package downloads, system updates
```

**Used By:**
- apt/yum package managers
- Docker image pulls
- Software updates

---

### 3. DNS (Domain Resolution)

```
Protocol: UDP
Port: 53
Destination: 0.0.0.0/0
Purpose: Domain name resolution
```

**DNS Servers:**
- Primary: 100.125.1.250 (Huawei Cloud DNS)
- Secondary: 8.8.8.8 (Google DNS)

---

### 4. DWS (Database Connection)

```
Protocol: TCP
Port: 8000
Destination: 0.0.0.0/0
Purpose: Data Warehouse Service connection
```

**Used By:** ECS instances connecting to DWS endpoint

---

### 5. NTP (Time Synchronization)

```
Protocol: UDP
Port: 123
Destination: 0.0.0.0/0
Purpose: Time synchronization
```

**Used By:** System time sync (cron logs, authentication)

---

## Network Architecture Diagram

```
┌─────────────────────────────────────────────────────────────────────────────┐
│                              INTERNET (0.0.0.0/0)                          │
└─────────────────────────────────────────────────────────────────────────────┘
                                    │
                                    │ HTTPS (443), HTTP (80)
                                    │ (Public Access)
                                    ▼
┌─────────────────────────────────────────────────────────────────────────────┐
│                        Huawei Cloud VPC: ayco-vpc                           │
│                           CIDR: 172.16.0.0/16                               │
│                                                                             │
│  ┌───────────────────────────────────────────────────────────────────────┐ │
│  │                     Security Group: ayco-sg                            │ │
│  │                                                                       │ │
│  │  INGRESS:                                                             │ │
│  │  • TCP 22     ← presenter_ip (SSH)                                   │ │
│  │  • TCP 443    ← 0.0.0.0/0 (HTTPS - Public)                            │ │
│  │  • TCP 80     ← 0.0.0.0/0 (HTTP - Public)                             │ │
│  │  • TCP 8501   ← presenter_ip (Streamlit)                             │ │
│  │  • TCP 1-65535 ← 172.16.0.0/16 (Internal)                             │ │
│  │                                                                       │ │
│  │  EGRESS:                                                              │ │
│  │  • TCP 443    → 0.0.0.0/0 (HTTPS)                                    │ │
│  │  • TCP 80     → 0.0.0.0/0 (HTTP)                                     │ │
│  │  • UDP 53     → 0.0.0.0/0 (DNS)                                      │ │
│  │  • TCP 8000   → 0.0.0.0/0 (DWS)                                      │ │
│  │  • UDP 123    → 0.0.0.0/0 (NTP)                                      │ │
│  └───────────────────────────────────────────────────────────────────────┘ │
│                                                                             │
│  ┌───────────────────┐      ┌───────────────────┐      ┌─────────────────┐ │
│  │   ECS: ayco-dify  │      │   ECS: ayco-web   │      │  Other ECS      │ │
│  │                   │      │                   │      │                 │ │
│  │  • Dify (80/443)  │◄────►│  • Landing Page   │      │  • DLI Agent    │ │
│  │  • Streamlit(8501)│      │  • Nginx Proxy    │      │  • CDM Agent    │ │
│  │  • Docker Compose│      │                   │      │                 │ │
│  └───────────────────┘      └───────────────────┘      └─────────────────┘ │
│           │                           │                           │         │
│           └───────────────────────────┴───────────────────────────┘         │
│                                   │                                         │
│                                   │ Internal TCP (1-65535)                  │
│                                   ▼                                         │
│  ┌───────────────────────────────────────────────────────────────────────┐ │
│  │                        Huawei Cloud Managed Services                   │ │
│  │                                                                       │ │
│  │  ┌─────────────┐  ┌─────────────┐  ┌─────────────┐  ┌─────────────┐ │ │
│  │  │     DWS     │  │     DLI     │  │  DataArts   │  │FunctionGraph│ │ │
│  │  │  (Port 8000)│  │  (Spark)    │  │  Studio     │  │   (Serverless)│ │ │
│  │  └─────────────┘  └─────────────┘  └─────────────┘  └─────────────┘ │ │
│  └───────────────────────────────────────────────────────────────────────┘ │
│                                                                             │
│  ┌───────────────────────────────────────────────────────────────────────┐ │
│  │                           Storage & Messaging                         │ │
│  │                                                                       │ │
│  │  ┌─────────────┐  ┌─────────────┐  ┌─────────────┐  ┌─────────────┐ │ │
│  │  │     OBS     │  │     KMS     │  │     IAM     │  │     EIP     │ │ │
│  │  │   (Buckets) │  │  (Encryption)│  │   (Roles)   │  │ (Public IPs)│ │ │
│  │  └─────────────┘  └─────────────┘  └─────────────┘  └─────────────┘ │ │
│  └───────────────────────────────────────────────────────────────────────┘ │
└─────────────────────────────────────────────────────────────────────────────┘
```

---

## Traffic Flow Examples

### 1. Presenter SSH Access

```
Presenter IP (TCP/22) → ayco-sg (allow if source == presenter_ip) → ECS SSH
```

### 2. Public HTTPS to Dify

```
Internet (TCP/443) → ayco-sg (allow 0.0.0.0/0) → ECS Dify Web UI
```

### 3. Internal Service Communication

```
ECS Dify (TCP/8000) → ayco-sg (allow VPC CIDR) → DWS Endpoint
```

### 4. External API Calls

```
ECS (HTTPS) → ayco-sg (egress allow TCP/443) → DeepSeek MaaS API
```

### 5. Streamlit Dashboard (Direct Access)

```
Presenter IP (TCP/8501) → ayco-sg (allow if source == presenter_ip) → Streamlit
```

---

## Security Considerations

### ✅ Current Hardening

1. **SSH restricted to presenter IP** - Prevents brute force attacks
2. **Demo ports restricted to presenter IP** - Limits attack surface
3. **Specific egress rules** - Only required protocols allowed outbound
4. **Internal VPC communication** - Services can communicate securely

### ⚠️ Demo Trade-offs

1. **HTTP/HTTPS public access** - Required for demo accessibility
2. **All TCP within VPC** - Simplified for demo setup (production would restrict)
3. **No Cloud Firewall** - Documented but not regional-available (see `terraform/modules/foundation/cfw.tf`)

### 🔄 Future Hardening (Post-Demo)

1. **Implement Cloud Firewall (CFW)** - IPS/IDS protection
2. **Restrict internal ports** - Specific ports instead of 1-65535
3. **Network ACLs** - Additional layer of security
4. **Bastion host** - Jump server for SSH access
5. **Private subnets** - Isolate backend services

---

## Firewall Decision Log

### Cloud Firewall (CFW) - Not Implemented

**Status:** Resource defined but commented out in `terraform/modules/foundation/cwf.tf`

**Reason:**
- CFW may not be available in `la-north-2` region at demo time
- Security groups provide sufficient protection for demo scope
- Would add complexity without significant benefit for 45-minute workshop

**Post-Demo Action:** Evaluate CFW availability and enable if production deployment planned.

---

## Troubleshooting

### "Connection Refused" on Port 8501

**Diagnosis:**
```bash
# Check if security group allows your IP
curl -v http://<ECS_IP>:8501

# Check presenter_ip variable
cd terraform && terraform output presenter_ip
```

**Fix:** Update `var.presenter_ip` in `terraform.tfvars` and re-apply:

```bash
terraform apply -var 'presenter_ip=<YOUR_NEW_IP>'
```

---

### DWS Connection Timeout

**Diagnosis:**
```bash
# Check egress rule for DWS port
# Verify DWS endpoint is accessible from ECS
ssh root@<ECS_IP> "nc -zv <DWS_ENDPOINT> 8000"
```

**Fix:** Ensure DWS security group allows inbound from `ayco-sg` (Huawei Cloud typically handles this automatically).

---

### External API Failures (DeepSeek, Langfuse)

**Diagnosis:**
```bash
# Test HTTPS egress from ECS
ssh root@<ECS_IP> "curl -v https://api.deepseek.com/v1/models"
```

**Fix:** Verify egress rule allows TCP/443 to 0.0.0.0/0 (should be present in `ayco-sg`).

---

## Terraform Reference

**Security Group Definition:** `terraform/modules/foundation/main.tf` (lines 31-113)

**Key Variables:**
- `var.vpc_cidr` - VPC CIDR block (default: 172.16.0.0/16)
- `var.presenter_ip` - Presenter's public IP (required)
- `var.subnet_cidr` - Subnet CIDR block (default: 172.16.1.0/24)

**Key Outputs:**
- `module.foundation.security_group_id` - Security Group resource ID
- `module.foundation.vpc_id` - VPC resource ID
- `module.foundation.subnet_id` - Subnet resource ID

---

## Appendix: Port Reference

| Port | Protocol | Direction | Access | Purpose |
|------|----------|-----------|--------|---------|
| 22 | TCP | Ingress | Presenter only | SSH administration |
| 80 | TCP | Ingress | Public | HTTP (Dify web) |
| 443 | TCP | Ingress | Public | HTTPS (Dify web) |
| 8000 | TCP | Ingress | Presenter only | Dify API |
| 8001 | TCP | Ingress | Presenter only | Demo service |
| 8002 | TCP | Ingress | Presenter only | Demo service |
| 8443 | TCP | Ingress | Presenter only | Secure demo service |
| 8501 | TCP | Ingress | Presenter only | Streamlit dashboard |
| 53 | UDP | Egress | All | DNS resolution |
| 123 | UDP | Egress | All | NTP time sync |
| 443 | TCP | Egress | All | HTTPS APIs |
| 80 | TCP | Egress | All | HTTP downloads |
| 8000 | TCP | Egress | All | DWS database |

---

**Document Version:** 1.0  
**Last Updated:** May 4, 2026  
**Maintained By:** Eduardo Hernández Cansino  
**Related Docs:** [`README.md`](../README.md), [`architecture.md`](./architecture.md), [`prep-checklist.md`](./prep-checklist.md)
