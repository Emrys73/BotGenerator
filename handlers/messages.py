"""Conversational message handler with LLM orchestration."""

from aiogram import Router, types, F
from aiogram.fsm.context import FSMContext
import logging
import io
import sys
from pathlib import Path

sys.path.append(str(Path(__file__).parent.parent.parent))

from bot_generator.services.session_manager import session_manager
from bot_generator.services.conversational_orchestrator import orchestrator
from bot_generator.services.generator_service import BotGenerator
from bot_generator.models.project import ProjectStatus


router = Router()
logger = logging.getLogger(__name__)

# Initialize services
bot_gen = BotGenerator()


@router.message(F.text & ~F.text.startswith('/'))
async def message_handler(message: types.Message, state: FSMContext):
    """Handle conversational messages with LLM orchestration."""
    user_id = message.from_user.id
    user_message = message.text.strip()
    
    # Check if user has active project
    if not session_manager.has_active_project(user_id):
        await message.answer(
            "👋 Hi! To start creating a bot, send /create\n\n"
            "Or send /help for more information."
        )
        return
    
    project = session_manager.get_project(user_id)
    
    try:
        # Show typing indicator
        await message.bot.send_chat_action(message.chat.id, "typing")
        
        # Special handling for generation state
        if project.status == ProjectStatus.GENERATING:
            await handle_generation(message, project)
            return
        
        # Special handling for iteration state  
        if project.status == ProjectStatus.ITERATING:
            await handle_iteration(message, project)
            return
        
        # Process message through LLM orchestrator
        response = await orchestrator.process_message(
            user_id=user_id,
            message=user_message,
            project=project
        )
        
        # Send response
        if response:
            await message.answer(response)
        
        # Check if we need to trigger generation
        if project.status == ProjectStatus.GENERATING:
            await handle_generation(message, project)
        
    except Exception as e:
        logger.error(f"Error processing message: {e}", exc_info=True)
        await message.answer(
            "❌ <b>Sorry, something went wrong!</b>\n\n"
            f"Error: {str(e)}\n\n"
            "Please try again or send /end to restart."
        )


async def handle_generation(message: types.Message, project):
    """Handle bot code generation with progress updates."""
    user_id = message.from_user.id
    
    try:
        from bot_generator.utils.progress_tracker import generate_simple_progress_bar
        from aiogram.types import InlineKeyboardMarkup, InlineKeyboardButton
        
        # Build bot description from conversation
        bot_description = project.bot_description or " ".join(
            turn.content for turn in project.conversation_history 
            if turn.role == "user"
        )[:500]
        
        # Send progress message with game button
        game_keyboard = InlineKeyboardMarkup(inline_keyboard=[
            [InlineKeyboardButton(
                text="🎮 Play Space Shooter While You Wait!",
                url="http://localhost:8000/games/space-shooter/index.html"
            )]
        ])
        
        progress_msg = await message.answer(
            "🤖 <b>Bot Generation Started!</b>\n\n"
            f"{generate_simple_progress_bar(0, 6)}\n\n"
            "Current Stage: Initializing...\n"
            "⏱️ <b>Estimated time:</b> ~15s\n\n"
            "🎮 Play a game while you wait! ⬇️",
            reply_markup=game_keyboard
        )
        
        # Progress update callback
        async def update_progress(stage_num, total_stages, stage_name):
            try:
                completed_stages = []
                if stage_num >= 1:
                    completed_stages.append("✅ Parsed requirements")
                if stage_num >= 2:
                    completed_stages.append("✅ Designed architecture")
                if stage_num >= 3:
                    completed_stages.append("✅ Found templates")
                if stage_num >= 4:
                    completed_stages.append("✅ Generated code")
                if stage_num >= 5:
                    completed_stages.append("✅ Validated")
                if stage_num >= 6:
                    completed_stages.append("✅ Packaged")
                
                remaining_time = max(0, (6 - stage_num) * 2.5)
                
                status_text = (
                    f"🤖 <b>Bot Generation In Progress</b>\n\n"
                    f"<b>{generate_simple_progress_bar(stage_num, total_stages)}</b>\n\n"
                    f"{chr(10).join(completed_stages)}\n\n"
                    f"{stage_name}...\n\n"
                    f"⏱️ <b>Est. time remaining:</b> ~{int(remaining_time)}s"
                )
                
                await progress_msg.edit_text(status_text, reply_markup=game_keyboard)
            except Exception as e:
                logger.error(f"Error updating progress: {e}")
        
        # Generate bot with progress updates
        result = await bot_gen.generate_bot(
            user_prompt=bot_description,
            user_token=project.bot_token,
            progress_callback=update_progress
        )
        
        if not result.get("success"):
            await progress_msg.edit_text(
                f"❌ <b>Generation failed</b>\n\n"
                f"Error: {result.get('error')}\n\n"
                "Let's try again. What would you like to change?"
            )
            project.status = ProjectStatus.GATHERING_REQUIREMENTS
            return
        
        # Store generated files
        project.generated_files = result["files"]
        project.architecture = result["architecture"]
        project.bot_name = result["bot_name"]
        project.status = ProjectStatus.REVIEWING
        
        # Final progress update
        await progress_msg.edit_text(
            "🎉 <b>Bot Generation Complete!</b>\n\n"
            f"<b>{generate_simple_progress_bar(6, 6)}</b>\n\n"
            "✅ Parsed requirements\n"
            "✅ Designed architecture\n"
            "✅ Found templates\n"
            "✅ Generated code\n"
            "✅ Validated\n"
            "✅ Packaged\n\n"
            "📦 Sending your bot files..."
        )
        
        # Show success message
        intent = result["intent"]
        arch = result["architecture"]
        validation = result["validation"]
        
        success_msg = f"""
🎉 <b>Your Bot is Ready!</b>

<b>📋 Details:</b>
• Name: <code>{result['bot_name']}</code>
• Type: {intent['bot_type']}
• Framework: {arch['framework']}
• Complexity: {arch['complexity']}
• Files: {result['file_count']}

<b>✅ Validation:</b>
• Syntax: {validation['syntax']['summary']}
• Logic: {validation['logic']['summary']}
• Security: {validation['security']['summary']}

Sending ZIP file...
"""
        
        await message.answer(success_msg)
        
        # Send ZIP file
        zip_file = types.BufferedInputFile(
            result["zip_data"],
            filename=f"{result['bot_name']}.zip"
        )
        
        setup_instructions = f"""
📦 <b>Setup Instructions</b>

<b>✨ Your bot is pre-configured and ready!</b>

<b>Step 1:</b> Download & Extract
<code>unzip {result['bot_name']}.zip</code>
<code>cd {result['bot_name']}</code>

<b>Step 2:</b> Install Dependencies
<code>pip install -r requirements.txt</code>

<b>Step 3:</b> Run Your Bot! 🚀
<code>python main.py</code>

<b>That's it!</b> Your bot token is already configured.

<b>🎨 Want changes?</b>
Just tell me what to modify! For example:
• "Add a /stats command"
• "Change the welcome message"
• "Add export to PDF"

<b>✅ Happy with it?</b>
Send /end to complete this project!
"""
        
        await message.answer_document(
            zip_file,
            caption=setup_instructions
        )
        
        logger.info(f"Generated bot '{result['bot_name']}' for user {user_id}")
        
    except Exception as e:
        logger.error(f"Generation error: {e}", exc_info=True)
        await message.answer(
            f"❌ <b>Generation failed</b>\n\n{str(e)}\n\n"
            "Send /end to restart."
        )


async def handle_iteration(message: types.Message, project):
    """Handle iterative code refinement."""
    user_id = message.from_user.id
    
    try:
        # User's change request
        change_request = message.text.strip()
        
        await message.answer(
            "🔄 <b>Updating your bot...</b>\n\n"
            "Analyzing your request and modifying code...\n"
            "This may take a moment."
        )
        
        # TODO: Implement actual code modification
        # For now, regenerate with updated prompt
        updated_prompt = project.bot_description + "\n\nAlso: " + change_request
        
        result = await bot_gen.generate_bot(
            user_prompt=updated_prompt,
            user_token=project.bot_token
        )
        
        if not result.get("success"):
            await message.answer(
                f"❌ Update failed: {result.get('error')}\n\n"
                "Let's try a different approach?"
            )
            project.status = ProjectStatus.REVIEWING
            return
        
        # Update project
        project.generated_files = result["files"]
        project.iteration_count += 1
        project.status = ProjectStatus.REVIEWING
        
        # Send updated ZIP
        zip_file = types.BufferedInputFile(
            result["zip_data"],
            filename=f"{result['bot_name']}_v{project.iteration_count}.zip"
        )
        
        await message.answer(
            f"✅ <b>Updated!</b> (v{project.iteration_count})\n\n"
            f"Changes applied to {result['file_count']} files.\n\n"
            f"Sending updated ZIP..."
        )
        
        await message.answer_document(
            zip_file,
            caption=(
                f"📦 <b>Updated Bot (v{project.iteration_count})</b>\n\n"
                f"Your changes have been applied!\n\n"
                f"Want more changes? Just tell me!\n"
                f"Happy with it? Send /end"
            )
        )
        
        logger.info(f"Iteration {project.iteration_count} for user {user_id}")
        
    except Exception as e:
        logger.error(f"Iteration error: {e}", exc_info=True)
        await message.answer(
            f"❌ Update failed: {str(e)}\n\n"
            "Try describing the change differently?"
        )
        project.status = ProjectStatus.REVIEWING
