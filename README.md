# PYQ-Finder

A web application to scrape and download Previous Year Question (PYQ) papers from MIT Manipal library portals.

## Features

- 📚 Scrape PYQ papers from multiple library portals
- 🔍 Search and filter papers by year, semester, branch, and subject
- 📥 Download papers directly or from Firebase Storage
- 🎨 Modern UI with SvelteKit, TailwindCSS, and shadcn-svelte

## Tech Stack

- **Backend**: Flask (Python 3.11+)
- **Frontend**: SvelteKit + TailwindCSS + shadcn-svelte
- **Database**: Firebase Firestore
- **Storage**: Firebase Cloud Storage
- **Scraping**: BeautifulSoup4 + Selenium

## Project Structure

```
LibraryScraper/
├── backend/           # Flask API server
│   ├── app/
│   │   ├── routes/    # API endpoints
│   │   └── services/  # Scrapers and Firebase
│   ├── main.py
│   └── requirements.txt
├── frontend/          # SvelteKit application
│   ├── src/
│   └── package.json
└── README.md
```

## Getting Started

### Prerequisites

- Python 3.11+
- Node.js 18+
- Firebase project with Firestore and Storage enabled

### Backend Setup

```bash
cd backend
..\venv\Scripts\activate  # Windows
pip install -r requirements.txt
python main.py
```

### Frontend Setup

```bash
cd frontend
npm install
npm run dev
```

## Library Portals

This application scrapes from:
1. https://mitmpllibportal.manipal.edu/question-papers
2. https://libportal.manipal.edu/mit/Question%20Paper.aspx

## License

MIT
