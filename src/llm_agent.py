"""LLM agent for task interpretation and execution using OpenAI function calling."""

import json
from typing import Any, Dict, List, Optional, Union
import asyncio

from openai import AsyncOpenAI
from openai.types.chat import ChatCompletionMessageParam

from src.models import TaskDefinition, AnswerFormat
from src.web_scraper import WebScraper
from src.data_processor import DataProcessor
from src.analysis_engine import AnalysisEngine
from src.chart_generator import ChartGenerator
from src.logging_config import get_logger
from src.config import settings

logger = get_logger(__name__)


class LLMAgent:
    """
    LLM agent that interprets tasks and coordinates tool execution.
    
    Uses OpenAI's function calling to orchestrate data sourcing, processing,
    analysis, and visualization tasks.
    """
    
    def __init__(
        self,
        model: str = None,
        api_key: str = None
    ):
        """
        Initialize the LLM agent.
        
        Args:
            model: OpenAI model to use (defaults to settings.openai_model)
            api_key: OpenAI API key (defaults to settings.openai_api_key)
        """
        self.model = model or settings.openai_model
        self.api_key = api_key or settings.openai_api_key
        self.client = AsyncOpenAI(api_key=self.api_key)
        
        # Initialize tool components
        self.scraper = WebScraper()
        self.processor = DataProcessor()
        self.analyzer = AnalysisEngine()
        self.chart_gen = ChartGenerator()
        
        # Tool execution context
        self.context: Dict[str, Any] = {}
        
        logger.info(f"LLMAgent initialized with model: {self.model}")
    
    async def solve_task(self, task: TaskDefinition) -> Any:
        """
        Solve a task using LLM interpretation and tool execution.
        
        Supports multi-modal tasks including text, vision, and audio processing.
        
        Args:
            task: Parsed task definition
        
        Returns:
            Answer in the format specified by task.answer_format
        
        Raises:
            Exception: If task solving fails
        """
        logger.info(f"Solving task with format: {task.answer_format}")
        
        # Reset context for new task
        self.context = {
            'task': task,
            'files': {},
            'dataframes': {},
            'results': {},
            'images': {},
            'audio': {}
        }
        
        try:
            # Detect if task requires multi-modal capabilities
            requires_vision = self._requires_vision(task)
            requires_audio = self._requires_audio(task)
            
            # Select appropriate model
            model = self._select_model(requires_vision, requires_audio)
            
            # Build initial messages
            messages = self._build_initial_messages(task)
            
            # Execute LLM loop with function calling
            answer = await self._execute_llm_loop(messages, task.answer_format, model)
            
            logger.info(f"Task solved successfully, answer type: {type(answer)}")
            return answer
            
        except Exception as e:
            logger.error(f"Error solving task: {str(e)}")
            raise
    
    def _requires_vision(self, task: TaskDefinition) -> bool:
        """Check if task requires vision capabilities."""
        # Check for image file URLs
        for url in task.file_urls:
            url_str = str(url).lower()
            if any(ext in url_str for ext in ['.png', '.jpg', '.jpeg', '.gif', '.bmp', '.webp']):
                return True
        
        # Check instructions for vision-related keywords
        instructions_lower = task.instructions.lower()
        vision_keywords = ['image', 'picture', 'photo', 'visual', 'chart', 'diagram']
        return any(keyword in instructions_lower for keyword in vision_keywords)
    
    def _requires_audio(self, task: TaskDefinition) -> bool:
        """Check if task requires audio capabilities."""
        # Check for audio file URLs
        for url in task.file_urls:
            url_str = str(url).lower()
            if any(ext in url_str for ext in ['.mp3', '.wav', '.m4a', '.ogg', '.flac']):
                return True
        
        # Check instructions for audio-related keywords
        instructions_lower = task.instructions.lower()
        audio_keywords = ['audio', 'sound', 'speech', 'transcribe', 'voice']
        return any(keyword in instructions_lower for keyword in audio_keywords)
    
    def _select_model(self, requires_vision: bool, requires_audio: bool) -> str:
        """
        Select appropriate model based on task requirements.
        
        Args:
            requires_vision: Whether task requires vision capabilities
            requires_audio: Whether task requires audio capabilities
        
        Returns:
            Model identifier
        """
        if requires_vision:
            # Use vision-capable model
            model = "gpt-4o" if "gpt-4" in self.model else self.model
            logger.info(f"Using vision model: {model}")
            return model
        elif requires_audio:
            # Audio transcription handled separately via Whisper
            logger.info("Task requires audio processing")
            return self.model
        else:
            return self.model
    
    async def _call_llm_with_retry(
        self,
        model: str,
        messages: List[ChatCompletionMessageParam],
        tools: List[Dict[str, Any]],
        max_retries: int = 3
    ) -> Any:
        """
        Call LLM API with retry logic for rate limits and errors.
        
        Args:
            model: Model to use
            messages: Conversation messages
            tools: Tool definitions
            max_retries: Maximum number of retries
        
        Returns:
            API response
        
        Raises:
            Exception: If all retries fail
        """
        from openai import RateLimitError, APIError
        
        for attempt in range(max_retries):
            try:
                response = await self.client.chat.completions.create(
                    model=model,
                    messages=messages,
                    tools=tools,
                    tool_choice="auto"
                )
                return response
            
            except RateLimitError as e:
                if attempt < max_retries - 1:
                    wait_time = 2 ** attempt  # Exponential backoff
                    logger.warning(f"Rate limit hit, retrying in {wait_time}s...")
                    await asyncio.sleep(wait_time)
                else:
                    logger.error("Rate limit exceeded, max retries reached")
                    raise
            
            except APIError as e:
                if attempt < max_retries - 1:
                    wait_time = 2 ** attempt
                    logger.warning(f"API error, retrying in {wait_time}s: {str(e)}")
                    await asyncio.sleep(wait_time)
                else:
                    logger.error("API error, max retries reached")
                    raise
            
            except Exception as e:
                logger.error(f"Unexpected error calling LLM: {str(e)}")
                raise
    
    def _build_initial_messages(
        self,
        task: TaskDefinition
    ) -> List[ChatCompletionMessageParam]:
        """Build initial message context for LLM."""
        system_prompt = self._get_system_prompt()
        user_prompt = self._get_user_prompt(task)
        
        messages: List[ChatCompletionMessageParam] = [
            {"role": "system", "content": system_prompt},
            {"role": "user", "content": user_prompt}
        ]
        
        return messages

    def _get_system_prompt(self) -> str:
        """Get system prompt for task interpretation."""
        return """You are a data analysis assistant that helps solve data-related tasks.

You have access to the following tools:
- download_file: Download files from URLs
- parse_file: Parse files (PDF, CSV, JSON) into structured data
- filter_data: Filter data based on conditions
- aggregate_data: Perform aggregations (sum, count, mean, etc.)
- analyze_data: Perform statistical analysis
- create_chart: Generate visualizations

Your job is to:
1. Understand the task requirements
2. Use tools to download and process data
3. Perform required analysis
4. Return the final answer in the specified format

Always think step-by-step and use tools systematically. Store intermediate results for later use."""
    
    def _get_user_prompt(self, task: TaskDefinition) -> str:
        """Get user prompt with task details."""
        prompt = f"""Task Instructions:
{task.instructions}

Required Answer Format: {task.answer_format.value}

"""
        
        if task.file_urls:
            prompt += f"Files to process:\n"
            for i, url in enumerate(task.file_urls, 1):
                prompt += f"{i}. {url}\n"
            prompt += "\n"
        
        if task.additional_context:
            prompt += f"Additional Context:\n{json.dumps(task.additional_context, indent=2)}\n\n"
        
        prompt += "Please solve this task step by step using the available tools."
        
        return prompt
    
    async def _execute_llm_loop(
        self,
        messages: List[ChatCompletionMessageParam],
        answer_format: AnswerFormat,
        model: Optional[str] = None,
        max_iterations: int = 10
    ) -> Any:
        """
        Execute LLM loop with function calling.
        
        Args:
            messages: Conversation messages
            answer_format: Required answer format
            model: Model to use (defaults to self.model)
            max_iterations: Maximum number of LLM calls
        
        Returns:
            Final answer in specified format
        """
        tools = self._get_tool_definitions()
        model = model or self.model
        
        for iteration in range(max_iterations):
            logger.debug(f"LLM iteration {iteration + 1}/{max_iterations}")
            
            # Call LLM with function calling and error handling
            try:
                response = await self._call_llm_with_retry(
                    model=model,
                    messages=messages,
                    tools=tools
                )
            except Exception as e:
                logger.error(f"LLM API call failed: {str(e)}")
                raise
            
            message = response.choices[0].message
            
            # Check if LLM wants to call functions
            if message.tool_calls:
                # Add assistant message to history
                messages.append({
                    "role": "assistant",
                    "content": message.content,
                    "tool_calls": [
                        {
                            "id": tc.id,
                            "type": tc.type,
                            "function": {
                                "name": tc.function.name,
                                "arguments": tc.function.arguments
                            }
                        }
                        for tc in message.tool_calls
                    ]
                })
                
                # Execute tool calls
                for tool_call in message.tool_calls:
                    function_name = tool_call.function.name
                    function_args = json.loads(tool_call.function.arguments)
                    
                    logger.info(f"Executing tool: {function_name}")
                    
                    # Execute the tool
                    try:
                        result = await self._execute_tool(function_name, function_args)
                        result_str = json.dumps(result, default=str)
                    except Exception as e:
                        logger.error(f"Tool execution error: {str(e)}")
                        result_str = json.dumps({"error": str(e)})
                    
                    # Add tool result to messages
                    messages.append({
                        "role": "tool",
                        "tool_call_id": tool_call.id,
                        "content": result_str
                    })
            
            else:
                # LLM provided final answer
                final_content = message.content
                logger.info("LLM provided final answer")
                
                # Parse answer based on format
                answer = self._parse_answer(final_content, answer_format)
                return answer
        
        # Max iterations reached
        logger.warning("Max iterations reached without final answer")
        raise RuntimeError("LLM did not provide final answer within iteration limit")
    
    def _get_tool_definitions(self) -> List[Dict[str, Any]]:
        """Get OpenAI function definitions for available tools."""
        return [
            {
                "type": "function",
                "function": {
                    "name": "download_file",
                    "description": "Download a file from a URL",
                    "parameters": {
                        "type": "object",
                        "properties": {
                            "url": {
                                "type": "string",
                                "description": "URL of the file to download"
                            },
                            "file_id": {
                                "type": "string",
                                "description": "Identifier to store the file (e.g., 'data_file', 'pdf_doc')"
                            },
                            "headers": {
                                "type": "object",
                                "description": "Optional HTTP headers for authentication",
                                "additionalProperties": {"type": "string"}
                            }
                        },
                        "required": ["url", "file_id"]
                    }
                }
            },
            {
                "type": "function",
                "function": {
                    "name": "parse_file",
                    "description": "Parse a downloaded file into structured data",
                    "parameters": {
                        "type": "object",
                        "properties": {
                            "file_id": {
                                "type": "string",
                                "description": "Identifier of the downloaded file"
                            },
                            "file_type": {
                                "type": "string",
                                "enum": ["pdf", "csv", "json"],
                                "description": "Type of file to parse"
                            },
                            "df_id": {
                                "type": "string",
                                "description": "Identifier to store the parsed DataFrame"
                            },
                            "options": {
                                "type": "object",
                                "description": "Parsing options (e.g., page number for PDF)",
                                "properties": {
                                    "page": {"type": "integer"},
                                    "normalize": {"type": "boolean"}
                                }
                            }
                        },
                        "required": ["file_id", "file_type", "df_id"]
                    }
                }
            },
            {
                "type": "function",
                "function": {
                    "name": "filter_data",
                    "description": "Filter a DataFrame based on conditions",
                    "parameters": {
                        "type": "object",
                        "properties": {
                            "df_id": {
                                "type": "string",
                                "description": "Identifier of the DataFrame to filter"
                            },
                            "conditions": {
                                "type": "array",
                                "description": "List of filter conditions",
                                "items": {
                                    "type": "object",
                                    "properties": {
                                        "column": {"type": "string"},
                                        "operator": {
                                            "type": "string",
                                            "enum": ["==", "!=", ">", "<", ">=", "<=", "in", "not_in", "contains"]
                                        },
                                        "value": {}
                                    },
                                    "required": ["column", "operator", "value"]
                                }
                            },
                            "result_id": {
                                "type": "string",
                                "description": "Identifier to store the filtered DataFrame"
                            }
                        },
                        "required": ["df_id", "conditions", "result_id"]
                    }
                }
            },
            {
                "type": "function",
                "function": {
                    "name": "aggregate_data",
                    "description": "Perform aggregation operations on a DataFrame",
                    "parameters": {
                        "type": "object",
                        "properties": {
                            "df_id": {
                                "type": "string",
                                "description": "Identifier of the DataFrame to aggregate"
                            },
                            "operations": {
                                "type": "object",
                                "description": "Aggregation operations (column: function)",
                                "additionalProperties": {"type": "string"}
                            },
                            "group_by": {
                                "type": "string",
                                "description": "Optional column to group by"
                            },
                            "result_id": {
                                "type": "string",
                                "description": "Identifier to store the result"
                            }
                        },
                        "required": ["df_id", "operations", "result_id"]
                    }
                }
            },
            {
                "type": "function",
                "function": {
                    "name": "analyze_data",
                    "description": "Perform statistical analysis on data",
                    "parameters": {
                        "type": "object",
                        "properties": {
                            "df_id": {
                                "type": "string",
                                "description": "Identifier of the DataFrame to analyze"
                            },
                            "analysis_type": {
                                "type": "string",
                                "enum": ["statistics", "correlation", "value_counts", "sort"],
                                "description": "Type of analysis to perform"
                            },
                            "options": {
                                "type": "object",
                                "description": "Analysis-specific options"
                            },
                            "result_id": {
                                "type": "string",
                                "description": "Identifier to store the result"
                            }
                        },
                        "required": ["df_id", "analysis_type", "result_id"]
                    }
                }
            },
            {
                "type": "function",
                "function": {
                    "name": "create_chart",
                    "description": "Create a visualization chart",
                    "parameters": {
                        "type": "object",
                        "properties": {
                            "df_id": {
                                "type": "string",
                                "description": "Identifier of the DataFrame to visualize"
                            },
                            "chart_type": {
                                "type": "string",
                                "enum": ["bar", "line", "scatter", "pie"],
                                "description": "Type of chart to create"
                            },
                            "config": {
                                "type": "object",
                                "description": "Chart configuration (x, y, title, etc.)",
                                "properties": {
                                    "x": {"type": "string"},
                                    "y": {},
                                    "title": {"type": "string"},
                                    "xlabel": {"type": "string"},
                                    "ylabel": {"type": "string"}
                                }
                            },
                            "result_id": {
                                "type": "string",
                                "description": "Identifier to store the chart (base64 URI)"
                            }
                        },
                        "required": ["df_id", "chart_type", "config", "result_id"]
                    }
                }
            },
            {
                "type": "function",
                "function": {
                    "name": "get_value",
                    "description": "Get a specific value from stored results",
                    "parameters": {
                        "type": "object",
                        "properties": {
                            "result_id": {
                                "type": "string",
                                "description": "Identifier of the stored result"
                            },
                            "path": {
                                "type": "string",
                                "description": "Optional path to extract specific value (e.g., 'column_name', 'row[0]')"
                            }
                        },
                        "required": ["result_id"]
                    }
                }
            },
            {
                "type": "function",
                "function": {
                    "name": "process_image",
                    "description": "Process an image file for analysis",
                    "parameters": {
                        "type": "object",
                        "properties": {
                            "file_id": {
                                "type": "string",
                                "description": "Identifier of the downloaded image file"
                            },
                            "image_id": {
                                "type": "string",
                                "description": "Identifier to store the processed image"
                            }
                        },
                        "required": ["file_id", "image_id"]
                    }
                }
            },
            {
                "type": "function",
                "function": {
                    "name": "analyze_image",
                    "description": "Analyze an image using vision model",
                    "parameters": {
                        "type": "object",
                        "properties": {
                            "image_id": {
                                "type": "string",
                                "description": "Identifier of the processed image"
                            },
                            "prompt": {
                                "type": "string",
                                "description": "Question or instruction for image analysis"
                            },
                            "result_id": {
                                "type": "string",
                                "description": "Identifier to store the analysis result"
                            }
                        },
                        "required": ["image_id", "prompt", "result_id"]
                    }
                }
            },
            {
                "type": "function",
                "function": {
                    "name": "transcribe_audio",
                    "description": "Transcribe audio file to text using Whisper",
                    "parameters": {
                        "type": "object",
                        "properties": {
                            "file_id": {
                                "type": "string",
                                "description": "Identifier of the downloaded audio file"
                            },
                            "result_id": {
                                "type": "string",
                                "description": "Identifier to store the transcription"
                            }
                        },
                        "required": ["file_id", "result_id"]
                    }
                }
            }
        ]

    async def _execute_tool(
        self,
        function_name: str,
        function_args: Dict[str, Any]
    ) -> Dict[str, Any]:
        """
        Execute a tool function.
        
        Args:
            function_name: Name of the tool to execute
            function_args: Arguments for the tool
        
        Returns:
            Tool execution result
        """
        logger.debug(f"Executing {function_name} with args: {function_args}")
        
        try:
            if function_name == "download_file":
                return await self._tool_download_file(**function_args)
            
            elif function_name == "parse_file":
                return await self._tool_parse_file(**function_args)
            
            elif function_name == "filter_data":
                return await self._tool_filter_data(**function_args)
            
            elif function_name == "aggregate_data":
                return await self._tool_aggregate_data(**function_args)
            
            elif function_name == "analyze_data":
                return await self._tool_analyze_data(**function_args)
            
            elif function_name == "create_chart":
                return await self._tool_create_chart(**function_args)
            
            elif function_name == "get_value":
                return await self._tool_get_value(**function_args)
            
            elif function_name == "process_image":
                return await self._tool_process_image(**function_args)
            
            elif function_name == "analyze_image":
                return await self._tool_analyze_image(**function_args)
            
            elif function_name == "transcribe_audio":
                return await self._tool_transcribe_audio(**function_args)
            
            else:
                raise ValueError(f"Unknown tool: {function_name}")
        
        except Exception as e:
            logger.error(f"Tool execution failed: {str(e)}")
            return {"success": False, "error": str(e)}
    
    async def _tool_download_file(
        self,
        url: str,
        file_id: str,
        headers: Optional[Dict[str, str]] = None
    ) -> Dict[str, Any]:
        """Download a file and store it in context."""
        try:
            file_bytes = await self.scraper.download_file(url, headers)
            self.context['files'][file_id] = file_bytes
            
            return {
                "success": True,
                "file_id": file_id,
                "size": len(file_bytes),
                "message": f"Downloaded {len(file_bytes)} bytes"
            }
        except Exception as e:
            return {"success": False, "error": str(e)}
    
    async def _tool_parse_file(
        self,
        file_id: str,
        file_type: str,
        df_id: str,
        options: Optional[Dict[str, Any]] = None
    ) -> Dict[str, Any]:
        """Parse a file into structured data."""
        try:
            if file_id not in self.context['files']:
                return {"success": False, "error": f"File '{file_id}' not found"}
            
            file_bytes = self.context['files'][file_id]
            options = options or {}
            
            if file_type == "pdf":
                page = options.get('page')
                df = self.processor.extract_pdf_table(file_bytes, page)
            elif file_type == "csv":
                df = self.processor.parse_csv(file_bytes)
            elif file_type == "json":
                normalize = options.get('normalize', True)
                result = self.processor.parse_json(file_bytes, normalize)
                # If result is not a DataFrame, store as-is
                if not hasattr(result, 'shape'):
                    self.context['results'][df_id] = result
                    return {
                        "success": True,
                        "df_id": df_id,
                        "type": type(result).__name__,
                        "message": f"Parsed JSON as {type(result).__name__}"
                    }
                df = result
            else:
                return {"success": False, "error": f"Unsupported file type: {file_type}"}
            
            self.context['dataframes'][df_id] = df
            
            return {
                "success": True,
                "df_id": df_id,
                "shape": df.shape,
                "columns": list(df.columns),
                "head": df.head(3).to_dict(orient='records')
            }
        except Exception as e:
            return {"success": False, "error": str(e)}
    
    async def _tool_filter_data(
        self,
        df_id: str,
        conditions: List[Dict[str, Any]],
        result_id: str
    ) -> Dict[str, Any]:
        """Filter a DataFrame."""
        try:
            if df_id not in self.context['dataframes']:
                return {"success": False, "error": f"DataFrame '{df_id}' not found"}
            
            df = self.context['dataframes'][df_id]
            filtered_df = self.analyzer.filter_data(df, conditions)
            self.context['dataframes'][result_id] = filtered_df
            
            return {
                "success": True,
                "result_id": result_id,
                "original_rows": len(df),
                "filtered_rows": len(filtered_df),
                "head": filtered_df.head(3).to_dict(orient='records')
            }
        except Exception as e:
            return {"success": False, "error": str(e)}
    
    async def _tool_aggregate_data(
        self,
        df_id: str,
        operations: Dict[str, str],
        result_id: str,
        group_by: Optional[str] = None
    ) -> Dict[str, Any]:
        """Aggregate a DataFrame."""
        try:
            if df_id not in self.context['dataframes']:
                return {"success": False, "error": f"DataFrame '{df_id}' not found"}
            
            df = self.context['dataframes'][df_id]
            result = self.analyzer.aggregate(df, operations, group_by)
            
            # Store result
            if hasattr(result, 'shape'):
                self.context['dataframes'][result_id] = result
                return {
                    "success": True,
                    "result_id": result_id,
                    "shape": result.shape,
                    "result": result.to_dict(orient='records') if len(result) <= 10 else result.head(10).to_dict(orient='records')
                }
            else:
                self.context['results'][result_id] = result
                return {
                    "success": True,
                    "result_id": result_id,
                    "result": result.to_dict() if hasattr(result, 'to_dict') else str(result)
                }
        except Exception as e:
            return {"success": False, "error": str(e)}
    
    async def _tool_analyze_data(
        self,
        df_id: str,
        analysis_type: str,
        result_id: str,
        options: Optional[Dict[str, Any]] = None
    ) -> Dict[str, Any]:
        """Perform statistical analysis."""
        try:
            if df_id not in self.context['dataframes']:
                return {"success": False, "error": f"DataFrame '{df_id}' not found"}
            
            df = self.context['dataframes'][df_id]
            options = options or {}
            
            if analysis_type == "statistics":
                columns = options.get('columns')
                stats = options.get('stats')
                result = self.analyzer.calculate_statistics(df, columns, stats)
            elif analysis_type == "correlation":
                method = options.get('method', 'pearson')
                columns = options.get('columns')
                result = self.analyzer.correlation_analysis(df, method, columns)
            elif analysis_type == "value_counts":
                column = options.get('column')
                if not column:
                    return {"success": False, "error": "column required for value_counts"}
                normalize = options.get('normalize', False)
                top_n = options.get('top_n')
                result = self.analyzer.value_counts(df, column, normalize, top_n)
            elif analysis_type == "sort":
                by = options.get('by')
                if not by:
                    return {"success": False, "error": "by required for sort"}
                ascending = options.get('ascending', True)
                result = self.analyzer.sort_data(df, by, ascending)
            else:
                return {"success": False, "error": f"Unknown analysis type: {analysis_type}"}
            
            # Store result
            if hasattr(result, 'shape'):
                self.context['dataframes'][result_id] = result
                return {
                    "success": True,
                    "result_id": result_id,
                    "shape": result.shape,
                    "result": result.to_dict(orient='records') if len(result) <= 10 else result.head(10).to_dict(orient='records')
                }
            else:
                self.context['results'][result_id] = result
                return {
                    "success": True,
                    "result_id": result_id,
                    "result": result.to_dict() if hasattr(result, 'to_dict') else str(result)
                }
        except Exception as e:
            return {"success": False, "error": str(e)}
    
    async def _tool_create_chart(
        self,
        df_id: str,
        chart_type: str,
        config: Dict[str, Any],
        result_id: str
    ) -> Dict[str, Any]:
        """Create a visualization chart."""
        try:
            if df_id not in self.context['dataframes']:
                return {"success": False, "error": f"DataFrame '{df_id}' not found"}
            
            df = self.context['dataframes'][df_id]
            base64_uri = self.chart_gen.create_chart(df, chart_type, config)
            self.context['results'][result_id] = base64_uri
            
            return {
                "success": True,
                "result_id": result_id,
                "size": len(base64_uri),
                "message": f"Created {chart_type} chart"
            }
        except Exception as e:
            return {"success": False, "error": str(e)}
    
    async def _tool_get_value(
        self,
        result_id: str,
        path: Optional[str] = None
    ) -> Dict[str, Any]:
        """Get a value from stored results."""
        try:
            # Check in results first
            if result_id in self.context['results']:
                value = self.context['results'][result_id]
                return {
                    "success": True,
                    "value": value,
                    "type": type(value).__name__
                }
            
            # Check in dataframes
            if result_id in self.context['dataframes']:
                df = self.context['dataframes'][result_id]
                
                if path:
                    # Extract specific value using path
                    # Simple path parsing (e.g., "column_name" or "iloc[0,1]")
                    if '[' in path:
                        # Handle indexing
                        value = eval(f"df.{path}")
                    else:
                        # Assume column name
                        value = df[path].tolist()
                else:
                    # Return full DataFrame as dict
                    value = df.to_dict(orient='records')
                
                return {
                    "success": True,
                    "value": value,
                    "type": type(value).__name__
                }
            
            return {"success": False, "error": f"Result '{result_id}' not found"}
        except Exception as e:
            return {"success": False, "error": str(e)}
    
    async def _tool_process_image(
        self,
        file_id: str,
        image_id: str
    ) -> Dict[str, Any]:
        """Process an image file."""
        try:
            if file_id not in self.context['files']:
                return {"success": False, "error": f"File '{file_id}' not found"}
            
            file_bytes = self.context['files'][file_id]
            image = self.processor.process_image(file_bytes)
            self.context['images'][image_id] = image
            
            return {
                "success": True,
                "image_id": image_id,
                "size": image.size,
                "mode": image.mode,
                "message": f"Processed image: {image.size[0]}x{image.size[1]}"
            }
        except Exception as e:
            return {"success": False, "error": str(e)}
    
    async def _tool_analyze_image(
        self,
        image_id: str,
        prompt: str,
        result_id: str
    ) -> Dict[str, Any]:
        """Analyze an image using vision model."""
        try:
            if image_id not in self.context['images']:
                return {"success": False, "error": f"Image '{image_id}' not found"}
            
            image = self.context['images'][image_id]
            
            # Convert image to base64 for API
            import io
            import base64
            buffer = io.BytesIO()
            image.save(buffer, format='PNG')
            buffer.seek(0)
            image_base64 = base64.b64encode(buffer.getvalue()).decode('utf-8')
            
            # Call vision model
            response = await self.client.chat.completions.create(
                model="gpt-4o",
                messages=[
                    {
                        "role": "user",
                        "content": [
                            {"type": "text", "text": prompt},
                            {
                                "type": "image_url",
                                "image_url": {
                                    "url": f"data:image/png;base64,{image_base64}"
                                }
                            }
                        ]
                    }
                ]
            )
            
            result = response.choices[0].message.content
            self.context['results'][result_id] = result
            
            return {
                "success": True,
                "result_id": result_id,
                "result": result
            }
        except Exception as e:
            return {"success": False, "error": str(e)}
    
    async def _tool_transcribe_audio(
        self,
        file_id: str,
        result_id: str
    ) -> Dict[str, Any]:
        """Transcribe audio file using Whisper."""
        try:
            if file_id not in self.context['files']:
                return {"success": False, "error": f"File '{file_id}' not found"}
            
            file_bytes = self.context['files'][file_id]
            
            # Save to temporary file for Whisper API
            import tempfile
            import os
            
            with tempfile.NamedTemporaryFile(delete=False, suffix='.mp3') as temp_file:
                temp_file.write(file_bytes)
                temp_path = temp_file.name
            
            try:
                # Call Whisper API
                with open(temp_path, 'rb') as audio_file:
                    transcription = await self.client.audio.transcriptions.create(
                        model="whisper-1",
                        file=audio_file
                    )
                
                result = transcription.text
                self.context['results'][result_id] = result
                
                return {
                    "success": True,
                    "result_id": result_id,
                    "transcription": result
                }
            finally:
                # Clean up temp file
                if os.path.exists(temp_path):
                    os.unlink(temp_path)
        
        except Exception as e:
            return {"success": False, "error": str(e)}
    
    def _parse_answer(self, content: str, answer_format: AnswerFormat) -> Any:
        """
        Parse LLM response into the required answer format.
        
        Args:
            content: LLM response content
            answer_format: Required answer format
        
        Returns:
            Parsed answer in the correct format
        """
        logger.info(f"Parsing answer as {answer_format.value}")
        
        # Clean content
        content = content.strip()
        
        try:
            if answer_format == AnswerFormat.BOOLEAN:
                # Parse boolean
                lower = content.lower()
                if 'true' in lower or 'yes' in lower:
                    return True
                elif 'false' in lower or 'no' in lower:
                    return False
                else:
                    # Try to parse as JSON
                    return bool(json.loads(content))
            
            elif answer_format == AnswerFormat.NUMBER:
                # Parse number
                # Try to extract number from text
                import re
                numbers = re.findall(r'-?\d+\.?\d*', content)
                if numbers:
                    num_str = numbers[0]
                    return float(num_str) if '.' in num_str else int(num_str)
                else:
                    return json.loads(content)
            
            elif answer_format == AnswerFormat.STRING:
                # Return as string
                # Try to extract from JSON if wrapped
                try:
                    parsed = json.loads(content)
                    if isinstance(parsed, str):
                        return parsed
                except:
                    pass
                return content
            
            elif answer_format == AnswerFormat.BASE64:
                # Should be a base64 data URI
                # Check if it's stored in context
                if content in self.context['results']:
                    return self.context['results'][content]
                # Otherwise return as-is
                return content
            
            elif answer_format == AnswerFormat.JSON:
                # Parse as JSON object
                try:
                    return json.loads(content)
                except json.JSONDecodeError:
                    # Try to extract JSON from markdown code blocks
                    import re
                    json_match = re.search(r'```(?:json)?\s*(\{.*?\})\s*```', content, re.DOTALL)
                    if json_match:
                        return json.loads(json_match.group(1))
                    # Try without code blocks
                    json_match = re.search(r'\{.*\}', content, re.DOTALL)
                    if json_match:
                        return json.loads(json_match.group(0))
                    raise
            
            else:
                logger.warning(f"Unknown answer format: {answer_format}")
                return content
        
        except Exception as e:
            logger.error(f"Error parsing answer: {str(e)}")
            # Return raw content as fallback
            return content
