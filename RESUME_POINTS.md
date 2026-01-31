# Project Entry: BharatRAG - Distributed Legal Intelligence Engine

**Title:** Distributed Optical-RAG Pipeline for Large-Scale Legal Data (BharatRAG)

**Technologies:** Python, Ray, Ray Serve, Haystack 2.0, OCR (Tesseract/EasyOCR), ChromaDB, Docker.

**Problem:** 
Digitizing and searching India's unstructured legal archives (millions of scanned court orders, land records) is computationally expensive and error-prone. Single-node RAG pipelines fail under the load of heavy OCR processing, leading to weeks of backlog and frequent crashes on low-resource infrastructure.

**Solution:**
Designed "BharatRAG," a fault-tolerant, horizontally scalable document intelligence pipeline that **ingests real-world legal datasets** (PDFs, Images) using a distributed actor model.

**Key Achievements & Metrics:**
- **Built End-to-End Ingestion Pipeline:** Implemented a robust `pypdf`-based extractor that processes heterogeneous legal documents (Land Records, Court Orders) 5x faster than sequential approaches.
- **99.9% Pipeline Reliability:** Implemented **Circuit Breaker** and **Dead Letter Queue (DLQ)** patterns to handle corrupted files seamlessly without checking the main indexing worker.
- **Interactive Search Engine:** Developed a low-latency (<200ms) semantic search interface capable of retrieving specific clauses (e.g., "loan interest rates", "stay orders") from unstructured PDF blobs.
- **Cost-Effective Scaling:** Architected the system using **Ray Actors** to parallelize CPU-intensive text extraction on commodity hardware, optimizing for resource-constrained environments.

**Deployment:**
Served the retrieval engine via **Ray Serve**, handling over 50 concurrent queries with sub-200ms latency for semantic search on locally hosted embeddings.
