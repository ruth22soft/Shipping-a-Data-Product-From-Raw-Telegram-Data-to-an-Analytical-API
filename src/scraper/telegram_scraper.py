# Telegram scraper logic
import os
import json
import logging
from datetime import datetime
from pathlib import Path
from telethon import TelegramClient
from telethon.errors import RPCError
from dotenv import load_dotenv
import asyncio

# Load environment variables
load_dotenv()

# Configure logging
logging.basicConfig(
    filename='data/scrape.log',
    level=logging.INFO,
    format='%(asctime)s - %(levelname)s - %(message)s'
)
logger = logging.getLogger(__name__)

# Telegram API credentials
api_id = os.getenv('TELEGRAM_API_ID')
api_hash = os.getenv('TELEGRAM_API_HASH')
phone = os.getenv('TELEGRAM_PHONE')

# Define channels to scrape
channels = [
    'CheMed123',
    'lobelia4cosmetics',
    'tikvahpharma'
    # Add more channels from https://et.tgstat.com/medicine as needed
]

# Data Lake paths
messages_dir = Path('E:/week_7/Shipping-a-Data-Product-From-Raw-Telegram-Data-to-an-Analytical-API/data/raw/telegram_messages')
images_dir = Path('E:/week_7/Shipping-a-Data-Product-From-Raw-Telegram-Data-to-an-Analytical-API/data/raw/telegram_images')
messages_dir.mkdir(exist_ok=True)
images_dir.mkdir(exist_ok=True)

async def scrape_channel(client, channel):
    """
    Scrape messages and images from a Telegram channel.
    """
    try:
        logger.info(f"Scraping channel: {channel}")
        # Get the channel entity
        entity = await client.get_entity(channel)
        
        # Create date-based directory
        today = datetime.now().strftime('%Y-%m-%d')
        message_output_dir = messages_dir / today / channel
        image_output_dir = images_dir / today / channel
        message_output_dir.mkdir(parents=True, exist_ok=True)
        image_output_dir.mkdir(parents=True, exist_ok=True)

        # Prepare JSON file
        messages_file = message_output_dir / 'messages.json'
        messages = []

        # Iterate over messages
        async for message in client.iter_messages(entity, limit=100):  # Adjust limit as needed
            message_data = {
                'id': message.id,
                'date': message.date.isoformat(),
                'text': message.text or '',
                'has_image': message.photo is not None
            }
            messages.append(message_data)

            # Download image if available
            if message.photo:
                image_filename = f"image_{message.id}.jpg"
                image_path = image_output_dir / image_filename
                await client.download_media(message.photo, file=image_path)
                logger.info(f"Downloaded image: {image_path}")
                message_data['image_path'] = str(image_path)

        # Save messages to JSON
        with open(messages_file, 'w', encoding='utf-8') as f:
            json.dump(messages, f, indent=4, ensure_ascii=False)
        logger.info(f"Saved {len(messages)} messages to {messages_file}")

    except RPCError as e:
        logger.error(f"Error scraping {channel}: {e}")
        raise

async def main():
    """
    Initialize Telegram client and scrape all channels.
    """
    async with TelegramClient('session_name', api_id, api_hash) as client:
        # Authenticate if not already logged in
        await client.start(phone=phone)
        logger.info("Telegram client started")

        # Scrape each channel
        for channel in channels:
            await scrape_channel(client, channel)

if __name__ == '__main__':
    asyncio.run(main())