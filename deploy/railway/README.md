Railway deployment guide
=======================

This folder contains a tiny template and instructions to deploy the `chatbot` Docker service to Railway.

Two ways to deploy on Railway:

1. Connect GitHub and let Railway build from your Dockerfile
2. Use the Railway CLI to deploy the image locally or from a registry

Quick steps (GitHub integration)
-------------------------------

1. Go to https://railway.app and create a new project.
2. Choose "Deploy from GitHub" and link your repository.
3. Railway will detect the `Dockerfile` in the repo and add a service. If it doesn't, choose "Custom" and point it at the Dockerfile.
4. In the Railway service settings, add the following environment variables (use the Railway UI -> Variables):

- SUPABASE_URL
- SUPABASE_SERVICE_KEY

5. Deploy — Railway will build your Dockerfile and run the container.

Quick steps (Railway CLI)
------------------------

1. Install Railway CLI: https://docs.railway.app/develop/cli
2. Run in your repo folder:

```bash
railway login
railway init  # creates a project and links it to your account
railway up    # builds and deploys the service
```

Setting variables with CLI:

```bash
railway variables set SUPABASE_URL=<value> SUPABASE_SERVICE_KEY=<value>
```

If you prefer to use a pre-built image (from GHCR or Docker Hub) instead of building on Railway, use the Railway UI to create a service from an image and paste the image URL (e.g. `ghcr.io/anishsingh1250/chatbot:latest`).
