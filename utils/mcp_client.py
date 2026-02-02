"""MCP Client for connecting to MCP servers."""

import asyncio
import json
from typing import Dict, Any, Optional
import subprocess
import sys
from pathlib import Path


class MCPClient:
    """Client for communicating with MCP servers via stdio."""
    
    def __init__(self):
        self.servers = {}
        # Get project root (parent of bot_generator)
        self.base_dir = Path(__file__).parent.parent.parent
    
    async def connect_server(self, server_name: str, server_path: str):
        """
        Connect to an MCP server.
        
        Args:
            server_name: Name identifier for the server
            server_path: Path to the server's server.py file
        """
        # For now, store server paths - actual subprocess communication would be added here
        self.servers[server_name] = {
            "path": server_path,
            "connected": False
        }
    
    async def call_tool(self, server_name: str, tool_name: str, arguments: Dict[str, Any]) -> Any:
        """
        Call a tool on an MCP server.
        
        Args:
            server_name: Name of the server
            tool_name: Name of the tool
            arguments: Tool arguments
            
        Returns:
            Tool result
        """
        # Simplified version - in production, this would use MCP protocol over stdio
        # For now, we'll import and call directly
        
        if server_name == "parser":
            from mcp_servers.parser.tools import ParserTools
            parser = ParserTools(self.base_dir / "mcp_servers/parser/data")
            
            if tool_name == "parse_intent":
                return parser.parse_intent(arguments["prompt"])
        
        elif server_name == "architecture":
            from mcp_servers.architecture.tools import ArchitectureTools
            architect = ArchitectureTools(self.base_dir / "mcp_servers/architecture/data")
            
            if tool_name == "design_architecture":
                return architect.design_architecture(arguments["intent"])
        
        elif server_name == "templates":
            from mcp_servers.templates_lib.tools import TemplateTools
            templates = TemplateTools(self.base_dir / "mcp_servers/templates_lib/data")
            
            if tool_name == "get_best_match":
                return templates.get_best_match(arguments["bot_type"], arguments["features"])
        
        elif server_name == "generator":
            from mcp_servers.generator.tools import GeneratorTools
            generator = GeneratorTools(self.base_dir / "mcp_servers/generator/data")
            
            if tool_name == "generate_bot":
                # Call async generate_bot with await
                return await generator.generate_bot(
                    arguments["architecture"],
                    arguments["bot_name"],
                    arguments.get("user_token")
                )
        
        elif server_name == "validator":
            from mcp_servers.validator.tools import ValidatorTools
            validator = ValidatorTools(self.base_dir / "mcp_servers/validator/data")
            
            if tool_name == "validate_syntax":
                return validator.validate_syntax(arguments["files"])
            elif tool_name == "test_bot_logic":
                return validator.test_bot_logic(arguments["files"], arguments["bot_type"])
            elif tool_name == "security_scan":
                return validator.security_scan(arguments["files"])
        
        raise ValueError(f"Unknown server or tool: {server_name}.{tool_name}")
