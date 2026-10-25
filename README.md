# PromiseTrace-AI 🤖

## Overview
PromiseTrace-AI is an AI-powered project designed to automate web-based information gathering using TinyFish AI. It sends a website URL and a specific goal to the TinyFish automation API, which navigates the website and collects relevant information.

## Features
- 🌐 Automated website navigation
- 🤖 AI-powered web automation using TinyFish
- 🔗 Custom website URL input
- 📊 Structured automation results
- ⚡ Python-based API integration

## Tech Stack
- Python
- Requests
- TinyFish AI API
- JSON

## Project Structure

```text
PromiseTrace-AI/
├── main.py
├── README.md
├── requirements.txt
└── .gitignore
```

*Note: The project structure may vary depending on the files present in your repository.*

## Prerequisites
- Python 3.10 or later
- A valid TinyFish API key
- Internet connection

## Installation

### 1. Clone the Repository

```bash
git clone <YOUR_GITHUB_REPOSITORY_URL>
cd PromiseTrace-AI
```

### 2. Install Dependencies

```bash
pip install -r requirements.txt
```

If `requirements.txt` is unavailable, install Requests:

```bash
pip install requests
```

### 3. Configure the API Key

Set your TinyFish API key as an environment variable.

**Windows PowerShell:**

```powershell
$env:TINYFISH_API_KEY="YOUR_API_KEY"
```

Replace `YOUR_API_KEY` with your actual API key.

**Important:** Never publish your API key in your source code or GitHub repository.

### 4. Run the Project

```bash
python main.py
```

Follow the program's instructions to provide the website URL and automation goal, if prompted.

## How It Works

1. The user provides a website URL and an automation goal.
2. The Python application sends the request to the TinyFish API.
3. TinyFish performs the requested web automation.
4. The application processes and displays the returned results.

## Environment Variables

| Variable | Description |
|---|---|
| `TINYFISH_API_KEY` | API key used to authenticate TinyFish requests |

## Security
- Keep API credentials private.
- Do not commit `.env` files or API keys.
- Use environment variables to manage sensitive information.

## Future Improvements
- Support multiple websites.
- Improve error handling and retry mechanisms.
- Export results to CSV or JSON.
- Add a user-friendly interface.
- Implement structured data validation.

## Author

Developed as an AI automation project.

## License

Add a suitable open-source license if you intend to distribute this project publicly.
