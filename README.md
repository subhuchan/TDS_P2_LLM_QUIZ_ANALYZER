# TDS Project 2 - LLM Quiz Analyzer

This project implements an LLM-powered quiz analysis system with web scraping, data processing, and analysis capabilities.

## Features

- **Web Scraping**: Download files and scrape web content using aiohttp
- **Data Processing**: Parse CSV, JSON, and PDF files with comprehensive data cleaning
- **Analysis Engine**: Statistical analysis, filtering, aggregation, and data transformations

## Installation

```bash
pip install -r requirements.txt
```

## Testing

Run all tests:
```bash
python -m pytest tests/ -v
```

Run specific test modules:
```bash
python -m pytest tests/test_web_scraper.py -v
python -m pytest tests/test_data_processor.py -v
python -m pytest tests/test_analysis_engine.py -v
```

## Project Structure

```
TDS_P2/
├── src/
│   ├── web_scraper.py       # Web scraping functionality
│   ├── data_processor.py    # Data parsing and processing
│   ├── analysis_engine.py   # Data analysis operations
│   └── logging_config.py    # Logging configuration
├── tests/
│   ├── test_web_scraper.py
│   ├── test_data_processor.py
│   └── test_analysis_engine.py
├── .kiro/
│   └── specs/
│       └── test-fixes/      # Specification for test fixes
└── requirements.txt
```

## API Endpoints

The system provides API endpoints for quiz analysis tasks. See the API documentation for details.

## License

MIT License - see LICENSE file for details.

## Contact

Email: 22f3000695@ds.study.iitm.ac.in
