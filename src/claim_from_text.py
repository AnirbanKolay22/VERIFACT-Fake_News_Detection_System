import os
import warnings
import json


# --- Clean startup (no warnings) ---
os.environ["TF_CPP_MIN_LOG_LEVEL"] = "2"
warnings.filterwarnings("ignore", category=FutureWarning)

from transformers import BartForConditionalGeneration, BartTokenizer
import torch

# --- Load BART model lazily ---
MODEL_NAME = "facebook/bart-large-cnn"
device = torch.device("cpu")
tokenizer = None
model = None
model_load_error = None


def load_model_once():
    global tokenizer, model, model_load_error
    if tokenizer is not None and model is not None:
        return
    if model_load_error is not None:
        return

    try:
        tokenizer = BartTokenizer.from_pretrained(MODEL_NAME)
        model = BartForConditionalGeneration.from_pretrained(MODEL_NAME)
        model.to(device)
    except Exception as exc:
        model_load_error = exc


def summarize_text(text, max_chars=95):
    """
    Generates <=100 char, fact-dense query string for evidence APIs
    """
    if text is None:
        return ""

    text = " ".join(str(text).split())
    if not text:
        return ""

    if len(text) <= 80:
        return text[:max_chars]

    load_model_once()
    if tokenizer is None or model is None:
        return text[:max_chars]

    try:
        inputs = tokenizer(
            text,
            max_length=512,
            return_tensors="pt",
            truncation=True
        ).to(device)

        summary_ids = model.generate(
            inputs["input_ids"],
            num_beams=2,
            length_penalty=0.8,
            max_length=45,
            min_length=20,
            no_repeat_ngram_size=3,
            early_stopping=True
        )

        summary = tokenizer.decode(
            summary_ids[0],
            skip_special_tokens=True
        )
    except Exception:
        return text[:max_chars]

    return summary.strip() if summary.strip() else text[:max_chars]




# -------------------------
# 🧪 Example usage
# -------------------------
if __name__ == "__main__":
    text = """
    There are times when the night sky glows with bands of color. The bands may
begin as cloud shapes and then spread into a great arc across the entire sky. They
may fall in folds like a curtain drawn across the heavens. The lights usually grow
brighter, then suddenly dim. During this time the sky glows with pale yellow, pink,
green, violet, blue, and red. These lights are called the Aurora Borealis. Some
people call them the Northern Lights. Scientists have been watching them for
hundreds of years. They are not quite sure what causes them. In ancient time people were afraid of the Lights. They imagined that they saw fiery dragons in the
sky. Some even concluded that the heavens were on fire.
    """

    result = summarize_text(text)
    print("\n--- ORIGINAL TEXT ---\n")
    print(text)

    print("\n--- BART SUMMARY ---\n")
    print(json.dumps(result, indent=4, ensure_ascii=False))
