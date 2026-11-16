import os
from dotenv import load_dotenv
from langchain_groq import ChatGroq
from langchain_core.prompts import ChatPromptTemplate, MessagesPlaceholder
from langchain_core.messages import HumanMessage, AIMessage

load_dotenv()
if not os.getenv("GROQ_API_KEY"):
    raise RuntimeError("GROQ_API_KEY is missing. Add it to your .env file.")

MAIN_MODEL = "openai/gpt-oss-120b"
FALLBACK_MODEL = "openai/gpt-oss-20b"

prompt = ChatPromptTemplate.from_messages([
    ("system", "You are a helpful, friendly assistant."),
    MessagesPlaceholder("history"),
    ("human", "{input}"),
])
prompt = ChatPromptTemplate.from_messages([
    ("system",
     "You are a helpful assistant. Keep answers short: 1 to 3 sentences "
     "unless the user asks for detail. Do not add extra explanations, "
     "headings or follow-up suggestions."),
    MessagesPlaceholder("history"),
    ("human", "{input}"),
])
history = []


def ask(model_id, text):
    """Stream a reply from one model and return the full text."""
    chain = prompt | ChatGroq(model=model_id, temperature=0.7)
    reply = ""
    for chunk in chain.stream({"input": text, "history": history}):
        print(chunk.content, end="", flush=True)
        reply += chunk.content
    return reply


print("Chatbot ready.")
print(f"Main model:     {MAIN_MODEL}")
print(f"Fallback model: {FALLBACK_MODEL}")
print("Type 'exit' to quit, 'clear' to reset the conversation.\n")

while True:
    try:
        user_input = input("You: ").strip()
    except (KeyboardInterrupt, EOFError):
        print("\nGoodbye!")
        break

    if not user_input:
        continue
    if user_input.lower() in ("exit", "quit"):
        print("Goodbye!")
        break
    if user_input.lower() == "clear":
        history.clear()
        print("Conversation cleared.\n")
        continue

    reply = None
    for model_id in (MAIN_MODEL, FALLBACK_MODEL):
        label = "main" if model_id == MAIN_MODEL else "fallback"
        print(f"Bot [{label}]: ", end="", flush=True)
        try:
            reply = ask(model_id, user_input)
            break
        except Exception as e:
            print(f"(failed: {str(e)[:100]})")
            if model_id == MAIN_MODEL:
                print("Switching to fallback model...\n")

    if reply is None:
        print("\nBoth models failed. Check your API key, internet or rate limits.\n")
        continue

    print("\n")
    history.append(HumanMessage(content=user_input))
    history.append(AIMessage(content=reply))