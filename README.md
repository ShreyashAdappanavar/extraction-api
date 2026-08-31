# Structured Extraction API

Takes raw, unstructured support ticket text and returns validated, schema-compliant JSON.

**Live demo:** `https://extraction-api-564896055817.us-central1.run.app/docs` (interactive API docs, no frontend yet)

## What it does

Support tickets in production are messy: missing details, contradictory statements, multiple issues raised in one message, no consistent structure. This API takes that raw text and extracts a fixed set of fields — customer name, issue category, urgency, order details, a summary — as validated JSON a downstream system can actually rely on.

## Architecture

```
Client → POST /extract → LLM call (DeepSeek, json_object mode) 
       → parse + validate against a Pydantic schema
       → on failure: retry with the specific validation error fed back to the model (max 3 attempts)
       → on success: return the validated ticket
       → on repeated failure: return a 500 with a clear error, not a silent bad response
```

## Tech stack

- FastAPI
- DeepSeek (LLM, OpenAI-SDK-compatible API)
- Pydantic (schema validation)
- Docker
- Google Cloud Run (deployed via GitHub-connected continuous deploy)

## Key features

- Nested schema validation (a `Ticket` contains an `OrderDetails` sub-object), not just flat fields
- Two-stage retry logic: JSON syntax failures and schema validation failures are treated as distinct problems, each with a different corrective message sent back to the model
- Strict enum-style fields (`Literal` types) for category/urgency/product, preventing inconsistent free-text values from silently passing validation
- Fails loudly and explicitly after 3 failed attempts, rather than returning a null or partial result

## Setup

```bash
git clone https://github.com/ShreyashAdappanavar/extraction-api.git
cd extraction-api
pip install -r requirements.txt
```

Create a `.env` file:
```
DEEPSEEK_API_KEY=your_key_here
FRONTEND_ORIGIN=http://localhost:3000
```

Run locally:
```bash
uvicorn app:app --reload
```

Or with Docker:
```bash
docker build -t extraction-api .
docker run -p 8080:8080 -e PORT=8080 --env-file .env extraction-api
```

## API usage example

**Request:**
```bash
curl -X POST https://extraction-api-564896055817.us-central1.run.app/extract \
  -H "Content-Type: application/json" \
  -d '{"ticket_str": "the app crashed 4 times today trying to submit a return for the ergonomic keyboard, ordered the wrong layout, eventually got a confirmation number but no email confirmation which normally comes within minutes"}'
```

**Response:**
```json
{
  "customer_name": null,
  "issue_category": "technical",
  "urgency": "High",
  "order": {
    "order_id": null,
    "product": "ergonomic_keyboard",
    "purchase_date": null
  },
  "summary": "Customer experienced repeated app crashes while trying to submit a return for an ergonomic keyboard. Eventually received a confirmation number but no email confirmation, and is unsure if the return was successfully submitted."
}
```

## A real tradeoff, stated honestly

The retry logic only helps with failures the model can actually correct by trying again — a formatting mistake, a wrong category guess. It cannot recover from failures caused by constraints outside the model's own awareness, like an output length limit cutting a response off mid-generation; retrying with the same instruction produces the same truncated result every time. This was confirmed directly by deliberately forcing that failure during testing, not assumed.

## License

MIT