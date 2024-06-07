from flask import Flask, request
from telegram import Update, InlineKeyboardButton, InlineKeyboardMarkup
from telegram.ext import Updater, CommandHandler, CallbackQueryHandler, MessageHandler, Filters
import requests
import json

app = Flask(__name__)

TELEGRAM_TOKEN = 'YOUR_TELEGRAM_BOT_API_TOKEN'
SOLANA_RPC_URL = 'https://api.mainnet-beta.solana.com'
SOLANA_RECIPIENT_ADDRESS = 'RECIPIENT_SOLANA_ADDRESS'

updater = Updater(TELEGRAM_TOKEN, use_context=True)

def start(update, context):
    update.message.reply_text('Welcome! Send your token address to get started.')

def handle_message(update, context):
    user_message = update.message.text
    if user_message.startswith('SOL'):
        # Process token address
        context.user_data['token_address'] = user_message
        update.message.reply_text('Send your Telegram link to make it clickable in the Trending List.')
    elif user_message.startswith('https://t.me/'):
        context.user_data['telegram_link'] = user_message
        update.message.reply_text('Select promotion length and type.', reply_markup=get_promotion_keyboard())

def get_promotion_keyboard():
    keyboard = [
        [InlineKeyboardButton('Top 3 - 3 Hours - 0.01 SOL', callback_data='top3_3h_0.01'),
         InlineKeyboardButton('Top 10 - 3 Hours - 0.008 SOL', callback_data='top10_3h_0.008')],
        # Add more buttons here
    ]
    return InlineKeyboardMarkup(keyboard)

def button_callback(update, context):
    query = update.callback_query
    query.answer()
    # Extract data from the callback_data and process payment
    selection = query.data.split('_')
    slot_type, duration, cost = selection[0], selection[1], selection[2]
    token_address = context.user_data.get('token_address')
    telegram_link = context.user_data.get('telegram_link')
    # Process payment here using Solana
    success = process_solana_payment(token_address, float(cost))
    if success:
        query.edit_message_text(text=f"Promotion set: {slot_type} for {duration} at {cost} SOL.")
        # Update trending list and notify user
    else:
        query.edit_message_text(text="Payment failed, please try again.")

def process_solana_payment(sender_address, amount):
    try:
        # Create the transaction
        transaction = {
            "jsonrpc": "2.0",
            "id": 1,
            "method": "sendTransaction",
            "params": [
                {
                    "from_pubkey": sender_address,
                    "to_pubkey": SOLANA_RECIPIENT_ADDRESS,
                    "lamports": int(amount * 10**9)  # Convert SOL to lamports
                }
            ]
        }
        headers = {'Content-Type': 'application/json'}
        response = requests.post(SOLANA_RPC_URL, headers=headers, data=json.dumps(transaction))
        response_json = response.json()
        if 'result' in response_json:
            return True
        else:
            print(f"Payment failed: {response_json}")
            return False
    except Exception as e:
        print(f"An error occurred: {e}")
        return False

def main():
    dp = updater.dispatcher

    dp.add_handler(CommandHandler('start', start))
    dp.add_handler(MessageHandler(Filters.text & ~Filters.command, handle_message))
    dp.add_handler(CallbackQueryHandler(button_callback))

    updater.start_polling()
    updater.idle()

@app.route('/webhook', methods=['POST'])
def webhook():
    update = Update.de_json(request.get_json(), updater.bot)
    updater.dispatcher.process_update(update)
    return "ok"

if __name__ == '__main__':
    main()
    app.run(port=8443)
