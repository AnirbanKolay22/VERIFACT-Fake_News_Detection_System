# 🧠 Multimodal Fake News Detection System

This project implements a **multimodal fake news detection system** capable of analyzing **text, images, videos, and web links**.  
It extracts verifiable claims, retrieves evidence from trusted sources, evaluates semantic similarity, and produces an explainable credibility verdict.

The system is designed as an **academic MCA-level project**, focusing on modularity, explainability, and real NLP techniques.

---

## 📌 System Overview

The system follows a unified verification pipeline:

**Input → Claim Extraction → Claim Normalization → Evidence Retrieval → Verification → Explanation → Verdict**

Supported input types:
- 📝 Text
- 🖼️ Image
- 🎥 Video
- 🔗 News / social media links


---

## 🔁 Processing Pipeline

### 1️⃣ Input Handling
- Handled via **FastAPI** (`app/main.py`)
- Accepts text, file uploads, or URLs
- Routes input based on modality

---

### 2️⃣ Claim Extraction
| Modality | Method |
|--------|--------|
| Text | Abstractive summarization using transformer models |
| Image | OCR → summarized claim |
| Video | Audio extraction → speech-to-text → summarized claim |
| Link | Web scraping → summarized claim |

Goal: extract a **short, factual, verifiable claim**.

---

### 3️⃣ Claim Normalization
- Removes noise and extra clauses
- Keeps claims within API length limits
- Relaxes queries when evidence retrieval fails

---

### 4️⃣ Evidence Retrieval
- Queries Wikipedia and trusted sources
- Extracts multiple evidence snippets
- Assigns trust scores per source

---

### 5️⃣ Claim Verification
- Uses **semantic similarity** (Sentence Transformers)
- Compares extracted claim with retrieved evidence
- Outputs similarity score and verdict label

Possible labels:
- **Supported**
- **Refuted**
- **Uncertain**

---

### 6️⃣ Explanation Generation
- Selects the strongest evidence
- Produces a human-readable explanation
- Explains why a claim is real, fake, or uncertain

---

### 7️⃣ Final Output

```json
{
  "claim": "Narendra Modi is President of Bihar",
  "verdict": "Fake",
  "confidence": 0.23,
  "explanation": "Evidence contradicts the claim..."
}
```

---

### 🚀 How to Run the Project

1. **Install dependencies**

```bash
pip install -r requirements.txt
```

2. **Start the FastAPI server**

```bash
uvicorn app.main:app --reload
```

3. **Access the API**

Open your browser or use curl:

```text
http://127.0.0.1:8000
```

---

### 🎯 Key Features

- **Multimodal**: text, image, video, and link processing
- **Modular & extensible** architecture
- **Semantic verification** using sentence embeddings
- **Explainable** outputs with evidence and reasoning
- **Academic-project friendly** (easy to extend and experiment)

---

### ⚠️ Limitations

- Evidence retrieval primarily relies on **Wikipedia** and similar sources
- OCR and speech-to-text performance depends on input quality
- No social-media metadata or network-based analysis yet
- Claim extraction uses general summarization (not fine-tuned claim models)

---

### 🔮 Future Enhancements

- Zero-shot and NLI-based verification
- Source credibility and social-context scoring
- Multilingual support
- Knowledge-graph integration for richer evidence linking
- Fine-tuned claim extraction models

---

### 🎓 Intended Use

- MCA / academic final-year projects
- Research demonstrations and learning multimodal NLP pipelines

> Not intended for production deployment..
