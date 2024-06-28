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

# Define the tools with correct input_schema
# Define the tools with improved descriptions and structure
tools = [
    {
        "type": "function",
        "function": {
            "name": "create_folder",
            "description": "Creates a new folder at the specified path. Use this tool when you need to organize files or create a new project structure. The tool will create any necessary parent directories if they don't exist. If the folder already exists, it will not overwrite it.",
            "parameters": {
                "type": "object",
                "properties": {
                    "path": {"type": "string", "description": "The full path where the folder should be created. Use forward slashes (/) for path separation, even on Windows systems."}
                },
                "required": ["path"]
            }
        }
    },
    {
        "type": "function",
        "function": {
            "name": "create_file",
            "description": "Creates a new file at the specified path with optional content. Use this tool when you need to create a new file, such as a source code file, configuration file, or any text-based document. If the file already exists, it will be overwritten.",
            "parameters": {
                "type": "object",
                "properties": {
                    "path": {"type": "string", "description": "The full path where the file should be created, including the filename and extension."},
                    "content": {"type": "string", "description": "The initial content to write to the file. If not provided, an empty file will be created."}
                },
                "required": ["path"]
            }
        }
    },
    {
        "type": "function",
        "function": {
            "name": "write_to_file",
            "description": "Writes or appends content to an existing file at the specified path. Use this tool when you need to update the contents of a file, add new information, or overwrite existing content. If the file doesn't exist, it will be created.",
            "parameters": {
                "type": "object",
                "properties": {
                    "path": {"type": "string", "description": "The full path of the file to write to, including the filename and extension."},
                    "content": {"type": "string", "description": "The content to write to the file. This will overwrite any existing content in the file."},
                    "mode": {"type": "string", "enum": ["w", "a"], "description": "The write mode: 'w' for write (overwrite), 'a' for append. Default is 'w'."}
                },
                "required": ["path", "content"]
            }
        }
    },
    {
        "type": "function",
        "function": {
            "name": "read_file",
            "description": "Reads and returns the contents of a file at the specified path. Use this tool when you need to access the content of an existing file, such as to review code, check configuration settings, or analyze text data. This tool can handle various file types, including text files, source code, and even attempt to extract text from PDFs and HTML files.",
            "parameters": {
                "type": "object",
                "properties": {
                    "path": {"type": "string", "description": "The full path of the file to read, including the filename and extension."}
                },
                "required": ["path"]
            }
        }
    },
    {
        "type": "function",
        "function": {
            "name": "list_files",
            "description": "Lists all files and directories in the specified path. Use this tool when you need to explore the contents of a directory, check for the existence of certain files, or get an overview of a project structure. It returns a list of file and directory names.",
            "parameters": {
                "type": "object",
                "properties": {
                    "path": {"type": "string", "description": "The path of the folder to list. If not provided, it lists the contents of the current working directory."}
                },
                "required": []
            }
        }
    },
    {
        "type": "function",
        "function": {
            "name": "tavily_search",
            "description": "Performs a web search using the Tavily API to find up-to-date information on a given query. Use this tool when you need current information, facts, or data that might not be in your training data. The search results can provide context for answering questions or solving problems.",
            "parameters": {
                "type": "object",
                "properties": {
                    "query": {"type": "string", "description": "The search query to send to the Tavily API."}
                },
                "required": ["query"]
            }
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

def execute_tool(tool_name, tool_input):
    if tool_name == "create_folder":
        return create_folder(tool_input["path"])
    elif tool_name == "create_file":
        return create_file(tool_input["path"], tool_input.get("content", ""))
    elif tool_name == "write_to_file":
        mode = tool_input.get("mode", "w")
        return write_to_file(tool_input["path"], tool_input["content"], mode)
    elif tool_name == "read_file":
        return read_file(tool_input["path"])
    elif tool_name == "list_files":
        return list_files(tool_input.get("path", "."))
    elif tool_name == "tavily_search":
        return tavily.search(query=tool_input["query"])
    else:
        return f"Error: Unknown tool '{tool_name}'"

def chat_with_claude(user_input, image_path=None, model=DEFAULT_MODEL, tool_choice="auto"):
    if not check_api_keys():
        return "Error: Missing API keys. Please set the required environment variables."

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
            model=CLAUDE_MODELS[model],
            max_tokens=4000,
            system=system_prompt, 
            messages=messages,
            tools=tools,
            tool_choice={"type": tool_choice} if tool_choice != "tool" else {"type": "function", "function": {"name": tool_choice}}
        )
    except Exception as e:
        print_colored(f"Error calling Claude API: {str(e)}", ERROR_COLOR)
        return "I'm sorry, there was an error communicating with the AI. Please try again."
    
    assistant_response = ""
    
    for content in response.content:
        if content.type == "text":
            assistant_response += content.text
            print_colored(f"\nClaude: {content.text}", CLAUDE_COLOR)
        elif content.type == "tool_call":
            tool_call = content.tool_call
            tool_name = tool_call.function.name
            tool_args = json.loads(tool_call.function.arguments)
            
            print_colored(f"\nTool Used: {tool_name}", TOOL_COLOR)
            print_colored(f"Tool Arguments: {tool_args}", TOOL_COLOR)
            
            result = execute_tool(tool_name, tool_args)
            print_colored(f"Tool Result: {result}", RESULT_COLOR)
            
            conversation_history.append({"role": "assistant", "content": [content]})
            conversation_history.append({
                "role": "tool",
                "content": str(result),
                "tool_call_id": tool_call.id
            })
            
            try:
                tool_response = client.messages.create(
                    model=CLAUDE_MODELS[model],
                    max_tokens=4000,
                    messages=[msg for msg in conversation_history if msg.get('content')],
                    tools=tools,
                    tool_choice={"type": tool_choice} if tool_choice != "tool" else {"type": "function", "function": {"name": tool_choice}}
                )
                
                for tool_content in tool_response.content:
                    if tool_content.type == "text":
                        assistant_response += tool_content.text
                        print_colored(f"\nClaude: {tool_content.text}", CLAUDE_COLOR)
            except Exception as e:
                print_colored(f"Error in tool response: {str(e)}", ERROR_COLOR)
                assistant_response += "\nI encountered an error while processing the tool result. Please try again."
    
    if assistant_response:
        conversation_history.append({"role": "assistant", "content": assistant_response})
    
    return assistant_response

def graceful_exit(signum, frame):
    print_colored("\nExiting Claude Engineer. Goodbye!", CLAUDE_COLOR)
    sys.exit(0)

def interactive_mode(model, tool_choice):
    if not check_api_keys():
        print_colored("Error: Missing API keys. Please set the required environment variables.", ERROR_COLOR)
        return

    print_colored(f"Welcome to the Claude-3 Engineer Chat (Model: {model})!", CLAUDE_COLOR)
    print_colored("Type 'exit' or press Ctrl+C to end the conversation.", CLAUDE_COLOR)
    print_colored("To include an image, type 'image' and press enter. Then enter the path to the image file.", CLAUDE_COLOR)
    print_colored("To change the model, type 'model' and press enter. Then enter the model name (opus, sonnet, or haiku).", CLAUDE_COLOR)
    print_colored("To change the tool choice, type 'tool_choice' and press enter. Then enter 'auto', 'any', or a specific tool name.", CLAUDE_COLOR)
    
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
                    response = chat_with_claude(user_input, image_path, model, tool_choice)
                else:
                    print_colored("Invalid image path. Please try again.", ERROR_COLOR)
                    continue
            elif user_input.lower() == 'model':
                new_model = input(f"{USER_COLOR}Enter the model name (opus, sonnet, or haiku): {Style.RESET_ALL}").strip().lower()
                if new_model in CLAUDE_MODELS:
                    model = new_model
                    print_colored(f"Model changed to: {model}", TOOL_COLOR)
                else:
                    print_colored("Invalid model name. Please try again.", ERROR_COLOR)
                continue
            elif user_input.lower() == 'tool_choice':
                new_tool_choice = input(f"{USER_COLOR}Enter tool choice (auto, any, or a specific tool name): {Style.RESET_ALL}").strip().lower()
                if new_tool_choice in ['auto', 'any'] or new_tool_choice in [tool['function']['name'] for tool in tools]:
                    tool_choice = new_tool_choice
                    print_colored(f"Tool choice changed to: {tool_choice}", TOOL_COLOR)
                else:
                    print_colored("Invalid tool choice. Please try again.", ERROR_COLOR)
                continue
            else:
                response = chat_with_claude(user_input, model=model, tool_choice=tool_choice)
            
            if response.startswith("Error"):
                print_colored(response, ERROR_COLOR)
            else:
                # Check if the response contains code and format it
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
                                # If no language is specified but there is code, print it as plain text
                                print_colored(f"Code:\n{code}", CLAUDE_COLOR)
                            else:
                                # If there's no code (empty block), just print the part as is
                                print_colored(part, CLAUDE_COLOR)
                else:
                    print_colored(response, CLAUDE_COLOR)
        except KeyboardInterrupt:
            graceful_exit(None, None)

def main():
    if not check_api_keys():
        sys.exit(1)

    parser = argparse.ArgumentParser(description="Claude Engineer - Interact with Claude AI from the command line")
    parser.add_argument("--query", type=str, help="Send a single query to Claude")
    parser.add_argument("--image", type=str, help="Path to an image file to analyze")
    parser.add_argument("--model", type=str, choices=list(CLAUDE_MODELS.keys()), default=DEFAULT_MODEL, help="Choose the Claude model to use")
    parser.add_argument("--tool_choice", type=str, default="auto", help="Set the tool choice (auto, any, or a specific tool name)")
    
    args = parser.parse_args()
    
    # Set up signal handler for graceful exit
    signal.signal(signal.SIGINT, graceful_exit)
    
    try:
        if args.query:
            if args.image:
                if not os.path.isfile(args.image):
                    raise FileNotFoundError(f"Image file not found: {args.image}")
                response = chat_with_claude(args.query, args.image, args.model, args.tool_choice)
            else:
                response = chat_with_claude(args.query, model=args.model, tool_choice=args.tool_choice)
            print(response)
        else:
            interactive_mode(args.model, args.tool_choice)
    except Exception as e:
        print_colored(f"An error occurred: {str(e)}", ERROR_COLOR)
        sys.exit(1)

if __name__ == "__main__":
    main()
