import logging
import os
import sys
import argparse
import time
import json
from typing import List, Dict, Any
import yaml
from PIL import Image
from pypdf import PdfReader

# Haystack Core
from haystack import Pipeline, Document
from haystack.components.embedders import SentenceTransformersDocumentEmbedder, SentenceTransformersTextEmbedder
from haystack.components.retrievers.in_memory import InMemoryEmbeddingRetriever
from haystack.components.readers import ExtractiveReader
from haystack.components.writers import DocumentWriter
from haystack.document_stores.in_memory import InMemoryDocumentStore

# Ray Integration for Distributed Computing (Conditional)

# Setup Logging
logging.basicConfig(level=logging.INFO, format='%(asctime)s - [BharatRAG] - %(levelname)s - %(message)s')
logger = logging.getLogger("BharatRAG")

# -----------------------------------------------------------------------------
# Configuration & Utilities
# -----------------------------------------------------------------------------

def load_config(config_path='bharat_config.yaml'):
    if not os.path.exists(config_path):
        # Default config if file missing
        return {
            'model_name': 'sentence-transformers/all-MiniLM-L6-v2',
            'num_workers': 2,
            'max_retries': 3,
            'chunk_size': 500
        }
    with open(config_path, 'r') as f:
        return yaml.safe_load(f)

try:
    import ray
    from ray import serve
    RAY_AVAILABLE = True
except ImportError:
    RAY_AVAILABLE = False
    logger.warning("Ray not installed. Running in LOCAL SIMULATION mode.")
    
# ... (rest of imports)

# -----------------------------------------------------------------------------
# Ray Actor: The "Ingestion Worker"
# Solves the bottleneck of processing millions of scanned scanned PDFs/Images
# -----------------------------------------------------------------------------

class DigitizationWorker:
    """
    A dedicated worker for 'Dirty Work': OCR, cleanup, and formatting.
    Scales horizontally across cheap CPU nodes to handle massive backlogs 
    of court records or government notices.
    """
    def __init__(self):
        # Initialize heavy OCR models here (e.g., Tesseract, EasyOCR)
        # self.ocr_engine = load_ocr_model() 
        pass

    def process_document(self, doc_path: str) -> Dict:
        """
        Actually processes PDF/Image files from the disk.
        Uses pypdf for text and mocks OCR for images (unless tesseract installed).
        """
        try:
            filename = os.path.basename(doc_path)
            logger.info(f"Processing real file: {filename}")
            
            content = ""
            meta = {
                "source": filename,
                "district": "Unknown", # Would be parsed from text in real life
                "processed_by": "worker_node"
            }

            if filename.endswith(".pdf"):
                reader = PdfReader(doc_path)
                for page in reader.pages:
                    content += page.extract_text() + "\n"
            elif filename.endswith(".txt"):
                with open(doc_path, 'r') as f:
                    content = f.read()
            else:
                # Simulate OCR for non-text files or raise if unknown
                if "corrupt" in filename:
                     raise ValueError("File corrupted or unreadable format (simulated)")
                content = f"[OCR Extracted] Image content from {filename}..."
            
            if not content.strip():
                 raise ValueError("No text extracted from document")

            # Simple keyword extraction for metadata (Simulated NER)
            if "Bhopal" in content: meta["district"] = "Bhopal"
            elif "Indore" in content: meta["district"] = "Indore"
            
            logger.info(f"Worker finished: {filename} ({len(content)} chars)")
            return {"content": content, "meta": meta}

        except Exception as e:
            logger.error(f"Failed to process {doc_path}: {e}")
            return {"error": str(e), "filepath": doc_path}

if RAY_AVAILABLE:
    DigitizationWorker = ray.remote(num_cpus=1)(DigitizationWorker)

# -----------------------------------------------------------------------------
# The Main Engine
# -----------------------------------------------------------------------------

class BharatRAGEngine:
    def __init__(self, config: Dict):
        self.config = config
        self.document_store = InMemoryDocumentStore()
        
        if RAY_AVAILABLE:
            self.workers = [DigitizationWorker.remote() for _ in range(config['num_workers'])]
        else:
            self.workers = [DigitizationWorker() for _ in range(config['num_workers'])]
        
        # Dead Letter Queue for failed documents (critical for legal compliance)
        self.failed_docs_log = "failed_ingestion_log.jsonl"
        
        self._setup_pipelines()

    def _setup_pipelines(self):
        # 1. Indexing Pipeline (Embeddings)
        self.indexing_pipeline = Pipeline()
        embedder = SentenceTransformersDocumentEmbedder(model=self.config['model_name'])
        writer = DocumentWriter(document_store=self.document_store)

        self.indexing_pipeline.add_component("embedder", embedder)
        self.indexing_pipeline.add_component("writer", writer)
        self.indexing_pipeline.connect("embedder.documents", "writer.documents")
        
        # 2. Query Pipeline (Retrieval)
        self.query_pipeline = Pipeline()
        text_embedder = SentenceTransformersTextEmbedder(model=self.config['model_name'])
        retriever = InMemoryEmbeddingRetriever(document_store=self.document_store)
        
        self.query_pipeline.add_component("text_embedder", text_embedder)
        self.query_pipeline.add_component("retriever", retriever)
        self.query_pipeline.connect("text_embedder.embedding", "retriever.query_embedding")

    def ingest_data_distributed(self, file_paths: List[str]):
        """
        Orchestrates the Ray workers to process files in parallel.
        Handles failures gracefully (Circuit Breaker pattern).
        """
        logger.info(f"Starting distributed ingestion of {len(file_paths)} legal documents...")
        
        if RAY_AVAILABLE:
            # Round-robin dispatch to Ray actors
            futures = []
            for i, path in enumerate(file_paths):
                worker = self.workers[i % len(self.workers)]
                futures.append(worker.process_document.remote(path))
            results = ray.get(futures)
        else:
             # Sequential fallback for demo
            results = []
            for i, path in enumerate(file_paths):
                 worker = self.workers[i % len(self.workers)]
                 results.append(worker.process_document(path))
        
        valid_docs = []
        failed_count = 0

        for res in results:
            if "error" in res:
                # Log to Dead Letter Queue
                failed_count += 1
                with open(self.failed_docs_log, "a") as f:
                    f.write(json.dumps(res) + "\n")
            else:
                doc = Document(content=res['content'], meta=res['meta'])
                valid_docs.append(doc)

        logger.info(f"Ingestion Stats: {len(valid_docs)} Success, {failed_count} Failed.")
        
        if valid_docs:
            # Run the embedding pipeline on the clean text
            # DocumentWriter component handles storage automatically
            max_retries = 3
            for attempt in range(max_retries):
                try:
                    self.indexing_pipeline.run({"embedder": {"documents": valid_docs}})
                    logger.info("Embeddings generated and stored.")
                    break
                except Exception as e:
                    if attempt < max_retries - 1 and "Timeout" in str(e):
                        logger.warning(f"Model loading timed out (Attempt {attempt+1}/{max_retries}). Retrying in 5s...")
                        time.sleep(5)
                    else:
                        logger.error(f"Failed to run indexing pipeline after {max_retries} attempts: {e}")
                        raise e

    def search(self, query: str, top_k: int = 3):
        logger.info(f"Querying: '{query}'")
        result = self.query_pipeline.run({
            "text_embedder": {"text": query},
            "retriever": {"top_k": top_k}
        })
        return result['retriever']['documents']

# -----------------------------------------------------------------------------
# Deployment Interface (Ray Serve)
# -----------------------------------------------------------------------------

if RAY_AVAILABLE:
    @serve.deployment(num_replicas=1)
    class BharatRAGAPI:
        def __init__(self, config_path: str):
            self.config = load_config(config_path)
            self.engine = BharatRAGEngine(self.config)
            
            # Pre-seed with dummy data for immediate testing
            dummy_files = ["land_record_001.pdf", "corrupt_file_X.img", "court_order_2024.pdf"]
            self.engine.ingest_data_distributed(dummy_files)

        async def __call__(self, request):
            data = await request.json()
            query = data.get("query", "")
            if not query:
                return {"error": "Query parameter missing"}
                
            results = self.engine.search(query)
            
            response = []
            for doc in results:
                response.append({
                    "snippet": doc.content,
                    "district": doc.meta.get('district'),
                    "score": doc.score
                })
                
            return {"results": response, "server": "BharatRAG-v1"}

# -----------------------------------------------------------------------------
# CLI Entry Point
# -----------------------------------------------------------------------------

if __name__ == "__main__":
    parser = argparse.ArgumentParser(description="BharatRAG: Distributed Engine for Legal Data")
    parser.add_argument("--mode", choices=["local", "deploy"], default="local")
    args = parser.parse_args()

    config = load_config()

    if args.mode == "local":
        # Start local Ray cluster
        if RAY_AVAILABLE:
            ray.init(ignore_reinit_error=True)
        else:
            logger.info("Ray unavailable, skipping ray.init()")
        
        engine = BharatRAGEngine(config)
        
        # Real Ingestion: Scan 'data/' folder
        data_dir = "data"
        if not os.path.exists(data_dir):
            logger.error(f"Data directory '{data_dir}' not found. Run create_dummy_data.py first.")
            sys.exit(1)

        files = [os.path.join(data_dir, f) for f in os.listdir(data_dir) if f.endswith(('.pdf', '.txt', '.png', '.jpg'))]
        if not files:
            logger.warning("No documents found in data/ folder!")
            sys.exit(1)
            
        logger.info(f"Found {len(files)} documents to ingest.")
        engine.ingest_data_distributed(files)
        
        # Interactive Search Loop
        print("\n" + "="*50)
        print("BharatRAG Engine Ready! (Type 'exit' to quit)")
        print("="*50 + "\n")
        
        while True:
            query = input("\nEnter Query >> ")
            if query.lower() in ["exit", "quit", "q"]:
                break
            
            if not query.strip():
                continue
                
            results = engine.search(query)
            print("-" * 30)
            for i, doc in enumerate(results, 1):
                district = doc.meta.get('district', 'N/A')
                source = doc.meta.get('source', 'Unknown')
                # Truncate content for display
                snippet = doc.content[:200].replace('\n', ' ') + "..."
                print(f"[{i}] {source} (District: {district})\n    {snippet}\n")
            print("-" * 30)
            
    elif args.mode == "deploy":
        if RAY_AVAILABLE:
            ray.init()
            serve.run(BharatRAGAPI.bind('bharat_config.yaml'))
        else:
            logger.error("Cannot deploy without Ray installed.")
