# GitHub Setup Guide for APEX

Moving an AI and data-heavy project like APEX onto GitHub relies on a single rule: **Push your code, not your data.** 

GitHub is excellent for tracking history and collaborating on code, but it is not meant to hold gigs of data, external models, or running database files. Let's break down exactly how this works with the stack we have built.

## 1. How External Tools (Gemma, Qdrant) work with Git

You might be wondering: *"If I am pushing this to GitHub, how does the other person (or myself on another laptop) get the Gemma model and the Qdrant database?"*

### EmbeddingGemma and Machine Learning Models
When we use `sentence-transformers` for embedding data, we reference model names like `all-MiniLM-L6-v2` or `google/embeddinggemma-300m`. When you run the Python code, `sentence-transformers` automatically downloads the gigabytes of model weights from HuggingFace and caches them deep inside your computer's OS profile (usually `~/.cache/huggingface`). 
- **Because of this:** We don't push models to GitHub. Since they are downloaded automatically the first time the code runs anywhere, we only need to keep the Python script that calls them!

### Qdrant and Vector Databases
When you run Qdrant via Docker, it allocates a spot on your local hard drive to permanently save any new vectorized data it builds during ingestion. Generally, you never commit the raw database storage files to Git. 
- **Because of this:** Any new user who clones your GitHub Repo will run `docker-compose up` to start an empty Qdrant instance, and then they will run your `python data_pipeline/ingest_bq.py` pipeline (which you wrote!) to pull data from Google BigQuery and rebuild the local database in minutes.

---

## 2. Setting up the `.gitignore`

The `.gitignore` tells Git exactly what it is not allowed to track. I have already successfully created this for you in the root of the project as `c:\Users\apex\apex-app\.gitignore`. 

It includes restrictions against tracking:
- Any `node_modules` (gigabytes of javascript packages)
- Any `.env` files (it is incredibly dangerous to put API keys on GitHub)
- The entire `apex_data/` folder (where large JSON arrays and `.npy` models live)
- Big Python cache structures like `.venv`
- `*.pkl` files like your 120MB `embedding_cache.pkl`!

---

## 3. Pushing the codebase to GitHub

Here are the step-by-step instructions to get your current application up to the cloud.

### Option A: Using the Command Line Interface (CLI)

1. **Go to GitHub.com** and create a new repository (name it something like `apex-patent-analyzer`). Do NOT initialize it with a README or gitignore, just leave it fully empty.
2. Open your terminal in VSCode (in the root directory `c:\Users\apex\apex-app`).
3. Initialize the repo:
   ```bash
   git init
   ```
4. Stage all files (the `.gitignore` will ensure no bad files are included in this command):
   ```bash
   git add .
   ```
5. Commit your files:
   ```bash
   git commit -m "Initial commit for APEX prototype"
   ```
6. Link it to GitHub (replace the URL with the one GitHub gave you):
   ```bash
   git remote add origin https://github.com/YOUR_USERNAME/apex-patent-analyzer.git
   ```
7. Push:
   ```bash
   git branch -M main
   git push -u origin main
   ```

### Option B: Using GitHub Desktop UI (Easiest if you are new to Git)
1. Download and install **GitHub Desktop**.
2. Sign in to your GitHub account.
3. Click **File -> Add Local Repository** and select the `c:\Users\apex\apex-app` folder. 
4. It will notice it is not a Git repo and will ask if you want to create one. Click **Create a repository**.
5. Give the repository a name, and press **Create**.
6. On the left side panel, write "Initial Commit" in the Summary box and hit **Commit to main**.
7. In the top bar, click the blue button that says **Publish repository**. Keep it private or public depending on your needs, and then hit publish. 

Your APEX repository is now safe in the cloud! Note: Because of how we configured the `.gitignore`, whenever you go to a new computer, remember to recreate the `.env` file!
