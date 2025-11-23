# Research Agent Architecture — Summary (MacBook + iMac Setup)

## 1. Overall System Design

You are building a two-machine knowledge + research workflow:

- **MacBook (Primary Device):**  
  Main interface for writing, coding, thinking, reading, carrying everywhere.

- **iMac “Hedorah” (Home Base):**  
  Always-on workstation acting as:
  - file server,
  - compute node,
  - background research agent host,
  - storage for papers, notes, datasets.

The shared folder on Hedorah (via SMB) is the canonical **Obsidian vault** and active knowledge base.

---

## 2. Vault Structure (Recommended)

A clean vault structure makes the agent predictable:

00_inbox/  
01_papers/  
	raw_pdfs/  
	notes/  
02_ideas/  
03_experiments/  
04_projects/  
99_system/  
	agent_log.md  
	agent_tasks.md  
	arxiv_inbox.md


- You write and edit normally in Obsidian  
- The agent operates within predictable directories  
- Git tracks all changes (recommended)

---

## 3. Agent Responsibilities (Modular Design)

Break the agent into functional modules:

### **1. Ingestion Module**
- Watches `raw_pdfs/` or `arxiv_inbox.md`
- Downloads arXiv PDFs
- Extracts metadata
- Creates structured `.md` notes in `01_papers/notes/`

### **2. Understanding Module**
- Generates summaries
- Extracts contributions, limitations, open problems

### **3. Connection-Finder**
- Uses embeddings + retrieval
- Links related papers
- Suggests conceptual relationships

### **4. Idea Generator**
- Proposes research ideas + experiment designs
- Writes `.md` files in `02_ideas/` and `03_experiments/`

### **5. Task Manager**
- Reads commands from `agent_tasks.md`
- Logs actions and updates statuses
- Runs periodically (cron/launchd)

---

## 4. Model Stack (Hybrid Approach)

Use different models for different tasks.

### **A. Frontier API Model (for deep reasoning)**
Ideal for:
- combining multiple papers
- generating research ideas
- designing experiments
- writing detailed structured notes

Examples:
- Claude 3.5+
- GPT-o1/o3
- Gemini 2.0

### **B. Local Models on iMac (lightweight tasks)**
Ideal for:
- metadata extraction
- short summaries
- tagging + classification
- embedding + retrieval
- cheap frequent tasks

Examples:
- `bge-large-en` (embeddings)
- 7B–14B local models via llama.cpp/ollama

### **C. Code Specialist (optional)**
For building and maintaining the agent itself:
- Claude Code
- GPT-o3-mini (code optimized)

---

## 5. ArXiv Discovery & Ingestion Pipeline

### **Stage 1: Discovery (Automated but Non-Ingesting)**
- A daily script queries arXiv API / RSS for specific categories or keywords
- Results appended to `99_system/arxiv_inbox.md` as:

```markdown
- [ ] 2411.01234 — Sparse Autoencoders and Circuits (cs.LG)
