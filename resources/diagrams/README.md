# Architecture Diagrams

This directory contains architecture diagrams for the course modules and labs.

## Diagrams

### Course Architecture Overview
The overall serverless architecture covered in the course:

```
                    ┌──────────────────────────────────────────────────┐
                    │                AWS Cloud                          │
                    │                                                  │
  Browser ─────────►│ CloudFront ──► S3 (Static Site)                  │
                    │                                                  │
  Mobile App ───────►│ API Gateway (HTTP API)                           │
                    │      │                                           │
                    │      ▼                                           │
                    │ Lambda Functions ◄─── Lambda Layers              │
                    │      │                                           │
                    │      ├──► DynamoDB                               │
                    │      │         │                                 │
                    │      │         └──► DynamoDB Streams             │
                    │      │                    │                      │
                    │      ├──► S3              ▼                      │
                    │      │             EventBridge                   │
                    │      │                    │                      │
                    │      └──► Step Functions  ▼                      │
                    │               │       SNS Topic                  │
                    │               │           │                      │
                    │               │     ┌─────┴──────┐              │
                    │               │     ▼            ▼              │
                    │               │  SQS Q1       SQS Q2            │
                    │               │     │            │              │
                    │               │     ▼            ▼              │
                    │               │  Lambda       Lambda            │
                    └──────────────────────────────────────────────────┘
                                    │
                              CloudWatch
                                 X-Ray
```

### Module-Specific Diagrams

For detailed diagrams of each module's architecture, refer to the module README files:

- [Module 1: Green IT Foundations](../../modules/01-green-it-and-serverless-foundations/README.md)
- [Module 4: Event-Driven Fan-Out](../../modules/04-event-driven-architecture/README.md)
- [Module 6: Step Functions Workflow](../../modules/06-step-functions/README.md)
- [Module 8: Capstone Architecture](../../modules/08-capstone-project/README.md)

## Tools for Creating Diagrams

- [draw.io / diagrams.net](https://app.diagrams.net/) – free, offline capable
- [AWS Architecture Icons](https://aws.amazon.com/architecture/icons/) – official icons
- [Excalidraw](https://excalidraw.com/) – hand-drawn style
- [Mermaid](https://mermaid.js.org/) – diagrams as code (used in this course)
