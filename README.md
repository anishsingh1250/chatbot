# chatbot

This repository contains a Python FastAPI service that powers a small health chatbot. The service exposes the following endpoints:

- `GET /` — health check returning `{ "status": "API is running." }`
- `POST /search` — search endpoint used by the chatbot frontend (expects JSON body `{ "query": "..." }`).

The project uses `sentence-transformers` to generate embeddings and `supabase` as a vector store. Environment variables (stored in `.env` locally or in your hosting secret manager) expected:

- SUPABASE_URL
- SUPABASE_SERVICE_KEY

## Building and running locally (Docker)

The repository includes a `Dockerfile` so you can build and run the service in a container.

```powershell
docker build -t chatbot:local .
docker run --rm -p 8000:8000 --env-file .env chatbot:local
# then in another shell
curl http://localhost:8000/
```

## Deploying the Docker image

Important: `sentence-transformers` and `torch` produce large images and long build times. For production, choose a host with sufficient RAM, or consider using a hosted embeddings API instead of loading the full model in-process.

### Render (Docker)

1. Create a Render account and a new "Web Service".
2. Connect your GitHub repo and choose the `main` branch.
3. Choose to deploy from Dockerfile, set the port to `8000`.
4. Add secrets in Render's dashboard (e.g., `SUPABASE_URL`, `SUPABASE_SERVICE_KEY`).
5. Deploy — Render builds the image and runs it.

### Fly.io

1. Install `flyctl` (https://fly.io/docs/hands-on/install-flyctl/).
2. Launch and deploy with your Dockerfile:

```bash
fly launch --name chatbot --dockerfile Dockerfile
fly secrets set SUPABASE_URL=... SUPABASE_SERVICE_KEY=...
fly deploy
```

### Railway

1. Create a Railway project and connect your GitHub repo.
2. Add a service that deploys from your Dockerfile (Railway can detect it).
3. Set environment variables in Railway's dashboard.
4. Deploy — Railway will build and run the container.

See `deploy/railway/` for a small `service.template.json` and a CLI guide to deploy via the Railway CLI.

## Secrets and notes

- Never commit `.env` to source control. Use the hosting platform secrets to store `SUPABASE_URL` and `SUPABASE_SERVICE_KEY`.
- If builds are slow on CI or Render, I can provide an optimized `requirements.txt` and Dockerfile that uses CPU-only wheels or a smaller base image.

If you want example provider configs (e.g., `render.yaml`, `fly.toml`, or Railway service files), tell me which provider and I will add them.