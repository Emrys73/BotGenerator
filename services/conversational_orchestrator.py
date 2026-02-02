"""Conversational orchestrator for bot creation using LLM."""

import logging
from typing import Dict, Any, List, Optional

import sys
from pathlib import Path
sys.path.append(str(Path(__file__).parent.parent.parent))

from bot_generator.services.llm_service import LLMService
from bot_generator.services.session_manager import session_manager
from bot_generator.models.project import BotProject, ProjectStatus
from bot_generator.utils.mcp_client import MCPClient


logger = logging.getLogger(__name__)


# System prompt for BotGenerator assistant
SYSTEM_PROMPT = """You are an expert Telegram bot creation assistant. Your role is to help users create custom Telegram bots through natural conversation.

**Your Capabilities:**
- Understanding user requirements through dialogue
- Asking clarifying questions when needed
- Designing bot architecture
- Generating production-ready code
- Iteratively refining based on feedback

**Your Conversation Style:**
- Friendly and professional
- Ask ONE question at a time
- Confirm understanding before generating
- Offer specific suggestions
- Use emojis moderately for better UX

**Available Tools (MCP Servers):**
1. **Parser** - Extract structured intent from conversation
2. **Architecture Designer** - Create bot architecture from requirements
3. **Template Library** - Find best code patterns
4. **Code Generator** - Generate complete bot code
5. **Validator** - Check code quality and security

**Workflow:**
1. **Gather Requirements**: Chat with user about what they want
   - Bot type (expense tracker, quiz, echo, etc.)
   - Key features
   - Special requirements

2. **Clarify**: Ask questions if anything is unclear
   - Be specific
   - One question at a time
   - Explain why you're asking

3. **Confirm**: Summarize what you understand
   - List key features
   - Ask for confirmation

4. **Request Token**: Ask for bot token from @BotFather
   - Explain how to get one if needed
   - Validate format

5. **Generate**: Create the bot
   - Show progress
   - Explain what you're doing

6. **Deliver**: Send ZIP file with instructions
   - List what's included
   - Provide setup steps
   - Offer to make changes

7. **Iterate**: Handle feedback
   - Understand what to change
   - Modify code
   - Send updated ZIP

**Important Rules:**
- NEVER ask for technical details users won't know (architecture patterns, frameworks, etc.)
- If uncertain about implementation, use research tools first
- Always validate bot tokens (format: numbers:letters)
- Keep responses concise but helpful
- Use bullet points for lists
- Include emojis for key points: 📝 ✅ 🎉 🤔 ⚠️

**Example Conversation:**
```
User: I want to build a bot
You: Great! What kind of bot would you like to create? 

For example:
• Expense tracker
• Quiz/trivia bot
• Reminder bot
• Something else?

User: expense tracker
You: Perfect! A few questions:

1. Should users be able to categorize expenses?
2. Do you need export features (like CSV)?
3. Any specific commands you want?

User: yes to categories, CSV export, and /add /list /stats commands
You: Excellent! 📝 Here's what I understand:

• Expense tracker bot
• Category support ✅
• CSV export ✅
• Commands: /add, /list, /stats

Does this sound right?

User: yes
You: Perfect! Now I need your bot token from @BotFather.

[continues...]
```

Remember: You're building trust and making bot creation accessible to everyone!"""


class ConversationalOrchestrator:
    """Orchestrate bot creation through LLM conversation."""
    
    def __init__(self):
        self.llm = LLMService()
        self.mcp_client = MCPClient()
        logger.info("ConversationalOrchestrator initialized")
    
    async def process_message(
        self,
        user_id: int,
        message: str,
        project: BotProject
    ) -> str:
        """
        Process user message and return AI response.
        
        Args:
            user_id: Telegram user ID
            message: User's message
            project: Active bot project
        
        Returns:
            AI assistant's response
        """
        # Add user message to history
        project.add_message("user", message)
        
        # Build conversation context
        messages = [
            {"role": "system", "content": SYSTEM_PROMPT}
        ] + project.get_conversation_context()
        
        # Determine what to do based on project status
        if project.status == ProjectStatus.GATHERING_REQUIREMENTS:
            response = await self._handle_requirements_gathering(
                message, project, messages
            )
        
        elif project.status == ProjectStatus.CLARIFYING:
            response = await self._handle_clarification(
                message, project, messages
            )
        
        elif project.status == ProjectStatus.GENERATING:
            response = await self._handle_generation(
                message, project, messages
            )
        
        elif project.status == ProjectStatus.REVIEWING:
            response = await self._handle_review(
                message, project, messages
            )
        
        elif project.status == ProjectStatus.ITERATING:
            response = await self._handle_iteration(
                message, project, messages
            )
        
        else:
            # Default: let LLM decide
            llm_response = await self.llm.chat(messages)
            response = llm_response["content"]
        
        # Add assistant response to history
        project.add_message("assistant", response)
        
        return response
    
    async def _handle_requirements_gathering(
        self,
        message: str,
        project: BotProject,
        messages: List[Dict]
    ) -> str:
        """Handle requirements gathering phase."""
        
        # Check if user is providing token (should move to clarifying first)
        if self._looks_like_token(message):
            return (
                "Thanks! But first, let me make sure I understand what "
                "you want to build.\n\n"
                "Can you describe the bot in a bit more detail?"
            )
        
        # Let LLM gather requirements
        llm_response = await self.llm.chat(messages + [{
            "role": "system",
            "content": (
                "The user is describing their bot. "
                "Ask clarifying questions if needed, or if you have enough info, "
                "ask for their bot token next."
            )
        }])
        
        response = llm_response["content"]
        
        # Check if LLM is asking for token -> move to clarifying
        if "token" in response.lower():
            project.status = ProjectStatus.CLARIFYING
        
        return response
    
    async def _handle_clarification(
        self,
        message: str,
        project: BotProject,
        messages: List[Dict]
    ) -> str:
        """Handle clarification phase (waiting for token)."""
        from shared.validation import validate_token_format, validate_token_with_telegram
        
        # Check if it's a valid token
        if self._looks_like_token(message):
            token = message.strip()
            
            # Validate token format
            if not validate_token_format(token):
                return (
                    "❌ That doesn't look like a valid bot token.\n\n"
                    "A valid token looks like:\n"
                    "`1234567890:ABCdefGHIjklMNOpqrs-TUVwxyz`\n\n"
                    "Please paste your token from @BotFather."
                )
            
            # Validate with Telegram API
            logger.info(f"Validating token for user {project.user_id}")
            is_valid, result = await validate_token_with_telegram(token)
            
            if not is_valid:
                return (
                    f"❌ Token validation failed: {result}\n\n"
                    "Please make sure you copied the full token from @BotFather.\n"
                    "The token should be active and not revoked."
                )
            
            # Token is valid!
            logger.info(f"Token validated successfully for bot @{result}")
            project.bot_token = token
            project.status = ProjectStatus.GENERATING
            
            return (
                f"✅ Token validated for @{result}!\n\n"
                "🚀 Generating your bot now...\n\n"
                "This will take about 10-15 seconds. I'm:\n"
                "1. Analyzing your requirements\n"
                "2. Designing the architecture\n"
                "3. Generating code files\n"
                "4. Validating everything\n\n"
                "Please wait..."
            )
        
        # Not a token, continue conversation
        llm_response = await self.llm.chat(messages)
        return llm_response["content"]
    
    async def _handle_generation(
        self,
        message: str,
        project: BotProject,
        messages: List[Dict]
    ) -> str:
        """Handle bot generation (should be called automatically)."""
        # This is called from the handler after status changes to GENERATING
        # Not directly from user message
        return ""
    
    async def _handle_review(
        self,
        message: str,
        project: BotProject,
        messages: List[Dict]
    ) -> str:
        """Handle user reviewing generated bot."""
        
        # Check if user wants changes
        change_keywords = ["change", "modify", "add", "remove", "update", "fix", "edit"]
        wants_changes = any(kw in message.lower() for kw in change_keywords)
        
        if wants_changes:
            project.status = ProjectStatus.ITERATING
            project.pending_changes = message
            
            return (
                "I understand you'd like to make changes. Let me update the bot for you...\n\n"
                "This may take a few seconds."
            )
        
        # User is happy or asking questions
        llm_response = await self.llm.chat(messages + [{
            "role": "system",
            "content": (
                "The user is reviewing their generated bot. "
                "Answer questions or offer to make changes. "
                "Remind them to send /end when done."
            )
        }])
        
        return llm_response["content"]
    
    async def _handle_iteration(
        self,
        message: str,
        project: BotProject,
        messages: List[Dict]
    ) -> str:
        """Handle iterative code refinement."""
        # This is handled separately in the workflow
        return ""
    
    def _looks_like_token(self, text: str) -> bool:
        """Check if text looks like a bot token."""
        import re
        token_pattern = r'^\d+:[A-Za-z0-9_-]+$'
        return bool(re.match(token_pattern, text.strip()))
    
    def _validate_token_format(self, token: str) -> bool:
        """Validate token format."""
        import re
        # Telegram bot tokens: numbers:alphanumeric_with_dash_underscore
        token_pattern = r'^\d{8,10}:[A-Za-z0-9_-]{35}$'
        return bool(re.match(token_pattern, token.strip()))


# Global orchestrator instance
orchestrator = ConversationalOrchestrator()
