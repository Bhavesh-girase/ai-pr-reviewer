# RepoVela deployment runbook

This repository is prepared for a single Ubuntu EC2 host running the API in Docker Compose, with the React frontend deployed separately to Vercel. The API is reachable only through Caddy over HTTPS; port 8000 is not published publicly.

## Before deploying

- Use an EC2 instance with **at least 4 GiB RAM**; 8 GiB is safer for repository indexing and AI reviews. This backend loads CPU PyTorch, an embedding model, and a cross-encoder. A 1 GiB micro instance is not a reliable target.
- Give the VM at least **30 GiB of EBS storage** and monitor disk usage as repositories and model caches accumulate. Docker data is kept in a named volume on the VM's disk.
- Set up a domain/subdomain for the API, for example `api.example.com`, and point its DNS A record to the EC2 public IP. Caddy obtains and renews the HTTPS certificate automatically.
- In the EC2 security group, allow inbound TCP 80 and 443. Allow SSH (TCP 22) only from your IP. Do not open port 8000 to the internet.
- Create or select the Supabase project and ensure all required, unapplied SQL files in `supabase/migrations/` have been applied in filename order. Do not blindly reapply migrations already installed on an existing project.

## Backend environment

On the EC2 host, create the `.env` file from the example and keep it private:

```bash
cp -n .env.example .env
chmod 600 .env
```

Set the real values in `.env`:

- `SUPABASE_URL` and `SUPABASE_SERVICE_ROLE_KEY` from Supabase. The service-role key is backend-only; never add it to Vercel or commit it. `SUPABASE_KEY` is accepted by the code as a legacy fallback but is not needed when the service-role variable is set.
- `SUPABASE_JWT_SECRET` from the Supabase project settings.
- `ENCRYPTION_KEY`: generate a stable key with `python -c "import base64, secrets; print(base64.urlsafe_b64encode(secrets.token_bytes(32)).decode())"`. Keep a secure backup; replacing it later prevents decrypting credentials already encrypted by the app.
- `GEMINI_API_KEY` from Google AI Studio.
- `API_DOMAIN`: the API hostname only, e.g. `api.example.com` (no scheme or path).
- `GITHUB_WEBHOOK_BASE_URL`: the complete public API URL, e.g. `https://api.example.com`.
- `CORS_ALLOWED_ORIGINS`: the exact Vercel site origin, e.g. `https://repovela.vercel.app` (no trailing slash; add a custom frontend domain too if used).
- Keep `ENABLE_API_DOCS=false`. Start with `REVIEW_WORKER_CONCURRENCY=1` on a small host.

## Deploy the backend

Install Git, Docker Engine, and the Docker Compose plugin on the EC2 host, then clone the repository and configure `.env` as above. Start the production stack from the repository root:

```bash
docker compose --profile production up -d --build
docker compose ps
docker compose logs -f backend caddy
```

The first build and first model download can take several minutes. Check `https://api.example.com/health`; it should return `{"status":"healthy"}`. The backend data and model cache are persisted in the `app_data` Docker volume, while Caddy's certificates are persisted in its own volumes. A regular `docker compose down` preserves these volumes; **do not use `docker compose down -v`** unless you intend to delete the stored data and certificates. Back up the EC2 EBS volume regularly.

For code updates, pull the repository and rebuild/restart:

```bash
git pull --ff-only
docker compose --profile production up -d --build
```

## Deploy the frontend to Vercel

Set these Vercel project environment variables, then trigger a new deployment:

- `VITE_API_BASE_URL=https://api.example.com`
- `VITE_SUPABASE_URL` — the Supabase project URL
- `VITE_SUPABASE_ANON_KEY` — the Supabase public/anon key (not the service-role key)

The frontend calls the API directly using `VITE_API_BASE_URL`; `frontend/vercel.json` only provides the SPA route fallback and no longer contains the old backend IP.

## Local Docker smoke test

Copy and fill in the root `.env`, then run the API on localhost without starting the production HTTPS proxy:

```bash
docker compose up --build
```

The API is available at `http://localhost:8000/health`. Port 8000 is bound to loopback only; Caddy reaches the backend over Docker's internal network. Stop the local stack with `Ctrl+C` or `docker compose down`.

## Important operational notes

- The app's repositories, Chroma indexes, local files, and Hugging Face model cache live on the EC2 disk, not in Git or Supabase. Stopping the EC2 instance keeps the EBS data, but EBS storage can continue to incur charges. Terminating the instance may delete its root disk unless its deletion behavior is changed or the data is backed up.
- A stopped EC2 instance is not reachable. If it receives a new public IP after restart, update DNS and the Vercel `VITE_API_BASE_URL`, or use a stable address.
- Keep one API process on this host. The review worker runs inside that process; the configured queue concurrency controls review jobs.
- Never commit `.env`, frontend secrets, GitHub tokens, model cache, repository clones, or database credentials.
