import os
import argparse
import sys
import json
from dotenv import load_dotenv
from anthropic import Anthropic, HUMAN_PROMPT, AI_PROMPT
from tavily import TavilyClient
from colorama import init, Style
import signal

# Import helper functions and constants
from .utils import (
    print_colored, print_code, create_folder, create_file,
    write_to_file, read_file, list_files, encode_image_to_base64,
    USER_COLOR, CLAUDE_COLOR, TOOL_COLOR, RESULT_COLOR, ERROR_COLOR
)

# Initialize colorama
init()

# Load environment variables
load_dotenv()

# Initialize the Anthropic client
client = Anthropic(api_key=os.getenv("ANTHROPIC_API_KEY"))

# Initialize the Tavily client
tavily = TavilyClient(api_key=os.getenv("TAVILY_API_KEY"))

# Set up the conversation memory
conversation_history = []

# Available Claude models
CLAUDE_MODELS = {
    "opus": "claude-3-opus-20240229",
    "sonnet": "claude-3-sonnet-20240229",
    "haiku": "claude-3-haiku-20240307"
}

# Default model
DEFAULT_MODEL = "sonnet"

# System prompt
system_prompt = """
You are Claude, an AI assistant powered by Anthropic's Claude-3.5-Sonnet model. You are an exceptional software developer with vast knowledge across multiple programming languages, frameworks, and best practices. Your capabilities include:
1. Creating project structures, including folders and files
2. Writing clean, efficient, and well-documented code
3. Debugging complex issues and providing detailed explanations
4. Offering architectural insights and design patterns
5. Staying up-to-date with the latest technologies and industry trends
6. Reading and analyzing existing files in the project directory
7. Listing files in the root directory of the project
8. Performing web searches to get up-to-date information or additional context
9. When you use search make sure you use the best query to get the most accurate and up-to-date information
10. You NEVER remove existing code if doesnt require to be changed or removed, never use comments  like # ... (keep existing code) ... or # ... (rest of the code) ... etc, you only add new code or remove it.
11. Analyzing images provided by the user
When an image is provided, carefully analyze its contents and incorporate your observations into your responses.
When asked to create a project:
- Always start by creating a root folder for the project.
- Then, create the necessary subdirectories and files within that root folder.
- Organize the project structure logically and follow best practices for the specific type of project being created.
- Use the provided tools to create folders and files as needed.
When asked to make edits or improvements:
- Use the read_file tool to examine the contents of existing files.
- Analyze the code and suggest improvements or make necessary edits.
- Use the write_to_file tool to implement changes.
Be sure to consider the type of project (e.g., Python, JavaScript, web application) when determining the appropriate structure and files to include.
You can now read files, list the contents of the root folder where this script is being run, and perform web searches. Use these capabilities when:
- The user asks for edits or improvements to existing files
- You need to understand the current state of the project
- You believe reading a file or listing directory contents will be beneficial to accomplish the user's goal
- You need up-to-date information or additional context to answer a question accurately
When you need current information or feel that a search could provide a better answer, use the tavily_search tool. This tool performs a web search and returns a concise answer along with relevant sources.
Always strive to provide the most accurate, helpful, and detailed responses possible. If you're unsure about something, admit it and consider using the search tool to find the most current information.
Answer the user's request using relevant tools (if they are available). Before calling a tool, do some analysis within \\<thinking>\\</thinking> tags. First, think about which of the provided tools is the 
relevant tool to answer the user's request. Second, go through each of the required parameters of the relevant tool and determine if the user has directly provided or given enough information to infer a value. 
When deciding if the parameter can be inferred, carefully consider all the context to see if it supports a specific value. If all of the required parameters are present or can be reasonably inferred, close the 
thinking tag and proceed with the tool call. BUT, if one of the values for a required parameter is missing, DO NOT invoke the function (not even with fillers for the missing params) and instead, ask the user 
to provide the missing parameters. DO NOT ask for more information on optional parameters if it is not provided.
"""

# Initialize the Anthropic client
client = Anthropic(api_key=os.getenv("ANTHROPIC_API_KEY"))

# Initialize the Tavily client
tavily = TavilyClient(api_key=os.getenv("TAVILY_API_KEY"))

# Set up the conversation memory
conversation_history = []

# Define the tools
tools = [
    {
        "name": "create_folder",
        "description": "Create a new folder at the specified path. Use this when you need to create a new directory in the project structure.",
        "input_schema": {
            "type": "object",
            "properties": {
                "path": {
                    "type": "string",
                    "description": "The path where the folder should be created"
                }
            },
            "required": ["path"]
        }
    },
    {
        "name": "create_file",
        "description": "Create a new file at the specified path with optional content. Use this when you need to create a new file in the project structure.",
        "input_schema": {
            "type": "object",
            "properties": {
                "path": {
                    "type": "string",
                    "description": "The path where the file should be created"
                },
                "content": {
                    "type": "string",
                    "description": "The initial content of the file (optional)"
                }
            },
            "required": ["path"]
        }
    },
    {
        "name": "write_to_file",
        "description": "Write content to an existing file at the specified path. Use this when you need to add or update content in an existing file.",
        "input_schema": {
            "type": "object",
            "properties": {
                "path": {
                    "type": "string",
                    "description": "The path of the file to write to"
                },
                "content": {
                    "type": "string",
                    "description": "The content to write to the file"
                }
            },
            "required": ["path", "content"]
        }
    },
    {
        "name": "read_file",
        "description": "Read the contents of a file at the specified path. Use this when you need to examine the contents of an existing file.",
        "input_schema": {
            "type": "object",
            "properties": {
                "path": {
                    "type": "string",
                    "description": "The path of the file to read"
                }
            },
            "required": ["path"]
        }
    },
    {
        "name": "list_files",
        "description": "List all files and directories in the root folder where the script is running. Use this when you need to see the contents of the current directory.",
        "input_schema": {
            "type": "object",
            "properties": {
                "path": {
                    "type": "string",
                    "description": "The path of the folder to list (default: current directory)"
                }
            }
        }
    },
    {
        "name": "tavily_search",
        "description": "Perform a web search using Tavily API to get up-to-date information or additional context. Use this when you need current information or feel a search could provide a better answer.",
        "input_schema": {
            "type": "object",
            "properties": {
                "query": {
                    "type": "string",
                    "description": "The search query"
                }
            },
            "required": ["query"]
        }
    }
]

def check_api_keys():
    missing_keys = []
    if not os.getenv("ANTHROPIC_API_KEY"):
        missing_keys.append("ANTHROPIC_API_KEY")
    if not os.getenv("TAVILY_API_KEY"):
        missing_keys.append("TAVILY_API_KEY")
    
    if missing_keys:
        print_colored("Warning: The following API keys were not found in the environment:", TOOL_COLOR)
        for key in missing_keys:
            print_colored(f"  - {key}", TOOL_COLOR)
        print_colored("Please set these environment variables or add them to your .env file.", TOOL_COLOR)
        return False
    return True

def execute_tool(tool_name, tool_args):
    print_colored(f"Executing tool: {tool_name} with args: {tool_args}", TOOL_COLOR)
    if tool_name == "create_folder":
        result = create_folder(tool_args["path"])
    elif tool_name == "create_file":
        result = create_file(tool_args["path"], tool_args.get("content", ""))
    elif tool_name == "write_to_file":
        result = write_to_file(tool_args["path"], tool_args["content"])
    elif tool_name == "read_file":
        result = read_file(tool_args["path"])
    elif tool_name == "list_files":
        result = list_files(tool_args.get("path", "."))
    elif tool_name == "tavily_search":
        result = tavily_search(tool_args["query"])
    else:
        result = f"Unknown tool: {tool_name}"
    
    print_colored(f"Tool execution result: {result}", RESULT_COLOR)
    return result

def tavily_search(query):
    try:
        response = tavily.qna_search(query=query, search_depth="advanced")
        return response
    except Exception as e:
        return f"Error performing search: {str(e)}"

def chat_with_claude(user_input, image_path=None):
    global conversation_history
    
    if image_path:
        print_colored(f"Processing image at path: {image_path}", TOOL_COLOR)
        image_base64 = encode_image_to_base64(image_path)
        
        if image_base64.startswith("Error"):
            print_colored(f"Error encoding image: {image_base64}", ERROR_COLOR)
            return "I'm sorry, there was an error processing the image. Please try again."

        image_message = {
            "role": "user",
            "content": [
                {
                    "type": "image",
                    "source": {
                        "type": "base64",
                        "media_type": "image/jpeg",
                        "data": image_base64
                    }
                },
                {
                    "type": "text",
                    "text": f"User input for image: {user_input}"
                }
            ]
        }
        conversation_history.append(image_message)
        print_colored("Image message added to conversation history", TOOL_COLOR)
    else:
        conversation_history.append({"role": "user", "content": user_input})
    
    messages = [msg for msg in conversation_history if msg.get('content')]
    
    try:
        response = client.messages.create(
            model="claude-3-sonnet-20240229",
            max_tokens=4000,
            system=system_prompt,
            messages=messages,
            tools=tools,
            tool_choice={"type": "auto"}
        )
    except Exception as e:
        print_colored(f"Error calling Claude API: {str(e)}", ERROR_COLOR)
        return "I'm sorry, there was an error communicating with the AI. Please try again."
    
    assistant_response = ""
    
    for content in response.content:
        if content.type == "text":
            assistant_response += content.text
            print_colored(f"\nClaude: {content.text}", CLAUDE_COLOR)
        elif content.type == "tool_calls":
            for tool_call in content.tool_calls:
                tool_name = tool_call.function.name
                tool_args = json.loads(tool_call.function.arguments)
                
                print_colored(f"\nExecuting Tool: {tool_name}", TOOL_COLOR)
                print_colored(f"Tool Arguments: {tool_args}", TOOL_COLOR)
                
                result = execute_tool(tool_name, tool_args)
                print_colored(f"Tool Result: {result}", RESULT_COLOR)
                
                assistant_response += f"\nI've used the {tool_name} tool. {result}"
                
                conversation_history.append({
                    "role": "tool",
                    "content": str(result),
                    "tool_call_id": tool_call.id
                })
    
    if assistant_response:
        conversation_history.append({"role": "assistant", "content": assistant_response})
    
    return assistant_response

def signal_handler(sig, frame):
    print_colored("\nGracefully exiting. Thank you for using Claude Engineer!", CLAUDE_COLOR)
    sys.exit(0)

def interactive_mode():
    print_colored("Welcome to the Claude-3 Engineer Chat!", CLAUDE_COLOR)
    print_colored("Type 'exit' or press Ctrl+C to end the conversation.", CLAUDE_COLOR)
    print_colored("Available tools: create_folder, create_file, write_to_file, read_file, list_files, tavily_search", TOOL_COLOR)
    print_colored("You can use tools directly by typing the tool name followed by JSON arguments.", TOOL_COLOR)
    print_colored("Example: create_folder {\"path\": \"my_project\"}", TOOL_COLOR)
    print_colored("To include an image, type 'image' and press enter. Then provide the image path.", TOOL_COLOR)
    
    while True:
        try:
            user_input = input(f"\n{USER_COLOR}You: {Style.RESET_ALL}")
            
            if user_input.lower() == 'exit':
                print_colored("Thank you for chatting. Goodbye!", CLAUDE_COLOR)
                break
            
            if user_input.lower() == 'image':
                image_path = input(f"{USER_COLOR}Enter the path to your image file: {Style.RESET_ALL}").strip()
                
                if os.path.isfile(image_path):
                    user_input = input(f"{USER_COLOR}You (prompt for image): {Style.RESET_ALL}")
                    response = chat_with_claude(user_input, image_path)
                else:
                    print_colored("Invalid image path. Please try again.", ERROR_COLOR)
                    continue
            elif user_input.lower().startswith(('create_folder', 'create_file', 'write_to_file', 'read_file', 'list_files', 'tavily_search')):
                try:
                    parts = user_input.split(maxsplit=1)
                    tool_name = parts[0]
                    tool_args = json.loads(parts[1]) if len(parts) > 1 else {}
                    result = execute_tool(tool_name, tool_args)
                    print_colored(f"Tool Result: {result}", RESULT_COLOR)
                    conversation_history.append({"role": "user", "content": f"I used the {tool_name} tool with arguments: {tool_args}"})
                    conversation_history.append({"role": "assistant", "content": f"The result of using the {tool_name} tool was: {result}"})
                except json.JSONDecodeError:
                    print_colored("Invalid JSON format for tool arguments. Please try again.", ERROR_COLOR)
                except Exception as e:
                    print_colored(f"Error executing tool: {str(e)}", ERROR_COLOR)
            else:
                response = chat_with_claude(user_input)
                
                # Check if Claude didn't use a tool but the user wanted to create a folder
                if "create a folder" in user_input.lower() and "create_folder" not in response:
                    folder_name = user_input.lower().split("named")[-1].strip()
                    print_colored(f"\nClaude didn't explicitly create the folder. Let me do that for you.", TOOL_COLOR)
                    result = execute_tool("create_folder", {"path": folder_name})
                    print_colored(f"Tool Result: {result}", RESULT_COLOR)
                
                if "```" in response:
                    parts = response.split("```")
                    for i, part in enumerate(parts):
                        if i % 2 == 0:
                            print_colored(part, CLAUDE_COLOR)
                        else:
                            lines = part.split('\n')
                            language = lines[0].strip() if lines else ""
                            code = '\n'.join(lines[1:]) if len(lines) > 1 else ""
                            
                            if language and code:
                                print_code(code, language)
                            elif code:
                                print_colored(f"Code:\n{code}", CLAUDE_COLOR)
                            else:
                                print_colored(part, CLAUDE_COLOR)
                else:
                    print_colored(response, CLAUDE_COLOR)
        except KeyboardInterrupt:
            print_colored("\nGracefully exiting. Thank you for using Claude Engineer!", CLAUDE_COLOR)
            break

def main():
    # Set up signal handler
    signal.signal(signal.SIGINT, signal_handler)
    
    try:
        interactive_mode()
    except Exception as e:
        print_colored(f"An unexpected error occurred: {str(e)}", ERROR_COLOR)
        sys.exit(1)

if __name__ == "__main__":
    main()