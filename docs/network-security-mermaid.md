# AYCO Network Security - Mermaid Diagrams

This document contains Mermaid diagrams for the AYCO network architecture. These can be rendered in Markdown viewers that support Mermaid (GitHub, GitLab, Notion, etc.).

---

## Network Architecture Overview

```mermaid
graph TB
    Internet[Internet<br/>0.0.0.0/0]

    subgraph VPC["Huawei Cloud VPC: ayco-vpc<br/>CIDR: 172.16.0.0/16"]
        SG["Security Group: ayco-sg"]

        subgraph ECS["ECS Instances"]
            Dify["ECS: ayco-dify<br/>Dify + Streamlit<br/>Ports: 80, 443, 8501"]
            Web["ECS: ayco-web<br/>Landing Page<br/>Port: 80"]
        end

        subgraph Managed["Managed Services"]
            DWS["DWS<br/>Data Warehouse<br/>Port: 8000"]
            DLI["DLI<br/>Spark SQL"]
            DataArts["DataArts<br/>Studio"]
            FG["FunctionGraph<br/>Serverless"]
        end

        subgraph Storage["Storage & Security"]
            OBS["OBS<br/>Object Storage"]
            KMS["KMS<br/>Encryption"]
            IAM["IAM<br/>Roles"]
        end
    end

    Internet -->|HTTPS 443<br/>HTTP 80| SG
    SG --> Dify
    SG --> Web

    Dify -.->|TCP 1-65535<br/>Internal| DWS
    Dify -.->|TCP 1-65535<br/>Internal| DLI
    Dify -.->|TCP 1-65535<br/>Internal| DataArts
    Dify -.->|TCP 1-65535<br/>Internal| FG

    Dify -->|HTTPS 443<br/>Egress| Internet
    Dify -->|HTTP 80<br/>Egress| Internet

    style Internet fill:#f9f9f9
    style SG fill:#ffeb99
    style Dify fill:#99ccff
    style Web fill:#99ccff
    style DWS fill:#99ff99
    style DLI fill:#99ff99
    style DataArts fill:#99ff99
    style FG fill:#99ff99
```

---

## Security Group Rules

### Ingress Rules

```mermaid
graph LR
    subgraph Ingress["Ingress Rules (Inbound)"]
        SSH["TCP 22<br/>← presenter_ip<br/>SSH Access"]
        HTTPS["TCP 443<br/>← 0.0.0.0/0<br/>HTTPS Public"]
        HTTP["TCP 80<br/>← 0.0.0.0/0<br/>HTTP Public"]
        Demo["TCP 8501<br/>← presenter_ip<br/>Streamlit"]
        Internal["TCP 1-65535<br/>← 172.16.0.0/16<br/>Internal VPC"]
    end

    subgraph Resources["Protected Resources"]
        Dify["ECS ayco-dify"]
        Web["ECS ayco-web"]
    end

    SSH --> Dify
    HTTPS --> Dify
    HTTPS --> Web
    HTTP --> Dify
    HTTP --> Web
    Demo --> Dify
    Internal --> Dify
    Internal --> Web

    style SSH fill:#ffcccc
    style HTTPS fill:#ccffcc
    style HTTP fill:#ccffcc
    style Demo fill:#ffcccc
    style Internal fill:#ffffcc
```

### Egress Rules

```mermaid
graph LR
    subgraph Resources["ECS Instances"]
        Dify["ayco-dify"]
        Web["ayco-web"]
    end

    subgraph Egress["Egress Rules (Outbound)"]
        HTTPS_out["TCP 443<br/>→ 0.0.0.0/0<br/>External APIs"]
        HTTP_out["TCP 80<br/>→ 0.0.0.0/0<br/>Downloads"]
        DNS["UDP 53<br/>→ 0.0.0.0/0<br/>DNS Resolution"]
        DWS_out["TCP 8000<br/>→ 0.0.0.0/0<br/>DWS Database"]
        NTP["UDP 123<br/>→ 0.0.0.0/0<br/>Time Sync"]
    end

    subgraph External["External Services"]
        MaaS["DeepSeek MaaS<br/>AI Model"]
        Langfuse["Langfuse<br/>Observability"]
        GitHub["GitHub<br/>Dify Repo"]
        Docker["Docker Hub<br/>Images"]
    end

    Dify --> HTTPS_out
    Dify --> HTTP_out
    Dify --> DNS
    Dify --> DWS_out
    Dify --> NTP

    Web --> HTTPS_out
    Web --> HTTP_out
    Web --> DNS
    Web --> NTP

    HTTPS_out --> MaaS
    HTTPS_out --> Langfuse
    HTTP_out --> GitHub
    HTTP_out --> Docker

    style HTTPS_out fill:#ccffcc
    style HTTP_out fill:#ccffcc
    style DNS fill:#ccccff
    style DWS_out fill:#ffffcc
    style NTP fill:#ccccff
```

---

## Traffic Flow Examples

### 1. Presenter Access to Streamlit Dashboard

```mermaid
sequenceDiagram
    participant P as Presenter<br/>(presenter_ip)
    participant SG as ayco-sg<br/>(Security Group)
    participant Dify as ECS ayco-dify<br/>(Streamlit:8501)

    P->>SG: TCP 8501
    SG->>SG: Check: Source == presenter_ip?
    SG->>Dify: Allow traffic
    Dify->>P: Streamlit Dashboard

    Note over SG: Rule: TCP 8501 from presenter_ip
```

### 2. Public HTTPS to Dify Web UI

```mermaid
sequenceDiagram
    participant U as Internet User<br/>(0.0.0.0/0)
    participant SG as ayco-sg<br/>(Security Group)
    participant Dify as ECS ayco-dify<br/>(HTTPS:443)

    U->>SG: TCP 443
    SG->>SG: Check: Port 443 allowed?
    SG->>Dify: Allow traffic
    Dify->>U: Dify Web UI

    Note over SG: Rule: TCP 443 from 0.0.0.0/0
```

### 3. Internal Service Communication (Dify ↔ DWS)

```mermaid
sequenceDiagram
    participant Dify as ECS ayco-dify<br/>(172.16.1.x)
    participant SG as ayco-sg<br/>(Security Group)
    participant DWS as DWS<br/>(Port 8000)

    Dify->>SG: TCP 8000 to VPC CIDR
    SG->>SG: Check: Source in 172.16.0.0/16?
    SG->>DWS: Allow traffic
    DWS->>Dify: Query Response

    Note over SG: Rule: TCP 1-65535 from 172.16.0.0/16
```

### 4. External API Call (Dify → DeepSeek MaaS)

```mermaid
sequenceDiagram
    participant Dify as ECS ayco-dify
    participant SG as ayco-sg<br/>(Egress)
    participant MaaS as DeepSeek MaaS<br/>(api-ap-southeast-1)

    Dify->>SG: HTTPS Request (TCP 443)
    SG->>SG: Check: Egress TCP 443 allowed?
    SG->>MaaS: Forward Request
    MaaS->>SG: Response
    SG->>Dify: Return Response

    Note over SG: Rule: TCP 443 to 0.0.0.0/0 (Egress)
```

---

## Security Group Decision Tree

```mermaid
graph TD
    Start["Incoming Packet"]
    CheckSG["Is it for ayco-sg?"]

    CheckSSH{"Port 22?"}
    CheckDemo{"Port 8501?"}
    CheckHTTPS{"Port 443?"}
    CheckHTTP{"Port 80?"}
    CheckInternal{"Source in<br/>172.16.0.0/16?"}

    AllowSSH["Allow<br/>(SSH Admin)"]
    AllowDemo["Allow<br/>(Streamlit)"]
    AllowHTTPS["Allow<br/>(Public HTTPS)"]
    AllowHTTP["Allow<br/>(Public HTTP)"]
    AllowInternal["Allow<br/>(VPC Internal)"]
    Deny["Deny"]

    Start --> CheckSG
    CheckSG -->|No| Deny
    CheckSG -->|Yes| CheckSSH

    CheckSSH -->|Yes| CheckPresenterIP
    CheckSSH -->|No| CheckDemo

    CheckDemo -->|Yes| CheckPresenterIP
    CheckDemo -->|No| CheckHTTPS

    CheckHTTPS -->|Yes| AllowHTTPS
    CheckHTTPS -->|No| CheckHTTP

    CheckHTTP -->|Yes| AllowHTTP
    CheckHTTP -->|No| CheckInternal

    CheckInternal -->|Yes| AllowInternal
    CheckInternal -->|No| Deny

    CheckPresenterIP{"Source ==<br/>presenter_ip?"}
    CheckPresenterIP -->|Yes| AllowSSH
    CheckPresenterIP -->|Yes| AllowDemo
    CheckPresenterIP -->|No| Deny

    style AllowSSH fill:#ccffcc
    style AllowDemo fill:#ccffcc
    style AllowHTTPS fill:#ccffcc
    style AllowHTTP fill:#ccffcc
    style AllowInternal fill:#ccffcc
    style Deny fill:#ffcccc
```

---

## Port Access Matrix

| Port | Protocol | Direction | Source | Target | Purpose | Access Level |
|------|----------|-----------|--------|--------|---------|--------------|
| 22 | TCP | Ingress | presenter_ip | ECS | SSH | 🔒 Restricted |
| 80 | TCP | Ingress | 0.0.0.0/0 | ECS | HTTP | 🌐 Public |
| 443 | TCP | Ingress | 0.0.0.0/0 | ECS | HTTPS | 🌐 Public |
| 8501 | TCP | Ingress | presenter_ip | ECS | Streamlit | 🔒 Restricted |
| 1-65535 | TCP | Ingress | 172.16.0.0/16 | ECS | Internal | 🔒 VPC Only |
| 443 | TCP | Egress | ECS | 0.0.0.0/0 | APIs | 🌐 All |
| 80 | TCP | Egress | ECS | 0.0.0.0/0 | Downloads | 🌐 All |
| 53 | UDP | Egress | ECS | 0.0.0.0/0 | DNS | 🌐 All |
| 8000 | TCP | Egress | ECS | 0.0.0.0/0 | DWS | 🌐 All |
| 123 | UDP | Egress | ECS | 0.0.0.0/0 | NTP | 🌐 All |

---

**Related Documentation:**
- [`network-security.md`](./network-security.md) - Detailed security group reference
- [`architecture.md`](./architecture.md) - Overall system architecture
- [`README.md`](../README.md) - Project overview

---

**Note:** These diagrams use Mermaid syntax. View them in:
- GitHub (native rendering)
- GitLab (native rendering)
- Notion (with Mermaid plugin)
- VS Code (with Mermaid plugin)
- Online: https://mermaid.live
