# Lab 04 – REST API with API Gateway

**Module:** [Module 3 – API Gateway & REST/HTTP APIs](../../modules/03-api-gateway/README.md)  
**Duration:** ~90 minutes  
**Services:** API Gateway (HTTP API), Lambda, DynamoDB

---

## Objective

Build a fully functional CRUD REST API for a "todo" application:

| Method | Path | Description |
|--------|------|-------------|
| `GET` | `/todos` | List all todos |
| `POST` | `/todos` | Create a new todo |
| `GET` | `/todos/{id}` | Get a single todo |
| `PUT` | `/todos/{id}` | Update a todo |
| `DELETE` | `/todos/{id}` | Delete a todo |

---

## Directory Structure

```
lab-04-api-gateway-rest/
├── README.md
├── template.yaml
├── src/
│   └── todos/
│       ├── app.py           ← Single Lambda handling all routes
│       └── requirements.txt
└── events/
    ├── list.json
    ├── create.json
    ├── get.json
    ├── update.json
    └── delete.json
```

---

## Step 1 – Deploy

```bash
cd labs/lab-04-api-gateway-rest
sam build
sam deploy --guided
# Stack name: api-gateway-lab
```

Note the `ApiUrl` output – you'll use this for testing.

---

## Step 2 – Test with curl

```bash
# Set the API URL from the stack output
API_URL=$(aws cloudformation describe-stacks \
  --stack-name api-gateway-lab \
  --query 'Stacks[0].Outputs[?OutputKey==`ApiUrl`].OutputValue' \
  --output text)

echo "API URL: $API_URL"

# Create a todo
curl -X POST "$API_URL/todos" \
  -H "Content-Type: application/json" \
  -d '{"title": "Learn Lambda", "done": false}'

# List all todos
curl "$API_URL/todos"

# Get specific todo (replace {id} with actual ID from create response)
curl "$API_URL/todos/{id}"

# Update a todo
curl -X PUT "$API_URL/todos/{id}" \
  -H "Content-Type: application/json" \
  -d '{"done": true}'

# Delete a todo
curl -X DELETE "$API_URL/todos/{id}"
```

---

## Step 3 – Explore the DynamoDB Table

```bash
aws dynamodb scan --table-name todos-lab --output table
```

Notice the single-table design with `PK = TODO#{id}` and `SK = METADATA`.

---

## Step 4 – Test Input Validation

Try creating a todo without a `title`:

```bash
curl -X POST "$API_URL/todos" \
  -H "Content-Type: application/json" \
  -d '{"done": false}'
```

You should receive a `400 Bad Request` response.

---

## Bonus – Add Authentication

1. Create a Cognito User Pool and User Pool Client.
2. Add a JWT Authorizer to the HTTP API in `template.yaml`.
3. Test that unauthenticated requests are rejected.

---

## Cleanup

```bash
sam delete --stack-name api-gateway-lab
```
