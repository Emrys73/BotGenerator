"""Enhanced command handlers with LLM integration."""

from aiogram import Router, types
from aiogram.filters import Command
from aiogram.fsm.context import FSMContext
import logging
import sys
from pathlib import Path

sys.path.append(str(Path(__file__).parent.parent.parent))

from bot_generator.services.session_manager import session_manager
from bot_generator.services.conversational_orchestrator import orchestrator
from bot_generator.models.project import ProjectStatus


router = Router()
logger = logging.getLogger(__name__)


@router.message(Command("start"))
async def start_handler(message: types.Message, state: FSMContext):
    """Handle /start command."""
    await state.clear()
    
    welcome_text = """
🤖 <b>Welcome to BotGenerator AI!</b>

I'm your intelligent bot creation assistant powered by AI. I'll help you build custom Telegram bots through natural conversation!

<b>How it works:</b>
1. Send /create to start
2. Tell me about your bot idea
3. I'll ask questions to understand better
4. Provide your bot token when I ask
5. I'll generate your complete bot
6. Download and run immediately!

<b>What makes me special:</b>
• 🤖 AI-powered conversation
• 📚 Smart research capabilities  
• 🔄 Iterative refinement
• ✨ Natural language understanding

<b>Commands:</b>
/create - Start building a bot
/status - Check current project
/end - Complete current project
/help - Detailed help
/examples - See examples

<b>Ready to create something amazing? Send /create! 🚀</b>
"""
    await message.answer(welcome_text)


@router.message(Command("create"))
async def create_handler(message: types.Message, state: FSMContext):
    """Start new bot creation with AI conversation."""
    user_id = message.from_user.id
    
    # Check for active project
    if session_manager.has_active_project(user_id):
        project = session_manager.get_project(user_id)
        await message.answer(
            f"⚠️ <b>You already have an active bot project!</b>\n\n"
            f"📋 Project ID: <code>{project.project_id}</code>\n"
            f"⏰ Started: {project.started_at.strftime('%H:%M:%S')}\n"
            f"📊 Status: {project.status.value}\n\n"
            f"<b>Options:</b>\n"
            f"• Continue working on it (just send me a message)\n"
            f"• Send /end to close this project first\n"
            f"• Send /status for details"
        )
        return
    
    # Start new project
    try:
        project = session_manager.start_project(user_id)
        session_manager.update_project_status(user_id, ProjectStatus.GATHERING_REQUIREMENTS)
        
        greeting = """
👋 <b>Hi! Let's build your bot together!</b>

I'm here to help you create exactly what you need. Just tell me in your own words:

<b>What kind of bot would you like to create?</b>

You can be as detailed or as brief as you like. For example:
• "I want an expense tracker"
• "A quiz bot with multiple choice questions"
• "Something to remind me of tasks"
• Or describe your own unique idea!

I'll ask questions if I need more clarity. Let's chat! 💬
"""
        
        await message.answer(greeting)
        logger.info(f"Started new project {project.project_id} for user {user_id}")
        
    except ValueError as e:
        await message.answer(f"❌ Error: {str(e)}")


@router.message(Command("end"))
async def end_handler(message: types.Message, state: FSMContext):
    """End current bot project."""
    user_id = message.from_user.id
    
    if not session_manager.has_active_project(user_id):
        await message.answer(
            "ℹ️ You don't have an active project.\n\n"
            "Send /create to start building a bot!"
        )
        return
    
    project = session_manager.get_project(user_id)
    
    # End project
    session_manager.end_project(user_id)
    await state.clear()
    
    summary = f"""
✅ <b>Project Completed!</b>

📋 Project ID: <code>{project.project_id}</code>
⏱️ Duration: {(project.last_updated - project.started_at).total_seconds():.0f}s
🔄 Iterations: {project.iteration_count}
💬 Messages: {len(project.conversation_history)}

Thank you for using BotGenerator! 🎉

<b>Want to create another bot?</b>
Send /create to start fresh!
"""
    
    await message.answer(summary)
    logger.info(f"Ended project {project.project_id} for user {user_id}")


@router.message(Command("status"))
async def status_handler(message: types.Message):
    """Show current project status."""
    user_id = message.from_user.id
    
    if not session_manager.has_active_project(user_id):
        await message.answer(
            "ℹ️ No active project.\n\n"
            "Send /create to start building a bot!"
        )
        return
    
    project = session_manager.get_project(user_id)
    
    # Calculate duration
    duration = project.last_updated - project.started_at
    duration_str = f"{duration.total_seconds():.0f}s"
    if duration.total_seconds() > 60:
        duration_str = f"{duration.total_seconds() / 60:.1f}m"
    
    status_text = f"""
📊 <b>Current Project Status</b>

<b>Project Details:</b>
• ID: <code>{project.project_id}</code>
• Status: {project.status.value.replace('_', ' ').title()}
• Duration: {duration_str}

<b>Progress:</b>
• Messages: {len(project.conversation_history)}
• Iterations: {project.iteration_count}
• Bot Name: {project.bot_name or 'Not set'}
• Has Token: {'✅' if project.bot_token else '❌'}

<b>Generated Files:</b>
{f"• {len(project.generated_files)} files created" if project.generated_files else "• Not generated yet"}

<b>Actions:</b>
• Continue chatting to work on your bot
• Send /end to complete project
"""
    
    await message.answer(status_text)


@router.message(Command("help"))
async def help_handler(message: types.Message):
    """Show detailed help."""
    help_text = """
<b>🆘 BotGenerator AI - Help Guide</b>

<b>🎯 What I Can Do:</b>
• Create custom Telegram bots from your ideas
• Have natural conversations to understand requirements
• Ask clarifying questions when needed
• Generate production-ready code
• Make iterative improvements based on feedback

<b>🤖 Supported Bot Types:</b>
• Expense Tracker - Track spending with categories
• Reminder Bot - Schedule notifications
• Quiz/Trivia Bot - Questions and scoring
• Echo Bot - Simple message repeater
• Todo List - Task management
• Poll Bot - Create and manage polls
• Custom - Your unique idea!

<b>💡 How to Get Best Results:</b>
1. Be conversational - describe in your own words
2. Answer my questions honestly
3. Don't worry about technical details
4. Tell me if something isn't clear
5. Request changes anytime!

<b>🔑 Getting a Bot Token:</b>
1. Open Telegram, search @BotFather
2. Send /newbot
3. Choose name and username
4. Copy the token
5. Paste it when I ask

<b>📝 Example Conversation:</b>
<i>You: I want to track my expenses
Me: Great! Should it have categories? Export features?
You: Yes to both
Me: Perfect! Paste your bot token...
[generates bot]</i>

<b>Commands:</b>
/create - Start new bot
/status - Check progress
/end - Complete project
/examples - See examples

Need help? Just ask me anything!
"""
    await message.answer(help_text)


@router.message(Command("examples"))
async def examples_handler(message: types.Message):
    """Show example bot descriptions."""
    examples_text = """
<b>📚 Example Bot Conversations</b>

<b>1. Simple Echo Bot</b>
<i>"I want a simple echo bot"</i>
→ Creates bot that repeats messages

<b>2. Expense Tracker</b>
<i>"Create an expense tracker with categories and CSV export"</i>
→ Full-featured expense tracking bot

<b>3. Quiz Bot</b>
<i>"I need a quiz bot with multiple choice questions and scoring"</i>
→ Interactive quiz bot with leaderboard

<b>4. Reminder Bot</b>
<i>"Build a reminder bot that schedules notifications"</i>
→ Bot with scheduling capabilities

<b>5. Custom Bot</b>
<i>"I want a bot that helps me learn Spanish vocabulary"</i>
→ We'll design it together through conversation!

<b>💡 Tips:</b>
• Be as specific or general as you like
• I'll ask questions to clarify
• You can request changes anytime
• Describe features you want

<b>Ready to create yours?</b>
Send /create to start!
"""
    await message.answer(examples_text)


@router.message(Command("cancel"))
async def cancel_handler(message: types.Message):
    """Alias for /end command."""
    await end_handler(message, FSMContext.from_user(message.from_user.id))
