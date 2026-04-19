import json
import os
from pathlib import Path

import anthropic
import pydantic
from dotenv import load_dotenv


class Order(pydantic.BaseModel):
    product_name: str
    price: float
    quantity: int


def extract_text_from_response(message: anthropic.types.Message) -> str:
    text_parts = []
    for block in message.content:
        if block.type == "text":
            text_parts.append(block.text)
    return "".join(text_parts).strip()


def load_env() -> None:
    # Load backend/.env so tests work when launched from this folder.
    backend_env = Path(__file__).resolve().parents[2] / ".env"
    load_dotenv(dotenv_path=backend_env, override=False)


def build_client() -> anthropic.Anthropic:
    client_kwargs = {}
    base_url = os.getenv("ANTHROPIC_BASE_URL", "").strip()
    if base_url:
        client_kwargs["base_url"] = base_url
    return anthropic.Anthropic(**client_kwargs)


def resolve_model() -> str:
    return (
        os.getenv("ANTHROPIC_MODEL")
        or os.getenv("EDITOR_MODEL")
        or "claude-sonnet-4-6"
    )


def normalize_json_text(raw_text: str) -> str:
    text = raw_text.strip()
    if text.startswith("```"):
        lines = text.splitlines()
        if lines and lines[0].startswith("```"):
            lines = lines[1:]
        if lines and lines[-1].strip() == "```":
            lines = lines[:-1]
        text = "\n".join(lines).strip()
    return text


def main() -> None:
    load_env()

    if not os.getenv("ANTHROPIC_API_KEY"):
        raise RuntimeError("ANTHROPIC_API_KEY is not set.")

    model = resolve_model()
    client = build_client()

    prompt = """
Extract product_name, price, and quantity from this customer message.
Return ONLY valid JSON.

Customer message:
"Hi, I'd like to order 2 packs of Green Tea for 5.50 dollars each."

Expected JSON format:
{"product_name":"Green Tea","price":5.50,"quantity":2}
""".strip()

    streamed_text = []
    print("Streaming output:")

    try:
        with client.messages.stream(
            model=model,
            max_tokens=256,
            messages=[{"role": "user", "content": prompt}],
        ) as stream:
            for text in stream.text_stream:
                print(text, end="", flush=True)
                streamed_text.append(text)

            final_message = stream.get_final_message()
    except anthropic.PermissionDeniedError as exc:
        configured_base_url = os.getenv("ANTHROPIC_BASE_URL", "").strip()
        hint = (
            "Permission denied (403). Check whether your API key is valid for the configured endpoint/model. "
            f"Current model: {model}. "
            f"ANTHROPIC_BASE_URL set: {bool(configured_base_url)}."
        )
        raise RuntimeError(hint) from exc

    print("\n\n---")

    full_text = "".join(streamed_text).strip()
    if not full_text:
        full_text = extract_text_from_response(final_message)

    normalized_text = normalize_json_text(full_text)
    print(f"Final text: {normalized_text}")

    parsed = Order.model_validate(json.loads(normalized_text))
    print(f"Parsed order: {parsed.model_dump()}")


if __name__ == "__main__":
    main()
