## python main.py --topic "Crypto and web3 potential 10 years from now" --cycles 2 --output crypto.md 

## cleaned up version.

##  tavily as input from component

## curl cmd 

curl -X POST http://localhost:8771/research   -H "Content-Type: application/json"   -d '{
    "topic": "do something principle",
    "cycles": 2,
    "tavily_api_key": "your-tavily-api-key-here",
    "output_file": "report.md"
  }'

## openAI

curl -X POST http://localhost:8771/research \
-H "Content-Type: application/json" \
-d '{
  "topic": "Latest developments in quantum computing",
  "cycles": 2,
  "openai_api_key": "your-openai-api-key-here",
  "tavily_api_key": "your-tavily-api-key-here"
}'