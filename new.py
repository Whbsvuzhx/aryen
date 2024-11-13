import os
import logging
from telegram import Update, Document
from telegram.ext import Application, CommandHandler, MessageHandler, filters, ContextTypes

# Set up logging
logging.basicConfig(
    format='%(asctime)s - %(name)s - %(levelname)s - %(message)s', level=logging.INFO
)
logger = logging.getLogger(__name__)

# Directly set your bot token here
BOT_TOKEN = '7329014487:AAFWyiXtttJU-QXkfQ8CsWoHiJhpQ44oubo'  # Replace with your actual bot token

# Specify the directory to save text files
SAVE_DIRECTORY = '/sdcard/download/converted_hex_files'

# Create the directory if it doesn't exist
os.makedirs(SAVE_DIRECTORY, exist_ok=True)


ADMIN_IDS = [1342302666, 987654321]


user_approvals = {}


async def start(update: Update, context: ContextTypes.DEFAULT_TYPE):
    await update.message.reply_text("Send me multiple binary (.bin) files, and I'll convert them to a single hex format!")


async def approve_user(update: Update, context: ContextTypes.DEFAULT_TYPE):
    user_id = update.message.from_user.id
    if user_id not in ADMIN_IDS:
        await update.message.reply_text("You do not have permission to approve users.")
        return

    if context.args:
        user_to_approve = int(context.args[0])
        user_approvals[user_to_approve] = True
        await update.message.reply_text(f"User  {user_to_approve} has been approved.")
    else:
        await update.message.reply_text("Please provide the user ID to approve.")

# Convert multiple files to hex payload format
async def convert_bins_to_hex(update: Update, context: ContextTypes.DEFAULT_TYPE):
    user_id = update.message.from_user.id
    if user_id not in user_approvals or not user_approvals[user_id]:
        await update.message.reply_text("You need to be approved by an admin to use this feature.")
        return

    try:
        if update.message.document:
            hex_strings = []
            documents = [update.message.document] if isinstance(update.message.document, Document) else update.message.document

            for file in documents:
                if file.file_name.endswith('.bin'):
                    # Download the file
                    file_path = await context.bot.get_file(file.file_id)
                    file_data = await file_path.download_as_bytearray()

                    # Convert to hex format with quotes
                    hex_string = ''.join(f'\\x{byte:02X}' for byte in file_data)
                    hex_strings.append(f'"{hex_string}"')  # Enclose in quotes

            # Prepare the combined hex string with a comma after each hex string
            combined_hex_string = ', '.join(hex_strings) + ','  # Add a comma at the end

            # Save the combined hex string to a .txt file
            txt_file_name = "combined.txt"
            txt_file_path = os.path.join(SAVE_DIRECTORY, txt_file_name)

            # Write to the file (create if it doesn't exist)
            with open(txt_file_path, 'a') as txt_file:
                txt_file.write(combined_hex_string + '\n')  # Add a newline after the entry

            logger.info(f"Combined Hex Payload appended to {txt_file_path}")

            # Send the file back to the user
            with open(txt_file_path, 'rb') as txt_file:
                await update.message.reply_document(document=txt_file, filename=txt_file_name)

        else:
            await update.message.reply_text("Please upload files.")
    except Exception as e:
        logger.error(f"Error processing files: {e}")
        await update.message.reply_text("An error occurred while processing your files.")

def main():
    application = Application.builder().token(BOT_TOKEN).build()
    application.add_handler(CommandHandler("start", start))
    application.add_handler(CommandHandler("approve", approve_user))  
    application.add_handler(MessageHandler(filters.Document.ALL, convert_bins_to_hex))
    application.run_polling()

if __name__ == '__main__':
    main()
