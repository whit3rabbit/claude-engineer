import os
import argparse
import sys
from dotenv import load_dotenv
from anthropic import Anthropic
from tavily import TavilyClient
from colorama import init, Style
import signal

# Import helper functions and constants
from .utils import (
    print_colored, print_code, create_folder, create_file,
    write_to_file, read_file, list_files, encode_image_to_base64,
    USER_COLOR, CLAUDE_COLOR, TOOL_COLOR, RESULT_COLOR
)

# Initialize colorama
init()

# Load environment variables
load_dotenv()

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
        "description": "Create a new folder at the specified path.",
        "parameters": {
            "type": "object",
            "properties": {
                "path": {"type": "string", "description": "The path where the folder should be created"}
            },
            "required": ["path"]
        }
    },
    {
        "name": "create_file",
        "description": "Create a new file at the specified path with optional content.",
        "parameters": {
            "type": "object",
            "properties": {
                "path": {"type": "string", "description": "The path where the file should be created"},
                "content": {"type": "string", "description": "The initial content of the file"}
            },
            "required": ["path"]
        }
    },
    {
        "name": "write_to_file",
        "description": "Write content to an existing file at the specified path.",
        "parameters": {
            "type": "object",
            "properties": {
                "path": {"type": "string", "description": "The path of the file to write to"},
                "content": {"type": "string", "description": "The content to write to the file"}
            },
            "required": ["path", "content"]
        }
    },
    {
        "name": "read_file",
        "description": "Read the contents of a file at the specified path.",
        "parameters": {
            "type": "object",
            "properties": {
                "path": {"type": "string", "description": "The path of the file to read"}
            },
            "required": ["path"]
        }
    },
    {
        "name": "list_files",
        "description": "List all files and directories in the specified path.",
        "parameters": {
            "type": "object",
            "properties": {
                "path": {"type": "string", "description": "The path of the folder to list (default: current directory)"}
            }
        }
    },
    {
        "name": "tavily_search",
        "description": "Perform a web search using Tavily API.",
        "parameters": {
            "type": "object",
            "properties": {
                "query": {"type": "string", "description": "The search query"}
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

def execute_tool(tool_name, tool_input):
    if tool_name == "create_folder":
        return create_folder(tool_input["path"])
    elif tool_name == "create_file":
        return create_file(tool_input["path"], tool_input.get("content", ""))
    elif tool_name == "write_to_file":
        return write_to_file(tool_input["path"], tool_input["content"])
    elif tool_name == "read_file":
        return read_file(tool_input["path"])
    elif tool_name == "list_files":
        return list_files(tool_input.get("path", "."))
    elif tool_name == "tavily_search":
        return tavily.search(query=tool_input["query"])
    else:
        return f"Unknown tool: {tool_name}"

def chat_with_claude(user_input, image_path=None):
    if not check_api_keys():
        return "Error: Missing API keys. Please set the required environment variables."

    global conversation_history
    
    if image_path:
        print_colored(f"Processing image at path: {image_path}", TOOL_COLOR)
        image_base64 = encode_image_to_base64(image_path)
        
        if image_base64.startswith("Error"):
            print_colored(f"Error encoding image: {image_base64}", TOOL_COLOR)
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
            model="claude-3-5-sonnet-20240620",
            max_tokens=4000,
            system=system_prompt,
            messages=messages,
            tools=tools,
            tool_choice={"type": "auto"}
        )
    except Exception as e:
        print_colored(f"Error calling Claude API: {str(e)}", TOOL_COLOR)
        return "I'm sorry, there was an error communicating with the AI. Please try again."
    
    assistant_response = ""
    
    for content_block in response.content:
        if content_block.type == "text":
            assistant_response += content_block.text
            print_colored(f"\nClaude: {content_block.text}", CLAUDE_COLOR)
        elif content_block.type == "tool_use":
            tool_name = content_block.name
            tool_input = content_block.input
            tool_use_id = content_block.id
            
            print_colored(f"\nTool Used: {tool_name}", TOOL_COLOR)
            print_colored(f"Tool Input: {tool_input}", TOOL_COLOR)
            
            result = execute_tool(tool_name, tool_input)
            print_colored(f"Tool Result: {result}", RESULT_COLOR)
            
            conversation_history.append({"role": "assistant", "content": [content_block]})
            conversation_history.append({
                "role": "user",
                "content": [
                    {
                        "type": "tool_result",
                        "tool_use_id": tool_use_id,
                        "content": result
                    }
                ]
            })
            
            try:
                tool_response = client.messages.create(
                    model="claude-3-5-sonnet-20240620",
                    max_tokens=4000,
                    system=system_prompt,
                    messages=[msg for msg in conversation_history if msg.get('content')],
                    tools=tools,
                    tool_choice={"type": "auto"}
                )
                
                for tool_content_block in tool_response.content:
                    if tool_content_block.type == "text":
                        assistant_response += tool_content_block.text
                        print_colored(f"\nClaude: {tool_content_block.text}", CLAUDE_COLOR)
            except Exception as e:
                print_colored(f"Error in tool response: {str(e)}", TOOL_COLOR)
                assistant_response += "\nI encountered an error while processing the tool result. Please try again."
    
    if assistant_response:
        conversation_history.append({"role": "assistant", "content": assistant_response})
    
    return assistant_response

def graceful_exit(signum, frame):
    print_colored("\nExiting Claude Engineer. Goodbye!", CLAUDE_COLOR)
    sys.exit(0)

def main():
    if not check_api_keys():
        sys.exit(1)

    parser = argparse.ArgumentParser(description="Claude Engineer - Interact with Claude AI from the command line")
    parser.add_argument("--query", type=str, help="Send a single query to Claude")
    parser.add_argument("--image", type=str, help="Path to an image file to analyze")
    
    args = parser.parse_args()
    
    # Set up signal handler for graceful exit
    signal.signal(signal.SIGINT, graceful_exit)
    
    try:
        if args.query:
            if args.image:
                if not os.path.isfile(args.image):
                    raise FileNotFoundError(f"Image file not found: {args.image}")
                response = chat_with_claude(args.query, args.image)
            else:
                response = chat_with_claude(args.query)
            print(response)
        else:
            interactive_mode()
    except Exception as e:
        print_colored(f"An error occurred: {str(e)}", TOOL_COLOR)
        sys.exit(1)

def interactive_mode():
    if not check_api_keys():
        print_colored("Error: Missing API keys. Please set the required environment variables.", TOOL_COLOR)
        return

    print_colored("Welcome to the Claude-3.5-Sonnet Engineer Chat with Image Support!", CLAUDE_COLOR)
    print_colored("Type 'exit' or press Ctrl+C to end the conversation.", CLAUDE_COLOR)
    print_colored("To include an image, type 'image' and press enter. Then enter the path to the image file.", CLAUDE_COLOR)
    
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
                    print_colored("Invalid image path. Please try again.", CLAUDE_COLOR)
                    continue
            else:
                response = chat_with_claude(user_input)
            
            if response.startswith("Error") or response.startswith("I'm sorry"):
                print_colored(response, TOOL_COLOR)
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

if __name__ == "__main__":
    main()
