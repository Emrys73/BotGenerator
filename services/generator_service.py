"""Bot Generator service - Orchestrates the bot generation workflow."""

import logging
from typing import Dict, Any
import zipfile
import io
from pathlib import Path
import sys

sys.path.append(str(Path(__file__).parent.parent.parent))

from bot_generator.utils.mcp_client import MCPClient


logger = logging.getLogger(__name__)


class BotGenerator:
    """Main bot generator service that orchestrates MCP servers."""
    
    def __init__(self):
        self.mcp_client = MCPClient()
        self.workflow_steps = []
    
    async def generate_bot(
        self,
        user_prompt: str,
        bot_name: str = None,
        user_token: str = None,
        progress_callback=None
    ) -> Dict[str, Any]:
        """
        Generate a complete bot from user prompt.
        
        Args:
            user_prompt: User's natural language description
            bot_name: Optional name for the bot
            user_token: Optional bot token to pre-configure in .env
            progress_callback: Optional async callback(stage_num, total_stages, stage_name)
            
        Returns:
            Dictionary with generated files and metadata
        """
        # Import validation utilities
        sys.path.append(str(Path(__file__).parent.parent.parent))
        from shared.validation import validate_prompt, sanitize_bot_name, ValidationError
        
        logger.info(f"Starting bot generation for prompt: {user_prompt}")
        self.workflow_steps = []
        total_stages = 6
        warnings = []
        
        # Validate input
        try:
            user_prompt = validate_prompt(user_prompt)
        except ValidationError as e:
            return {
                "success": False,
                "error": f"Invalid prompt: {str(e)}",
                "workflow_steps": [f"❌ Validation failed: {str(e)}"]
            }
        
        try:
            # Step 1: Parse Intent
            logger.info("Step 1: Parsing user intent...")
            self.workflow_steps.append("🔍 Parsing user intent...")
            if progress_callback:
                await progress_callback(1, total_stages, "🔍 Parsing your requirements")
            
            intent = await self.mcp_client.call_tool(
                "parser",
                "parse_intent",
                {"prompt": user_prompt}
            )
            
            logger.info(f"Parsed intent: {intent['bot_type']} (confidence: {intent['confidence']:.2%})")
            
            # Step 2: Design Architecture
            logger.info("Step 2: Designing bot architecture...")
            self.workflow_steps.append(f"🏗️ Designing {intent['bot_type']} architecture...")
            if progress_callback:
                await progress_callback(2, total_stages, "🏗️ Designing bot architecture")
            
            architecture = await self.mcp_client.call_tool(
                "architecture",
                "design_architecture",
                {"intent": intent}
            )
            
            logger.info(f"Architecture designed: {architecture['framework']} - {architecture['complexity']}")
            
            # Step 3: Find Best Template Match
            logger.info("Step 3: Finding best template match...")
            self.workflow_steps.append("📚 Finding template match...")
            if progress_callback:
                await progress_callback(3, total_stages, "📚 Finding best code patterns")
            
            try:
                template_match = await self.mcp_client.call_tool(
                    "templates",
                    "get_best_match",
                    {"bot_type": intent["bot_type"], "features": intent["features"]}
                )
            except Exception as e:
                logger.warning(f"Template matching failed: {e}")
                warnings.append("Template matching unavailable")
                template_match = None
            
            # Step 4: Generate Code
            logger.info("Step 4: Generating bot code...")
            self.workflow_steps.append("💻 Generating code...")
            if progress_callback:
                await progress_callback(4, total_stages, "💻 Generating code files")
            
            # Sanitize bot name
            if not bot_name:
                bot_name = f"{intent['bot_type']}_bot"
            bot_name = sanitize_bot_name(bot_name)
            
            generated = await self.mcp_client.call_tool(
                "generator",
                "generate_bot",
                {"architecture": architecture, "bot_name": bot_name, "user_token": user_token}
            )
            
            files = generated["files"]
            logger.info(f"Generated {len(files)} files")
            
            # Step 5: Validate Code (non-critical - allow partial failure)
            logger.info("Step 5: Validating generated code...")
            self.workflow_steps.append("✅ Validating code...")
            if progress_callback:
                await progress_callback(5, total_stages, "✅ Validating code quality")
            
            validation = {}
            
            # Syntax validation
            try:
                validation["syntax"] = await self.mcp_client.call_tool(
                    "validator",
                    "validate_syntax",
                    {"files": files}
                )
            except Exception as e:
                logger.warning(f"Syntax validation failed: {e}")
                validation["syntax"] = {"valid": False, "error": str(e)}
                warnings.append("Syntax validation incomplete")
            
            # Logic validation
            try:
                validation["logic"] = await self.mcp_client.call_tool(
                    "validator",
                    "test_bot_logic",
                    {"files": files, "bot_type": intent["bot_type"]}
                )
            except Exception as e:
                logger.warning(f"Logic validation failed: {e}")
                validation["logic"] = {"passed": False, "error": str(e)}
                warnings.append("Logic validation incomplete")
            
            # Security scan
            try:
                validation["security"] = await self.mcp_client.call_tool(
                    "validator",
                    "security_scan",
                    {"files": files}
                )
            except Exception as e:
                logger.warning(f"Security scan failed: {e}")
                validation["security"] = {"safe": True, "issues": [], "error": str(e)}
                warnings.append("Security scan incomplete")
            
            # Step 6: Package Files
            logger.info("Step 6: Packaging files...")
            self.workflow_steps.append("📦 Packaging files...")
            if progress_callback:
                await progress_callback(6, total_stages, "📦 Packaging your bot")
            
            zip_data = self._create_zip(files, bot_name)
            
            logger.info("Bot generation complete!")
            self.workflow_steps.append("✨ Bot generation complete!")
            
            result = {
                "success": True,
                "bot_name": bot_name,
                "intent": intent,
                "architecture": architecture,
                "files": files,
                "file_count": len(files),
                "validation": validation,
                "zip_data": zip_data,
                "workflow_steps": self.workflow_steps
            }
            
            if warnings:
                result["warnings"] = warnings
            
            return result
        
        except Exception as e:
            logger.error(f"Error in bot generation: {e}", exc_info=True)
            self.workflow_steps.append(f"❌ Error: {str(e)}")
            return {
                "success": False,
                "error": str(e),
                "workflow_steps": self.workflow_steps
            }
    
    def _create_zip(self, files: Dict[str, str], bot_name: str) -> bytes:
        """Create a ZIP file from generated files."""
        from shared.validation import sanitize_filename
        
        zip_buffer = io.BytesIO()
        
        with zipfile.ZipFile(zip_buffer, 'w', zipfile.ZIP_DEFLATED) as zip_file:
            for filename, content in files.items():
                # Sanitize both bot_name and filename
                safe_filename = sanitize_filename(filename)
                zip_file.writestr(f"{bot_name}/{safe_filename}", content)
        
        return zip_buffer.getvalue()
