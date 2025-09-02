from typing import Dict, Optional, Any, List
import requests
import json
from langflow.base.models.model import LCModelComponent
from langflow.field_typing import LanguageModel
from langflow.inputs import MessageTextInput
from langflow.field_typing.range_spec import RangeSpec
from langflow.inputs import IntInput, StrInput, DropdownInput
from langflow.io import Output
from langflow.schema.message import Message
from langflow.custom import Component
from langflow.schema import Data

# Define available models and their metadata
MODELS_METADATA = {
    "gpt-4o": {"icon": "brain", "description": "GPT-4o - Latest and most capable model (128K context)"},
    "gpt-4o-mini": {"icon": "brain", "description": "GPT-4o-mini - Fast and cost-effective (128K context)"},
    "gpt-4-turbo": {"icon": "brain", "description": "GPT-4 Turbo - High performance with 128K context"},
    "gpt-4-turbo-preview": {"icon": "brain", "description": "GPT-4 Turbo Preview - Latest preview version"},
    "gpt-4": {"icon": "brain", "description": "GPT-4 - Original GPT-4 model (8K context)"},
    "gpt-3.5-turbo": {"icon": "brain", "description": "GPT-3.5 Turbo - Fast and efficient (16K context)"},
    "gpt-3.5-turbo-16k": {"icon": "brain", "description": "GPT-3.5 Turbo 16K - Extended context version"},
}

class DeepQResearchTool(Component):
    """A tool that performs deep research on a given topic using Tavily search and OpenAI."""
    
    display_name = "DeepQ Research Tool"
    description = "Performs comprehensive deep research on a topic using Tavily search and OpenAI."
    icon = "🔍"
    name = "DeepQResearchTool"
    
    inputs = [
        MessageTextInput(
            name="topic",
            display_name="Research Topic",
            info="The topic or question to research",
            required=True,
            tool_mode=True,
        ),
        IntInput(
            name="cycles",
            display_name="Research Cycles",
            info="Number of research cycles (1-5)",
            value=2,
            range_spec=RangeSpec(min=1, max=5),
        ),
        StrInput(
            name="tavily_api_key",
            display_name="Tavily API Key",
            info="Your Tavily API key for search functionality",
            required=True,
        ),
        StrInput(
            name="openai_api_key",
            display_name="OpenAI API Key",
            info="Your OpenAI API key for AI processing",
            required=True,
        ),
        DropdownInput(
            name="openai_model",
            display_name="OpenAI Model",
            info="Select the OpenAI model to use for research",
            options=list(MODELS_METADATA.keys()),
            value="gpt-4o-mini",
            options_metadata=[MODELS_METADATA[model] for model in MODELS_METADATA.keys()],
        ),
    ]
    
    outputs = [
        Output(
            display_name="Research Results",
            name="research_results",
            method="get_research_results",
        ),
        Output(
            display_name="JSON Data",
            name="json_data", 
            method="get_json_data",
        ),
    ]
    
    def _make_api_request(self) -> Dict[str, Any]:
        """Make the API request to the research service."""
        try:
            # Try localhost first, then docker internal
            api_urls = ["http://localhost:8771/research", "http://host.docker.internal:8771/research"]
            
            payload = {
                "topic": self.topic,
                "cycles": self.cycles,
                "tavily_api_key": self.tavily_api_key,
                "openai_api_key": self.openai_api_key,
                "openai_model": self.openai_model,
                "output_file": "report.md"
            }
            
            for api_url in api_urls:
                try:
                    response = requests.post(
                        api_url,
                        json=payload,
                        headers={"Content-Type": "application/json"},
                        timeout=300
                    )
                    response.raise_for_status()
                    return response.json()
                except requests.exceptions.ConnectionError:
                    continue
            
            raise Exception("Could not connect to research API on any URL")
            
        except Exception as e:
            return {
                "error": str(e),
                "topic": self.topic,
                "status": "failed"
            }
    
    def get_research_results(self) -> Message:
        """Return formatted research results as a Message object."""
        result = self._make_api_request()
        
        if "error" in result:
            text = f"Error performing research: {result['error']}"
        else:
            # Format the response
            formatted_response = []
            
            if "final_summary" in result:
                formatted_response.append(f"Summary:\n{result['final_summary']}\n")
                
            if "final_report" in result:
                formatted_response.append(f"Detailed Report:\n{result['final_report']}\n")
                
            if "all_search_results" in result and isinstance(result["all_search_results"], list):
                formatted_response.append("\nSources:")
                for i, source in enumerate(result["all_search_results"][:5], 1):
                    if isinstance(source, dict):
                        title = source.get("title", f"Source {i}")
                        url = source.get("url", "")
                        formatted_response.append(f"{i}. {title}")
                        if url:
                            formatted_response.append(f"   URL: {url}")
                
                if len(result["all_search_results"]) > 5:
                    formatted_response.append(f"... and {len(result['all_search_results']) - 5} more sources")
            
            text = "\n".join(formatted_response)
            
        return Message(
            text=text,
            sender="DeepQ Research Tool",
            sender_name="Research Assistant"
        )
    
    def get_json_data(self) -> Message:
        """Return raw JSON data as Message object"""
        result = self._make_api_request()
        json_text = json.dumps(result, indent=2, ensure_ascii=False)
        
        return Message(
            text=json_text,
            sender="DeepQ Research Tool",
            sender_name="JSON Data"
        )

    def build(self):
        return self.get_research_results

# Keep the original DeepQComponent for backward compatibility
class DeepQComponent(LCModelComponent):
    display_name = "DeepQ"
    description = "Advanced research agent powered by DeepQ that performs comprehensive deep research on topics using Tavily search and OpenAI."
    icon = "🧠"
    name = "DeepQ"
    
    inputs = [
        MessageTextInput(
            name="topic",
            display_name="Research Topic",
            info="The topic or question to research",
            required=True,
        ),
        IntInput(
            name="cycles",
            display_name="Research Cycles",
            info="Number of research cycles (1-5)",
            value=2,
            range_spec=RangeSpec(min=1, max=5),
        ),
        StrInput(
            name="tavily_api_key",
            display_name="Tavily API Key",
            info="Your Tavily API key for search functionality",
            required=True,
        ),
        StrInput(
            name="openai_api_key",
            display_name="OpenAI API Key",
            info="Your OpenAI API key for AI processing",
            required=True,
        ),
        DropdownInput(
            name="openai_model",
            display_name="OpenAI Model",
            info="Select the OpenAI model to use for research",
            options=list(MODELS_METADATA.keys()),
            value="gpt-4o-mini",
            options_metadata=[MODELS_METADATA[model] for model in MODELS_METADATA.keys()],
        ),
    ]
    
    outputs = [
        Output(
            display_name="Research Results",
            name="research_results",
            method="get_research_message",
        ),
        Output(
            display_name="JSON Data",
            name="json_data", 
            method="get_json_data",
        ),
        Output(
            display_name="Text Output",
            name="text_output",
            method="get_text_output",
        ),
    ]
    
    def build_model(self) -> LanguageModel:
        return self
    
    def _make_api_request(self) -> Dict[str, Any]:
        """Make the API request and return JSON response"""
        try:
            # Try localhost first, then docker internal
            api_urls = ["http://localhost:8771/research", "http://host.docker.internal:8771/research"]
            
            payload = {
                "topic": self.topic,
                "cycles": self.cycles,
                "tavily_api_key": self.tavily_api_key,
                "openai_api_key": self.openai_api_key,
                "openai_model": self.openai_model,
                "output_file": "report.md"
            }
            
            for api_url in api_urls:
                try:
                    response = requests.post(
                        api_url,
                        json=payload,
                        headers={"Content-Type": "application/json"},
                        timeout=300
                    )
                    response.raise_for_status()
                    return response.json()
                except requests.exceptions.ConnectionError:
                    continue
            
            raise Exception("Could not connect to research API on any URL")
            
        except Exception as e:
            return {
                "error": str(e),
                "topic": self.topic,
                "status": "failed"
            }
    
    def get_research_message(self) -> Message:
        """Return only the final report as Message object, without repeating the question/topic."""
        json_response = self._make_api_request()
        if "error" in json_response:
            text = f"Error making research request: {json_response['error']}"
        else:
            # Only show the final_report, no topic/question heading
            text = json_response.get('final_report', 'No final report available.')
        return Message(
            text=text,
            sender="DeepQ",
            sender_name="Research Assistant"
        )
    
    def get_json_data(self) -> Message:
        """Return raw JSON data as Message object"""
        json_response = self._make_api_request()
        json_text = json.dumps(json_response, indent=2, ensure_ascii=False)
        
        return Message(
            text=json_text,
            sender="DeepQ",
            sender_name="JSON Data"
        )
    
    def get_text_output(self) -> str:
        """Return JSON as string for Text Output"""
        json_response = self._make_api_request()
        return json.dumps(json_response, indent=2, ensure_ascii=False)


# JSON Formatter Component - Compatible with above
from langflow.custom import Component
from langflow.io import HandleInput, Output, DropdownInput
from langflow.schema.message import Message

class JSONFormatterComponent(Component):
    display_name = "JSON Formatter"
    description = "Takes JSON input, formats it nicely, and outputs it as a clean message for Chat Output"
    icon = "FileText"
    name = "JSONFormatter"
    
    inputs = [
        HandleInput(
            name="json_input",
            display_name="JSON Input",
            info="Input from DeepQ or any JSON source",
            input_types=["Message", "Data", "str"],
            required=True,
        ),
        DropdownInput(
            name="format_type",
            display_name="Format Type",
            info="How to format the JSON output",
            options=["Pretty JSON", "Markdown Summary", "Key Points", "Raw Text", "Final Report Only"],
            value="Markdown Summary",
        ),
    ]
    
    outputs = [
        Output(
            display_name="Formatted Output",
            name="formatted_output",
            method="format_json",
        ),
    ]
    
    def format_json(self) -> Message:
        """Format the JSON input based on the selected format type"""
        try:
            # Extract the text content from the input
            if hasattr(self.json_input, 'text'):
                input_text = self.json_input.text
            elif isinstance(self.json_input, str):
                input_text = self.json_input
            else:
                input_text = str(self.json_input)
            
            # Try to parse as JSON
            try:
                json_data = json.loads(input_text)
            except json.JSONDecodeError:
                # If not valid JSON, return as is
                return Message(
                    text=f"Input is not valid JSON, returning as text:\n\n{input_text}",
                    sender="JSON Formatter"
                )
            
            # Format based on selected type
            if self.format_type == "Pretty JSON":
                formatted_text = json.dumps(json_data, indent=2, ensure_ascii=False)
                formatted_text = f"```json\n{formatted_text}\n```"
                
            elif self.format_type == "Markdown Summary":
                formatted_text = self._format_as_markdown(json_data)
                
            elif self.format_type == "Key Points":
                formatted_text = self._format_as_key_points(json_data)
                
            elif self.format_type == "Final Report Only":
                formatted_text = self._format_final_report(json_data)
                
            else:  # Raw Text
                formatted_text = self._format_as_raw_text(json_data)
            
            return Message(
                text=formatted_text,
                sender="JSON Formatter"
            )
            
        except Exception as e:
            error_msg = f"Error formatting JSON: {str(e)}\n\nOriginal input:\n{self.json_input}"
            return Message(
                text=error_msg,
                sender="JSON Formatter"
            )
    
    def _format_as_markdown(self, data: Dict[str, Any]) -> str:
        """Convert JSON to a nice markdown format"""
        if not isinstance(data, dict):
            return f"**Data:** {str(data)}"
        
        markdown = ""
        
        # Handle error responses
        if 'error' in data:
            markdown += f"# Research Error\n\n**Error:** {data['error']}\n\n"
            if 'topic' in data:
                markdown += f"**Topic:** {data['topic']}\n\n"
            return markdown
        
        # Handle successful research responses
        if 'topic' in data:
            markdown += f"# Research Report: {data['topic']}\n\n"
        
        if 'final_summary' in data:
            markdown += f"## Summary\n{data['final_summary']}\n\n"
        
        if 'final_report' in data:
            markdown += f"## Final Report\n{data['final_report']}\n\n"
        
        if 'research_cycles_completed' in data:
            markdown += f"**Research Cycles:** {data['research_cycles_completed']}\n\n"
        
        if 'all_search_results' in data and isinstance(data['all_search_results'], list):
            markdown += f"**Sources Analyzed:** {len(data['all_search_results'])}\n\n"
            
            # Show top sources
            if len(data['all_search_results']) > 0:
                markdown += "### Key Sources:\n"
                for i, result in enumerate(data['all_search_results'][:5]):  # Show first 5
                    if isinstance(result, dict):
                        if 'url' in result:
                            title = result.get('title', f'Source {i+1}')
                            url = result['url']
                            markdown += f"- [{title}]({url})\n"
                        elif 'title' in result:
                            markdown += f"- {result['title']}\n"
                        else:
                            markdown += f"- Source {i+1}\n"
                if len(data['all_search_results']) > 5:
                    markdown += f"- ... and {len(data['all_search_results']) - 5} more sources\n"
                markdown += "\n"
        
        # Add any other fields
        for key, value in data.items():
            if key not in ['topic', 'final_summary', 'final_report', 'research_cycles_completed', 'all_search_results', 'error']:
                if isinstance(value, (str, int, float, bool)):
                    markdown += f"**{key.replace('_', ' ').title()}:** {value}\n\n"
        
        return markdown
    
    def _format_as_key_points(self, data: Dict[str, Any]) -> str:
        """Extract key points from the JSON"""
        if not isinstance(data, dict):
            return f"• {str(data)}"
        
        points = []
        
        if 'error' in data:
            points.append(f"❌ **Error:** {data['error']}")
            if 'topic' in data:
                points.append(f"📋 **Topic:** {data['topic']}")
            return "\n".join(f"• {point}" for point in points)
        
        if 'topic' in data:
            points.append(f"📋 **Topic:** {data['topic']}")
        
        if 'final_summary' in data:
            summary = data['final_summary'][:200] + "..." if len(str(data['final_summary'])) > 200 else data['final_summary']
            points.append(f"📝 **Summary:** {summary}")
        
        if 'research_cycles_completed' in data:
            points.append(f"🔄 **Research Cycles:** {data['research_cycles_completed']}")
        
        if 'all_search_results' in data and isinstance(data['all_search_results'], list):
            points.append(f"📚 **Sources:** {len(data['all_search_results'])} analyzed")
        
        return "\n".join(f"• {point}" for point in points)
    
    def _format_as_raw_text(self, data: Dict[str, Any]) -> str:
        """Convert JSON to plain text"""
        if isinstance(data, dict):
            text_parts = []
            for key, value in data.items():
                if isinstance(value, (str, int, float, bool)):
                    text_parts.append(f"{key}: {value}")
                elif isinstance(value, list):
                    text_parts.append(f"{key}: {len(value)} items")
                else:
                    text_parts.append(f"{key}: {type(value).__name__}")
            return "\n".join(text_parts)
        else:
            return str(data)

    def _format_final_report(self, data: Dict[str, Any]) -> str:
        """Show only the final report section."""
        if not isinstance(data, dict):
            return str(data)
        report = ""
        if 'topic' in data:
            report += f"# {data['topic']}\n\n"
        if 'final_report' in data:
            report += data['final_report']
        else:
            report += "No final report available."
        return report


        