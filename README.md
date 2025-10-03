AI-powered lead qualification using multi-agent collaboration with CrewAI.

## Features

- Multi-agent AI system for intelligent lead analysis
- Email and form submission processing
- Configurable scoring criteria
- Detailed qualification reports
- Real-time agent collaboration visualization

## Project Structure

```
crewai-lead-qualification/
├── app.py                      # Main Streamlit application
├── requirements.txt            # Python dependencies
├── .env                        # Environment variables (create this)
├── .gitignore                 # Git ignore file
├── README.md                   # This file
└── src/
    ├── __init__.py
    ├── agents/
    │   ├── __init__.py
    │   └── lead_agents.py     # CrewAI agent definitions
    ├── tasks/
    │   ├── __init__.py
    │   └── lead_tasks.py      # CrewAI task definitions
    ├── crew/
    │   ├── __init__.py
    │   └── lead_crew.py       # Crew orchestration
    └── utils/
        ├── __init__.py
        ├── result_parser.py   # Result parsing utilities
        └── validators.py       # Input validation
```

## Setup

1. Create virtual environment:
```bash
python -m venv venv
source venv/bin/activate  # Windows: venv\Scripts\activate
```

2. Install dependencies:
```bash
pip install -r requirements.txt
```

3. Create `.env` file:
```bash
OPENAI_API_KEY=your_key_here
```

4. Run the application:
```bash
streamlit run app.py
```

## Usage

1. Configure target criteria in the sidebar
2. Choose input method (Email or Form)
3. Fill in lead information
4. Click "Analyze with CrewAI"
5. Review multi-agent analysis results

## Agent Workflow

1. **Email Parser** - Extracts contact information
2. **Company Researcher** - Gathers business intelligence
3. **Lead Scorer** - Calculates qualification score
4. **Recommendation Agent** - Provides next steps

## License

MIT
