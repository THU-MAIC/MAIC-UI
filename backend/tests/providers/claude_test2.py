from anthropic import Anthropic

if __name__ == "__main__":
    client = Anthropic(
        base_url="https://api.openai-proxy.org/anthropic",
        api_key="sk-Uhh35vdcXrEIU367YpgyaJetYy6DGtjKqZNlRt4jeI9A72qX",
    )

    message = client.messages.create(
        max_tokens=1024,
        messages=[
            {
                "role": "user",
                "content": "Hello, Claude",
            }
        ],
        # 可选model，支持claude-sonnet-4-6、claude-opus-4-6、claude-haiku-4-5-20251001等模型
        # model="claude-haiku-4-5-20251001",
        # model = "claude-sonnet-4-6"
        model="claude-opus-4-6",
    )
    print(message.content)
