# Module 3 – API Gateway & REST/HTTP APIs

**Duration:** 8 hours  
**Lab:** [Lab 04 – REST API with API Gateway](../../labs/lab-04-api-gateway-rest/README.md)

---

## Learning Objectives

After completing this module you will be able to:

- Differentiate between REST APIs, HTTP APIs, and WebSocket APIs.
- Build and deploy a CRUD API backed by Lambda.
- Configure request validation, models, and mappings.
- Implement authentication using Lambda Authorizers and Amazon Cognito.
- Apply throttling, caching, and usage plans to protect your API.
- Enable CORS for browser-based clients.

---

## 1. API Gateway Products

Amazon API Gateway offers three API types:

| Feature | REST API | HTTP API | WebSocket API |
|---------|----------|----------|---------------|
| Protocols | HTTP/S | HTTP/S | WebSocket |
| Latency | Medium | Low (~60% faster) | N/A |
| Price | Higher | ~70% cheaper | Per message |
| Features | Full (models, caching, usage plans) | Subset | Bi-directional |
| JWT Authorizer | Via Lambda | Native | Via Lambda |
| Recommended for | Feature-rich enterprise APIs | Most modern APIs | Real-time apps |

> **Recommendation:** Use **HTTP API** for new projects unless you need REST API-specific features (e.g., API keys / usage plans, edge-optimised endpoint, request/response transformations).

---

## 2. REST API Concepts

### 2.1 Resources & Methods

A REST API is a tree of **resources** (URL paths) each with one or more **methods** (GET, POST, PUT, DELETE, PATCH, OPTIONS).

```
/
└── /items                ← Resource
    ├── GET               ← Method: list all items
    ├── POST              ← Method: create item
    └── /{itemId}         ← Resource (path parameter)
        ├── GET           ← Method: get one item
        ├── PUT           ← Method: update item
        └── DELETE        ← Method: delete item
```

### 2.2 Integration Types

| Type | Description |
|------|-------------|
| **Lambda Proxy** | Raw event forwarded to Lambda; Lambda returns full response |
| **Lambda** | API GW transforms request/response (mapping templates) |
| **HTTP** | Proxy to any HTTP endpoint |
| **AWS Service** | Direct integration with AWS services (e.g., DynamoDB, SQS) |
| **Mock** | Returns a static response without calling a backend |

**Lambda Proxy** is the most common and simplest integration — use it by default.

### 2.3 Lambda Proxy Request/Response Contract

**Request (event):**
```json
{
  "resource": "/items/{itemId}",
  "path": "/items/42",
  "httpMethod": "GET",
  "headers": { "Accept": "application/json" },
  "pathParameters": { "itemId": "42" },
  "queryStringParameters": { "include": "details" },
  "body": null,
  "isBase64Encoded": false
}
```

**Response (from Lambda):**
```json
{
  "statusCode": 200,
  "headers": {
    "Content-Type": "application/json",
    "Access-Control-Allow-Origin": "*"
  },
  "body": "{\"itemId\": \"42\", \"name\": \"Widget\"}"
}
```

---

## 3. HTTP API (v2)

### 3.1 Key Differences from REST API

- Simplified payload format (Payload Format Version 2.0).
- Native JWT authorizer (no Lambda required for Cognito / OIDC).
- Auto-deploy stages.
- Built-in CORS configuration.

### 3.2 Payload Format Version 2.0

```json
{
  "version": "2.0",
  "routeKey": "GET /items/{itemId}",
  "rawPath": "/items/42",
  "rawQueryString": "include=details",
  "headers": { "accept": "application/json" },
  "pathParameters": { "itemId": "42" },
  "queryStringParameters": { "include": "details" },
  "body": null,
  "isBase64Encoded": false,
  "requestContext": {
    "accountId": "123456789012",
    "requestId": "abc123",
    "http": { "method": "GET", "path": "/items/42" }
  }
}
```

---

## 4. Authentication & Authorization

### 4.1 IAM Authorization

Use AWS Signature Version 4 — best for service-to-service communication.

```bash
aws apigateway test-invoke-method \
  --rest-api-id abc123 \
  --resource-id def456 \
  --http-method GET
```

### 4.2 Lambda Authorizer (Custom Authorizer)

A Lambda function that validates a token and returns an IAM policy.

```python
def handler(event, context):
    token = event["authorizationToken"]
    # Validate the token (JWT, API key, OAuth, etc.)
    if is_valid(token):
        return generate_policy("user", "Allow", event["methodArn"])
    return generate_policy("user", "Deny", event["methodArn"])

def generate_policy(principal_id, effect, resource):
    return {
        "principalId": principal_id,
        "policyDocument": {
            "Version": "2012-10-17",
            "Statement": [{"Action": "execute-api:Invoke", "Effect": effect, "Resource": resource}]
        },
        "context": {"userId": principal_id}  # passed to backend Lambda
    }
```

### 4.3 Amazon Cognito User Pools

1. Create a Cognito User Pool.
2. Configure the REST API authorizer to use the User Pool.
3. Clients obtain a JWT token from Cognito and pass it in the `Authorization` header.
4. API Gateway validates the token without invoking a Lambda.

### 4.4 JWT Authorizer (HTTP API)

```yaml
# SAM template
Auth:
  Authorizers:
    MyCognitoAuthorizer:
      JwtConfiguration:
        issuer: !Sub https://cognito-idp.${AWS::Region}.amazonaws.com/${UserPool}
        audience:
          - !Ref UserPoolClient
  DefaultAuthorizer: MyCognitoAuthorizer
```

---

## 5. Request Validation & Models

### 5.1 Request Validators (REST API)

Enable automatic validation of:
- **Request body** – validated against a JSON Schema model.
- **Request parameters** – required query strings and headers.

```yaml
RequestValidator:
  Type: AWS::ApiGateway::RequestValidator
  Properties:
    RestApiId: !Ref MyApi
    ValidateRequestBody: true
    ValidateRequestParameters: true
```

### 5.2 JSON Schema Model (REST API)

```json
{
  "$schema": "http://json-schema.org/draft-04/schema#",
  "title": "CreateItem",
  "type": "object",
  "required": ["name", "price"],
  "properties": {
    "name": { "type": "string", "minLength": 1 },
    "price": { "type": "number", "minimum": 0 }
  }
}
```

---

## 6. Throttling, Caching & Usage Plans

### 6.1 Throttling

API Gateway applies throttling at two levels:

| Level | Default Limit | Configurable |
|-------|--------------|--------------|
| Account (AWS-wide) | 10,000 req/s, 5,000 burst | Yes (support case) |
| Stage | Inherited | Yes (stage settings) |
| Method | Inherited | Yes (per-method override) |
| Usage plan | Custom | Yes |

### 6.2 Response Caching (REST API Only)

Enable caching per stage to reduce Lambda invocations:

```yaml
CacheClusterEnabled: true
CacheClusterSize: "0.5"  # 0.5 GB
MethodSettings:
  - ResourcePath: /items
    HttpMethod: GET
    CachingEnabled: true
    CacheTtlInSeconds: 300
```

### 6.3 Usage Plans & API Keys

```yaml
MyUsagePlan:
  Type: AWS::ApiGateway::UsagePlan
  Properties:
    Throttle:
      RateLimit: 100      # req/s
      BurstLimit: 200
    Quota:
      Limit: 10000        # per period
      Period: MONTH
```

---

## 7. CORS

Cross-Origin Resource Sharing must be enabled for browser clients on a different origin.

### 7.1 HTTP API (simple)

```yaml
CorsConfiguration:
  AllowHeaders:
    - Content-Type
    - Authorization
  AllowMethods:
    - GET
    - POST
    - OPTIONS
  AllowOrigins:
    - https://myapp.example.com
  MaxAge: 600
```

### 7.2 REST API (Lambda Proxy)

Your Lambda **must return CORS headers** in every response:

```python
CORS_HEADERS = {
    "Access-Control-Allow-Origin": "https://myapp.example.com",
    "Access-Control-Allow-Headers": "Content-Type,Authorization",
    "Access-Control-Allow-Methods": "GET,POST,PUT,DELETE,OPTIONS",
}

def handler(event, context):
    return {
        "statusCode": 200,
        "headers": CORS_HEADERS,
        "body": json.dumps({"message": "ok"}),
    }
```

---

## 8. Stages & Deployments

A **stage** is a named reference to a deployment (e.g., `dev`, `staging`, `prod`).

```bash
# Deploy using SAM
sam deploy --parameter-overrides StageName=prod

# Using AWS CLI
aws apigateway create-deployment \
  --rest-api-id abc123 \
  --stage-name prod
```

### Stage Variables

```bash
# In mapping template or Lambda env variable
${stageVariables.tableName}
```

---

## 9. Hands-On: Lab 04

➡️ [Lab 04 – REST API with API Gateway](../../labs/lab-04-api-gateway-rest/README.md)

**What you'll build:**  
A fully functional CRUD REST API for a "todo" application:
- `GET /todos` – list all todos
- `POST /todos` – create a new todo
- `GET /todos/{id}` – get a single todo
- `PUT /todos/{id}` – update a todo
- `DELETE /todos/{id}` – delete a todo

Backed by Lambda functions and DynamoDB, secured with a Cognito JWT Authorizer.

---

## 10. Key Takeaways

- HTTP API is the recommended choice for most use cases – faster and cheaper.
- REST API is necessary for advanced features like request/response transformation, caching, and usage plans.
- Always validate inputs at the API layer to protect your Lambda functions.
- Use Cognito or Lambda Authorizers to authenticate API requests.
- Return CORS headers from your Lambda for browser-based clients.

---

## 📖 Further Reading

- [API Gateway Developer Guide](https://docs.aws.amazon.com/apigateway/latest/developerguide/welcome.html)
- [Choosing between REST and HTTP APIs](https://docs.aws.amazon.com/apigateway/latest/developerguide/http-api-vs-rest.html)
- [Building serverless APIs](https://docs.aws.amazon.com/apigateway/latest/developerguide/http-api-develop.html)

---

*Previous Module → [Module 2: AWS Lambda](../02-aws-lambda/README.md)*  
*Next Module → [Module 4: Event-Driven Architecture](../04-event-driven-architecture/README.md)*
