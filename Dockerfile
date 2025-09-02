FROM python:3.11-slim

# Set working directory
WORKDIR /app

# Install system dependencies
RUN apt-get update && apt-get install -y \
    curl \
    && rm -rf /var/lib/apt/lists/*

# Copy requirements first for better caching
COPY requirements.txt .

# Install Python dependencies
RUN pip install --no-cache-dir -r requirements.txt

# Copy the entire project
COPY . .

# Expose the API port
EXPOSE 8771

# Set environment variables
ENV PYTHONPATH=/app \
    API_PORT=8771 \
    LLM_PROVIDER=openai \
    OPENAI_MODEL=gpt-4o \
    MAX_RESEARCH_CYCLES=3 \
    MAX_SEARCH_RESULTS_PER_QUERY=5 \
    MAX_URLS_TO_SCRAPE_PER_CYCLE=3

# Health check
HEALTHCHECK --interval=30s --timeout=30s --start-period=5s --retries=3 \
    CMD curl -f http://localhost:8771/health || exit 1

# Default command to run the FastAPI server
CMD ["python", "server/main_working.py"] 