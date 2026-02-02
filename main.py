"""Main entry point for BotGenerator - The MCP-based Telegram Bot Generator."""

import asyncio
import logging
from aiogram import Bot, Dispatcher
from aiogram.client.default import DefaultBotProperties
from aiogram.enums import ParseMode
from dotenv import load_dotenv
import os
import sys
from pathlib import Path

# Add parent directory to path
sys.path.append(str(Path(__file__).parent.parent))

# Load environment variables from parent directory
env_path = Path(__file__).parent.parent / '.env'
load_dotenv(dotenv_path=env_path)

# Import handlers
from handlers import start, messages

# Configure logging
logging.basicConfig(
    level=logging.INFO,
    format='%(asctime)s - %(name)s - %(levelname)s - %(message)s'
)
logger = logging.getLogger(__name__)


async def main():
    """Main bot function."""
    logger.info("Starting BotGenerator (MCP-based Bot Generator)...")
    
    # Get bot token
    bot_token = os.getenv("BOT_TOKEN")
    if not bot_token:
        raise ValueError("BOT_TOKEN not set in environment")
    
    # Initialize bot and dispatcher
    bot = Bot(
        token=bot_token,
        default=DefaultBotProperties(parse_mode=ParseMode.HTML)
    )
    dp = Dispatcher()
    
    # Register handlers
    dp.include_router(start.router)
    dp.include_router(messages.router)
    
    logger.info("BotGenerator is running and ready to create bots! 🤖")
    logger.info("Connected to 5 MCP servers:")
    logger.info("  • Parser - Intent parsing")
    logger.info("  • Architecture Designer - Bot design")
    logger.info("  • Template Library - Code templates")
    logger.info("  • Code Generator - Code generation")
    logger.info("  • Validator - Code validation")
    
    # Start polling
    try:
        await dp.start_polling(bot)
    except KeyboardInterrupt:
        logger.info("Received shutdown signal")
    except Exception as e:
        logger.error(f"Error in bot: {e}", exc_info=True)
    finally:
        await bot.session.close()
        logger.info("BotGenerator stopped.")


if __name__ == "__main__":
    asyncio.run(main())
