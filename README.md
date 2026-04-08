# AI Sales Coach Full-Stack Starter

This project is a React + FastAPI starter template for your AI Sales Coach platform.

## Stack
- Frontend: React + Vite + React Router
- Backend: FastAPI (Python)
- Architecture: React frontend calling a Python API backend that runs your AI/business logic

---

## Project Structure

```bash
ai-sales-coach-fullstack/
├── frontend/
├── backend/
└── README.md
```

---

## How to Start in VS Code

### 1. Open the project folder
Open the extracted `ai-sales-coach-fullstack` folder in VS Code.

### 2. Start the backend
Open a terminal in VS Code and run:

```bash
cd backend
python -m venv venv
```

#### On macOS/Linux
```bash
source venv/bin/activate
```

#### On Windows (PowerShell)
```powershell
venv\Scripts\Activate.ps1
```

Then install dependencies and start the backend:

```bash
pip install -r requirements.txt
uvicorn app.main:app --reload --port 8000
```

Backend will run at:
- `http://localhost:8000`
- Swagger docs: `http://localhost:8000/docs`

### 3. Start the frontend
Open a second terminal in VS Code and run:

```bash
cd frontend
npm install
npm run dev
```

Frontend will run at:
- `http://localhost:5173`

---

## App Flow
1. User lands on the Home Page
2. User clicks **Get Started**
3. User fills the lead form
4. Frontend sends form data to backend
5. Backend runs enrichment + recommendation + financing + AI summary
6. Frontend displays the generated report

---

## Current Features
- Home page with CTA
- Lead form page
- Report page
- FastAPI backend with one report generation endpoint
- Structured recommendation + financing logic
- Placeholder AI summary layer
- Clean service-based backend structure

---

## Important Note
This is a strong starter architecture and not a finished production system.
You should later improve:
- authentication
- database persistence
- real LLM integration
- PDF export
- better styling and design system
- richer domain-specific recommendation logic

---

## API Endpoint
### Generate report
`POST /api/report/generate`

Example payload:

```json
{
  "postcode": "68159",
  "product_interest": "solar_battery",
  "household_size": 4,
  "annual_consumption_kwh": 4500,
  "budget_band": "medium",
  "customer_goal": "reduce monthly bills"
}
```

---

## Next Suggested Improvements
- Replace placeholder AI summary with OpenAI or another LLM provider
- Add report persistence with PostgreSQL
- Add auth for installers/customers
- Add charts and cleaner card UI in React
- Add real subsidy and market data enrichment
