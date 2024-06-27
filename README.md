# Claude Engineer

Claude Engineer is an interactive command-line interface (CLI) that leverages the power of Anthropic's Claude-3.5-Sonnet model to assist with software development tasks. This tool combines the capabilities of a large language model with practical file system operations and web search functionality.

## Features

- Interactive chat interface with Claude-3.5-Sonnet
- File system operations (create folders, files, read/write files)
- Web search capabilities using Tavily API
- Syntax highlighting for code snippets
- Project structure creation and management
- Code analysis and improvement suggestions
- Vision capabilities support via drag and drop of images in the terminal

## Installation

Since Claude Engineer is not currently available in the PyPI repository, you need to install it directly from the source:

1. Clone the repository:
   ```
   git clone https://github.com/Doriandarko/claude-engineer.git
   cd claude-engineer
   ```

2. Install the package:
   ```
   pip install .
   ```

## Configuration

Before using Claude Engineer, you need to set up your API keys. You can do this either by setting environment variables or by using a `.env` file.

### Setting Environment Variables

#### Windows (Command Prompt)
```
set ANTHROPIC_API_KEY=your_anthropic_api_key_here
set TAVILY_API_KEY=your_tavily_api_key_here
```

#### Windows (PowerShell)
```
$env:ANTHROPIC_API_KEY="your_anthropic_api_key_here"
$env:TAVILY_API_KEY="your_tavily_api_key_here"
```

#### Linux/macOS
```
export ANTHROPIC_API_KEY=your_anthropic_api_key_here
export TAVILY_API_KEY=your_tavily_api_key_here
```

Replace `your_anthropic_api_key_here` and `your_tavily_api_key_here` with your actual API keys.

### Using a .env File

Alternatively, you can create a `.env` file in your project directory:

1. Create a file named `.env` in your project directory.
2. Add your Anthropic and Tavily API keys to the `.env` file:

```
ANTHROPIC_API_KEY=your_anthropic_api_key_here
TAVILY_API_KEY=your_tavily_api_key_here
```

## Usage

To start the Claude Engineer interface in interactive mode, run:

```
claude-engineer --interactive
```

You can also send a single query without entering interactive mode:

```
claude-engineer --query "Your query here"
```

To analyze an image along with your query:

```
claude-engineer --query "Describe this image" --image /path/to/your/image.jpg
```

## Available Tools

Claude Engineer provides several tools to assist with various tasks:

1. **create_folder**: Create a new folder at the specified path.
   Example: "Create a new folder called 'project' in the current directory."

2. **create_file**: Create a new file at the specified path with optional content.
   Example: "Create a new file called 'main.py' in the 'project' folder with a simple 'Hello, World!' program."

3. **write_to_file**: Write content to an existing file at the specified path.
   Example: "Add a new function to calculate factorial in the 'main.py' file."

4. **read_file**: Read the contents of a file at the specified path.
   Example: "Show me the contents of the 'main.py' file."

5. **list_files**: List all files and directories in the specified path.
   Example: "List all files in the current directory."

6. **tavily_search**: Perform a web search using Tavily API.
   Example: "Search for the latest best practices in Python web development."

To use these tools, simply describe your task in natural language, and Claude Engineer will interpret your request and use the appropriate tool.

## Image Analysis

You can also use Claude Engineer to analyze images. In interactive mode, type 'image' and press enter, then provide the path to your image file. Follow up with a prompt describing what you want to know about the image.

## Contributing

Contributions are welcome! Please feel free to submit a Pull Request.

## License

This project is licensed under the MIT License - see the LICENSE file for details.