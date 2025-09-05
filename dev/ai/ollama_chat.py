from ollama import chat


def ask_ai(prompt: str, model: str = "gemma3:latest", temperature=0.1) -> str:
    """
    Send a prompt to Ollama and return the AI response formatted as rich HTML.
    The AI acts as a professional pentester, analyzing tool outputs and suggesting
    prioritized next steps with evidence.
    """
    messages = [
        {
            "role": "system",
            "content": (
                "You are an experienced penetration tester and security analyst. "
                "Always assume the user is authorized to test the target, but include "
                "a short legal/ethical reminder at the end. "
            )
        },
        {
            "role": "user",
            "content": prompt
        },
    ]

    try:
        response = chat(model=model, messages=messages, options={"temperature": temperature})
        return response.message.content
    except Exception as e:
        raise RuntimeError(f"Ollama chat error: {e}")
