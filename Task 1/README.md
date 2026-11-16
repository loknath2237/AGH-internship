# Groq AI Chatbot with Automatic Model Fallback

## 📌 Project Overview

This project is a command-line AI chatbot built using Python, LangChain, and Groq API. It uses Groq-hosted language models to generate responses and provides automatic fallback functionality if the primary model fails.

The chatbot maintains conversation history, streams responses in real time, and allows users to reset conversations whenever needed.

## 🚀 Features

- **AI-Powered Conversations:** Uses Groq-hosted LLMs to generate intelligent responses.
- **Primary Model:** `openai/gpt-oss-120b`
- **Fallback Model:** `openai/gpt-oss-20b`
- **Automatic Model Switching:** Switches to the fallback model if the primary model encounters an error.
- **Streaming Responses:** Displays responses token by token in real time.
- **Conversation Memory:** Maintains previous messages to provide context-aware responses.
- **Clear Conversation:** Reset the conversation history using the `clear` command.
- **Environment Variables:** Securely manages API keys using a `.env` file.

## 🛠️ Technologies Used

- Python
- Groq API
- LangChain
- LangChain Groq
- LangChain Core
- Python-dotenv

## 📂 Project Structure

```text
Groq-AI-Chatbot/
│
├── chatbot.py          # Main chatbot application
├── .env                # Groq API key
├── .gitignore          # Files excluded from Git
├── requirements.txt    # Project dependencies
└── README.md           # Project documentation
```

## ⚙️ Installation and Setup

### 1. Clone the Repository

```bash
git clone <your-repository-url>
cd Groq-AI-Chatbot
```

### 2. Create a Virtual Environment

```bash
python -m venv venv
```

Activate the environment:

**Windows:**
```bash
venv\Scripts\activate
```

**Linux / macOS:**
```bash
source venv/bin/activate
```

### 3. Install Dependencies

```bash
pip install langchain langchain-groq langchain-core python-dotenv
```

### 4. Configure Groq API Key

Create a `.env` file in the project directory:

```env
GROQ_API_KEY=your_groq_api_key_here
```

Get your API key from [Groq Console](https://console.groq.com/).

### 5. Run the Chatbot

```bash
python chatbot.py
```

## 💬 Usage

Once the chatbot starts, you can interact with it through the terminal.

**Available Commands:**

| Command | Description |
|---|---|
| `exit` | Exit the chatbot |
| `quit` | Exit the chatbot |
| `clear` | Clear conversation history |

### Example Interaction

```text
Chatbot ready.
Main model:     openai/gpt-oss-120b
Fallback model: openai/gpt-oss-20b

You: What is Artificial Intelligence?

Bot [main]: Artificial Intelligence is the ability of machines
to perform tasks that typically require human intelligence.

You: exit

Goodbye!
```

## 🔄 Model Fallback Mechanism

The chatbot follows a two-level model execution strategy:

1. First, it attempts to generate a response using `openai/gpt-oss-120b`.
2. If the primary model fails due to an API error, rate limit, or other exception, it switches to `openai/gpt-oss-20b`.
3. If both models fail, an error message is displayed.

This improves chatbot reliability by providing an alternative model when the primary model is unavailable.

## 🔐 Security

- API keys are stored in the `.env` file.
- Never upload your `.env` file to GitHub.
- Add the following entries to `.gitignore`:

```gitignore
.env
venv/
__pycache__/
*.pyc
```

## 🔮 Future Enhancements

- Web-based chatbot interface.
- Persistent conversation storage.
- Support for multiple LLM providers.
- Chat export functionality.
- Customizable chatbot personalities.

## 👨‍💻 Author

**R. Loknath**

GitHub: [loknath2237](https://github.com/loknath2237)

---

⭐ If you find this project useful, consider giving it a star on GitHub.
