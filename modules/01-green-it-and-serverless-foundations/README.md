# Module 1 – Green IT & Serverless Foundations

**Duration:** 8 hours  
**Lab:** [Lab 01 – Carbon Footprint Calculator](../../labs/lab-01-carbon-footprint/README.md)

---

## Learning Objectives

After completing this module you will be able to:

- Define Green IT and explain why sustainability matters in cloud computing.
- Explain the serverless computing model and its key characteristics.
- Identify the primary AWS serverless services and their use cases.
- Calculate and compare the carbon footprint of serverless vs. traditional server workloads.

---

## 1. Green IT & Sustainable Cloud Computing

### 1.1 What Is Green IT?

Green IT (or Green Computing) refers to the design, manufacture, use, and disposal of computing resources in an environmentally responsible and eco-efficient manner.

**Key pillars:**
- **Energy efficiency** – reducing kWh consumed per unit of work.
- **Resource utilization** – maximising server usage to avoid idle capacity.
- **Carbon footprint** – net CO₂-equivalent emissions from compute workloads.
- **E-waste reduction** – minimising hardware churn.

### 1.2 Cloud vs. Traditional Data Centres

| Metric | On-Premises DC | Cloud (Hyperscaler) |
|--------|---------------|---------------------|
| Average PUE | 1.5 – 2.0 | 1.1 – 1.2 |
| Server utilisation | 5 – 15 % | 65 – 80 % |
| Renewable energy % | Varies | Up to 100 % (AWS goal) |
| Time to provision | Days – weeks | Seconds |

> **PUE (Power Usage Effectiveness)** = Total facility power / IT equipment power.  
> Lower is better. A PUE of 1.0 would be perfect efficiency.

### 1.3 AWS Sustainability Commitments

- **Carbon-neutral by 2040** (The Climate Pledge).
- **100 % renewable energy** by 2025 (achieved in 2023 globally).
- **Water stewardship** – AWS data centres in arid regions use closed-loop cooling.
- **AWS Customer Carbon Footprint Tool** – available in the Billing console.

---

## 2. Serverless Computing Fundamentals

### 2.1 Definition

> "Serverless is a cloud execution model where the cloud provider dynamically manages the allocation and provisioning of servers. A serverless application runs in stateless compute containers that are event-triggered, ephemeral, and fully managed by the cloud provider."

**Key characteristics (FIREM):**
- **F**unction as the unit of deployment
- **I**nvisible infrastructure management
- **R**eactive / event-driven
- **E**lastic scaling (zero to millions)
- **M**etered billing (pay-per-invocation)

### 2.2 Serverless vs. Other Compute Models

| Aspect | VMs (EC2) | Containers (ECS/EKS) | Serverless (Lambda) |
|--------|-----------|----------------------|---------------------|
| Unit of scale | VM | Container | Function |
| Provisioning | Minutes | Seconds | Milliseconds |
| Idle cost | Full VM cost | Partial (Fargate) | Zero |
| Max run time | Unlimited | Unlimited | 15 minutes |
| State | Stateful | Stateful | Stateless (by default) |
| Cold start | Boot time | Pull + start | ~ms to seconds |

### 2.3 When to Use Serverless

**Good fit:**
- Irregular, unpredictable, or spiky traffic.
- Event-driven pipelines (uploads, database changes, messages).
- APIs with variable load.
- Scheduled / cron jobs.
- Short-lived data transformations.

**Poor fit:**
- Long-running CPU-intensive batch jobs (> 15 min).
- Workloads requiring persistent connections (websockets — use API Gateway WebSocket APIs).
- Applications requiring a specific OS or kernel configuration.

---

## 3. AWS Serverless Services Overview

### 3.1 Compute

| Service | Purpose |
|---------|---------|
| **AWS Lambda** | Run code without provisioning servers |
| **AWS Fargate** | Serverless container execution |

### 3.2 Integration & Messaging

| Service | Purpose |
|---------|---------|
| **Amazon API Gateway** | Managed HTTP/WebSocket API endpoints |
| **Amazon SNS** | Pub/Sub messaging |
| **Amazon SQS** | Managed message queues |
| **Amazon EventBridge** | Event bus for SaaS and AWS services |

### 3.3 Data

| Service | Purpose |
|---------|---------|
| **Amazon DynamoDB** | Serverless NoSQL key-value/document store |
| **Amazon S3** | Object storage + event source |
| **Amazon Aurora Serverless v2** | Auto-scaling relational database |

### 3.4 Orchestration

| Service | Purpose |
|---------|---------|
| **AWS Step Functions** | Visual serverless workflow orchestration |

### 3.5 Developer Tools

| Service | Purpose |
|---------|---------|
| **AWS SAM** | Serverless Application Model (IaC) |
| **AWS CDK** | Cloud Development Kit (IaC with code) |

---

## 4. AWS Global Infrastructure

### 4.1 Regions & Availability Zones

- **Region** – geographically isolated collection of data centres.  
- **Availability Zone (AZ)** – one or more discrete data centres within a region with redundant power, networking, and connectivity.
- **Edge Location** – CloudFront / Lambda@Edge node.

### 4.2 Choosing a Region

Factors to consider:
1. **Data residency / compliance** (GDPR, etc.)
2. **Latency** to end users
3. **Service availability** (not all services in all regions)
4. **Carbon intensity** of the regional power grid

```
Greenest AWS regions (based on renewable energy commitments):
  - eu-west-1 (Ireland) – 100% renewable
  - us-west-2 (Oregon) – 100% renewable
  - eu-north-1 (Stockholm) – 100% renewable
```
> **Note:** Check the [AWS Sustainability page](https://sustainability.aboutamazon.com/) for the latest figures as AWS continuously expands its renewable energy portfolio.

---

## 5. Hands-On: Lab 01

➡️ [Lab 01 – Carbon Footprint Calculator](../../labs/lab-01-carbon-footprint/README.md)

**What you'll build:**  
A Python Lambda function that queries the AWS Carbon Footprint API (or simulates the calculation) and compares the CO₂ emissions of running a workload as:
- A Lambda function
- An EC2 t3.micro (24/7)
- An EC2 m5.large (24/7)

---

## 6. Key Takeaways

- Serverless reduces idle compute → lower energy use → smaller carbon footprint.
- AWS hyperscale achieves PUE ≈ 1.1 vs. enterprise DC average of 1.6+.
- Lambda's pay-per-ms billing directly maps to energy consumption.
- Choose AWS regions with high renewable energy percentage for greener workloads.

---

## 📖 Further Reading

- [AWS Sustainability Pillar (Well-Architected)](https://docs.aws.amazon.com/wellarchitected/latest/sustainability-pillar/welcome.html)
- [AWS Customer Carbon Footprint Tool](https://aws.amazon.com/aws-cost-management/aws-customer-carbon-footprint-tool/)
- [The Climate Pledge](https://www.theclimatepledge.com/)
- [Green Software Foundation](https://greensoftware.foundation/)

---

*Next Module → [Module 2: AWS Lambda Deep Dive](../02-aws-lambda/README.md)*
