# ProPosition Agent v0.3.0

A versatile and extensible agent framework built with Supabase, Ollama, and A2A protocol for agent collaboration. This project provides a foundation for creating intelligent agents that can leverage local LLM capabilities, connect to a Supabase database, communicate with a Master Control Program (MCP) for tool execution, and collaborate with other agents using the A2A protocol.

---

## Features

- **Supabase Integration:** Uses Supabase for vector storage and retrieval instead of ChromaDB
- **Local LLM Support:** Connects to Ollama for local GPU inference instead of calling external API providers
- **MCP Tool Execution:** Generic interface to a Master Control Program for executing tools
- **A2A Protocol:** Agent-to-agent communication for collaboration between multiple agents
- **Streamlit Interface:** User-friendly web interface for interacting with the agent

---

## Prerequisites

- Python 3.11+
- Ollama running locally or accessible via network
- Supabase account and project
- Dependencies in `requirements.txt`

---

## Installation

1. **Clone the repository:**
   ```bash
   git clone https://github.com/pro-position-ai/ProPosAgent003.git
   cd ProPosAgent003
   ```

2. **Install dependencies:**
   ```bash
   python -m venv venv
   source venv/bin/activate  # On Windows: venv\Scripts\activate
   pip install -r requirements.txt
   ```

3. **Set up environment variables:**
   - Copy `.env.example` to `.env`
   - Edit `.env` with your Supabase credentials, Ollama URL, and other configuration options

4. **Setup Supabase:**
   - Create a new Supabase project
   - Create a table for storing knowledge (e.g., `knowledge_base`)
   - Configure vector search capabilities in your Supabase project

5. **Install Ollama:**
   - Follow the instructions at [Ollama.ai](https://ollama.ai) to install Ollama
   - Pull required models: `ollama pull llama3`

---

## Usage

### Running the Agent via Command Line

```bash
python generic_agent.py --input "Your question or task here"
```

Optional arguments:
- `--table`: Supabase table name (default: `knowledge_base`)
- `--agent-id`: Unique identifier for the agent (default: `generic-agent-1`)
- `--agent-name`: Human-readable name for the agent (default: `Generic Agent`)

### Running the Streamlit Interface

```bash
streamlit run streamlit_app.py
```

The interface will be available at [http://localhost:8501](http://localhost:8501)

---

## Project Structure

```
generic-agent/
├── a2a_protocol.py      # A2A protocol implementation for agent collaboration
├── generic_agent.py     # Main agent implementation with Supabase, Ollama and A2A
├── streamlit_app.py     # Streamlit web interface
├── utils.py             # Utility functions for Supabase operations
├── requirements.txt     # Project dependencies
├── .env.example         # Example environment configuration
└── README.md            # Project documentation
```

---

## Extending the Agent

### Adding New Tool Capabilities

To add new tool capabilities, you can implement new tool functions in the `generic_agent.py` file or extend the MCP server to support additional tools.

### Customizing the Agent Behavior

You can customize the agent's behavior by modifying the system prompt in the `Agent` initialization in `generic_agent.py`.

### Integration with Other Systems

The agent is designed to be easily integrated with other systems through the MCP server interface and A2A protocol.

---

## A2A Protocol

The A2A (Agent-to-Agent) protocol enables:

1. **Agent Discovery:** Finding and connecting to other agents
2. **Message Passing:** Asynchronous communication between agents
3. **Task Delegation:** Assigning tasks to specialized agents
4. **Collaborative Problem Solving:** Multiple agents working together on complex tasks

---

## MCP Server

The Master Control Program (MCP) server acts as a central hub for tool execution, providing:

1. **Tool Registry:** A central repository of available tools
2. **Access Control:** Permission management for tool execution
3. **Execution Environment:** Safe execution environment for tools
4. **Result Handling:** Standardized format for tool execution results

---

## Troubleshooting

- **Supabase Connection Issues:** Verify your Supabase URL and API key
- **Ollama Not Available:** Ensure Ollama is running and accessible at the configured URL
- **MCP Server Unavailable:** Check the MCP server URL and authentication credentials
- **A2A Protocol Errors:** Verify that the A2A protocol is properly configured

---

## Future Enhancements

- **Multi-modal Support:** Extend the agent to handle images, audio, and video
- **Tool Learning:** Allow the agent to learn new tools from examples
- **Advanced Collaboration:** Implement more sophisticated agent collaboration patterns
- **Memory Optimization:** Improve knowledge management and context handling
