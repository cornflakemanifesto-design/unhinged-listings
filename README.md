# Unhinged Listings

Where mundane commerce meets existential dread.

A Craigslist-styled archive of real Facebook Marketplace listings written through the lens of late-stage capitalism and fourth-wall-breaking nihilism.

## Project Structure

```
unhinged-listings/
├── server.py          # FastAPI backend (API + serves frontend)
├── static/
│   └── index.html     # Complete frontend (single-page app)
├── requirements.txt   # Python dependencies
├── render.yaml        # Render deployment config
├── .gitignore
└── README.md
```

## Deploy to Render (Free Tier)

### Step 1: Set Up MongoDB Atlas (Free)

1. Go to [mongodb.com/atlas](https://www.mongodb.com/atlas) and create a free account
2. Create a **free shared cluster** (M0 tier — 512MB, totally free)
3. Under **Database Access**, create a database user with a username and password
4. Under **Network Access**, click **Add IP Address** → **Allow Access From Anywhere** (0.0.0.0/0)
5. On the cluster page, click **Connect** → **Connect your application** → **Copy the connection string**
   - It will look like: `mongodb+srv://USERNAME:PASSWORD@cluster0.xxxxx.mongodb.net/?retryWrites=true&w=majority`
   - Replace `USERNAME` and `PASSWORD` with your actual credentials

### Step 2: Push to GitHub

1. Create a new repository on GitHub (e.g., `unhinged-listings`)
2. Push this project:

```bash
cd unhinged-listings
git init
git add .
git commit -m "Initial commit"
git branch -M main
git remote add origin https://github.com/YOUR-USERNAME/unhinged-listings.git
git push -u origin main
```

### Step 3: Deploy on Render

1. Go to [render.com](https://render.com) and sign up (free)
2. Click **New** → **Web Service**
3. Connect your GitHub repo
4. Render should auto-detect settings from `render.yaml`, but verify:
   - **Build Command**: `pip install -r requirements.txt`
   - **Start Command**: `uvicorn server:app --host 0.0.0.0 --port $PORT`
5. Under **Environment Variables**, add:
   - `MONGO_URL` = your MongoDB Atlas connection string from Step 1
   - `ADMIN_PASSWORD` = choose a password for the admin panel
   - `DB_NAME` = `unhinged_listings`
6. Click **Create Web Service**

Your site will be live at `https://unhinged-listings.onrender.com` (or similar) within a few minutes.

The database will be automatically seeded with your 5 existing listings on first launch.

## Using the Admin Panel

1. Go to `https://your-site.onrender.com/#/admin`
2. Enter your admin password
3. From here you can:
   - **Add** new listings with the form
   - **Edit** existing listings
   - **Delete** listings

## Running Locally

```bash
# Install dependencies
pip install -r requirements.txt

# Set environment variables (or create a .env file)
export MONGO_URL="mongodb://localhost:27017"
export DB_NAME="unhinged_listings"
export ADMIN_PASSWORD="changeme"

# Run the server
uvicorn server:app --reload --port 8000
```

Then open [http://localhost:8000](http://localhost:8000)

## Adding New Listings

Two ways:

1. **Admin Panel** (easiest): Go to `/#/admin`, log in, click "+ new listing"
2. **API**: POST to `/api/admin/listings?password=YOUR_PASSWORD` with listing JSON

## Notes

- Render's free tier spins down after 15 minutes of inactivity. First visit after idle may take ~30 seconds to load.
- MongoDB Atlas free tier gives you 512MB — enough for thousands of listings.
- Images are stored as URLs (hosted externally). You can use any image host or link to Facebook Marketplace images.
