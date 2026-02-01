# BharatRAG: Distributed Legal Data Engine

**BharatRAG** is a fault-tolerant, horizontally scalable RAG (Retrieval Augmented Generation) pipeline designed for processing massive volumes of unstructured legal and government data in resource-constrained environments.

## 🚀 How to Start

### 1. Prerequisites
- Python 3.9+
- A working internet connection (to download models)

### 2. Installation
Install the required dependencies using pip:
```bash
pip install -r requirements.txt
```

### 3. Running Locally (Simulation Mode)
To see the system in action with simulated OCR delays and fault tolerance:
```bash
python3 bharat_rag_engine.py --mode local
```
**What to expect:**
- You will see logs of "Ingestion Workers" starting up.
- The system will process dummy PDF/Image files.
- It will intentionally fail on "corrupt" files (and log them to `failed_ingestion_log.jsonl`).
- Finally, it will perform a search query ("land ownership in Bhopal") and show results.

### 4. Running as a Deployment (API)
To run as a scalable Ray Serve deployment:
```bash
python3 bharat_rag_engine.py --mode deploy
```
This exposes the engine as an HTTP API.

## 📂 Project Structure
- `bharat_rag_engine.py`: Core logic for Ray Actors and Haystack pipeline.
- `bharat_config.yaml`: Configuration for workers, models, and scaling.
- `RESUME_POINTS.md`: Technical summary for your portfolio/resume.

## Local Execution Notes

- If Ray is not installed, the engine runs in LOCAL SIMULATION mode.
- Some ingestion failures (e.g., corrupted or unreadable files) are expected and handled gracefully.
- On Windows, HuggingFace may show cache/symlink warnings; these do not affect execution and can be safely ignored.
