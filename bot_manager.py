import os
import time
import inspect
import logging
from telegram.ext import Updater, CommandHandler
from telegram.ext import MessageHandler, Filters
from telegram_helper import *
from bitmex_api import BitmexApi

logging.basicConfig(format='%(asctime)s - %(name)s - %(levelname)s - %(message)s',
                    level=logging.INFO)

logger = logging.getLogger(__name__)

all_commands = {"/help": "List of all commands",
                "/long": "Create buy market order. ::Symbol, Quantity",
                "/short": "Create sell market order. ::Symbol, Quantity",
                "/margin_status": "Get margin status",
                "/positions": "Get open positions",
                "/orders": "Get orders ::Last-n",
                "/cancel": "Cancel order with ID ::OrderID",
                "/cancel_all": "Cancel all orders",
                "/leverage": "Set leverage ::Symbol, leverage",
                "/history": "Get wallet history. ::Last n history",
                "/instrument": "Get instrument(s). ::Symbol",
                "/indices": "Get price indices. ::Root Symbol"}

DEF_MESSAGE = "This is a private bot to manage Bitmex account.\n" \
              "You can also set it up with your own Bitmex aaccount.\n\n" \
              "Get the source code here: {}\n" \
              "or contact {} for help.".format("https://github.com/SpiralDevelopment/Bitmex-to-Telegram",
                                              "@spiral_dev")
USD_CONTRACTS = ['ETH', 'XBT']

CONTRACTS_CODE = "U20"
TELEGRAM_BOT_TOKEN = "YOUR_TELEGRAM_BOT_TOKEN"


class TelegramBot(object):

    def __init__(self):
        try:
            self.bitmex_api = BitmexApi(api_key=os.environ['BITMEX_API_KEY'],
                                        api_secret=os.environ['BITMEX_API_SECRET'])
            self.updater = Updater(TELEGRAM_BOT_TOKEN)

            self.dispatcher = self.updater.dispatcher
            self.echo_handler = MessageHandler(Filters.text, self.unknown_text)
            self.unknown_handler = MessageHandler(Filters.command, self.unknown_command)

            self.margin_status = CommandHandler('margin_status', self.get_margin_status)
            self.positions = CommandHandler('positions', self.get_positions)
            self.cancel = CommandHandler('cancel', self.cancel_order, pass_args=True)
            self.cancel_all = CommandHandler('cancel_all', self.cancel_all_orders, pass_args=True)
            self.orders = CommandHandler('orders', self.get_orders, pass_args=True)
            self.buy_market_order = CommandHandler('long', self.create_buy_market_order, pass_args=True)
            self.sell_market_order = CommandHandler('short', self.create_sell_market_order, pass_args=True)
            self.leverage = CommandHandler('leverage', self.set_leverage, pass_args=True)
            self.history = CommandHandler('history', self.get_wallet_history, pass_args=True)
            self.instrument = CommandHandler('instrument', self.get_instrument, pass_args=True)
            self.indices = CommandHandler('indices', self.get_indices, pass_args=True)
            self.help = CommandHandler('help', self.get_help)

            self.is_initialized = True
        except KeyError as e:
            self.is_initialized = False
            logger.error(str(e))

    def run(self):
        self.dispatcher.add_handler(self.help)
        self.dispatcher.add_handler(self.margin_status)
        self.dispatcher.add_handler(self.positions)
        self.dispatcher.add_handler(self.orders)
        self.dispatcher.add_handler(self.cancel)
        self.dispatcher.add_handler(self.cancel_all)
        self.dispatcher.add_handler(self.buy_market_order)
        self.dispatcher.add_handler(self.sell_market_order)
        self.dispatcher.add_handler(self.leverage)
        self.dispatcher.add_handler(self.history)
        self.dispatcher.add_handler(self.indices)
        self.dispatcher.add_handler(self.instrument)

        self.dispatcher.add_handler(self.echo_handler)
        self.dispatcher.add_handler(self.unknown_handler)

        self.updater.start_polling()
        self.updater.idle()

    @staticmethod
    def get_help(bot, update):
        logger.info(inspect.stack()[0][3])
        logger.info("Admin Chat ID: %s", update.message.chat_id)
        logger.info("First Name: %s", update.message.from_user.first_name)
        logger.info("Last Name: %s", update.message.from_user.last_name)
        message = DEF_MESSAGE

        if is_admin_texting(update):
            message = ''

            for key, value in all_commands.items():
                message = message + "{0} - {1} \n".format(key, value)

        bot.send_message(chat_id=update.message.chat_id, text=message)

    def get_positions(self, bot, update):
        logger.info(inspect.stack()[0][3])
        message = DEF_MESSAGE

        if is_admin_texting(update):
            try:
                response = self.bitmex_api.get_positions()
                logger.info(response)

                if isinstance(response, list) and len(response) > 0:
                    message = ''
                    for pos in response:
                        margin = float(pos['posMargin']) / (10 ** 8)

                        if margin > 0:
                            message += "Symbol: {}\n" \
                                       "Foreign Notional: {}\n" \
                                       "Home Notional: {}\n" \
                                       "Entry Price: {}\n" \
                                       "Mark Price: {}\n" \
                                       "Liq Price: {}\n" \
                                       "Margin: {}\n" \
                                       "Leverage: {}\n" \
                                       "Unrealised Pnl: {}\n" \
                                       "Unrealised Pnl Roe: {}\n" \
                                       "Realised Pnl: {}\n\n".format(pos['symbol'],
                                                                     pos['foreignNotional'],
                                                                     pos['homeNotional'],
                                                                     pos['avgEntryPrice'],
                                                                     pos['markPrice'],
                                                                     pos['liquidationPrice'],
                                                                     margin,
                                                                     pos['leverage'],
                                                                     float(pos['unrealisedPnl']) / (10 ** 8),
                                                                     pos['unrealisedRoePcnt'],
                                                                     float(pos['realisedPnl']) / (10 ** 8))
                else:
                    message = "No open positions"

            except Exception as e:
                logger.error(str(e))
                message = str(e)

        bot.send_message(chat_id=update.message.chat_id, text=message)

    def get_orders(self, bot, update, args):
        logger.info('%s %s', inspect.stack()[0][3], args)
        message = DEF_MESSAGE

        if is_admin_texting(update):
            try:
                n = int(args[0]) if len(args) > 0 else 3

                response = self.bitmex_api.get_orders()
                logger.info(response)
                message = ""

                for order in response[-n:]:
                    message += "Symbol: {}\n" \
                               "Status: {}\n" \
                               "Price: {}\n" \
                               "Qty: {}\n" \
                               "Time: {}\n" \
                               "Side: {}\n" \
                               "Order Type: {}\n" \
                               "Order ID: {}\n" \
                               "clOrd ID: {}\n" \
                               "Execution Instruction: {}\n" \
                               "StopPx: {}\n" \
                               "TimeInForce: {}\n" \
                               "Triggered: {}\n\n".format(order['symbol'],
                                                          order['ordStatus'],
                                                          order['price'],
                                                          order['orderQty'],
                                                          order['timestamp'],
                                                          order['side'],
                                                          order['ordType'],
                                                          order['orderID'],
                                                          order['clOrdID'],
                                                          order['execInst'],
                                                          order['stopPx'],
                                                          order['timeInForce'],
                                                          order['triggered'])

            except Exception as e:
                logger.error(str(e))
                message = str(e)

        bot.send_message(chat_id=update.message.chat_id, text=message)

    def cancel_order(self, bot, update, args):
        logger.info('%s %s', inspect.stack()[0][3], args)
        message = DEF_MESSAGE

        if is_admin_texting(update):
            try:
                if len(args) > 0:
                    order_id = args[0]

                    if '-' in order_id:
                        response = self.bitmex_api.cancel_order(orderID=order_id)
                    else:
                        response = self.bitmex_api.cancel_order(clOrdID=order_id)
                    logger.info(response)

                    if isinstance(response, list) and len(response) > 0:
                        message = "Order Canceled"
                    elif isinstance(response, dict) and 'error' in response:
                        message = "{}\n{}".format(response['error']['name'],
                                                  response['error']['message'])
                    else:
                        message = 'No order canceled'
                else:
                    message = 'Send clOrd ID or order ID'
            except Exception as e:
                logger.error(str(e))
                message = str(e)

        bot.send_message(chat_id=update.message.chat_id, text=message)

    def cancel_all_orders(self, bot, update, args):
        logger.info('%s %s', inspect.stack()[0][3], args)
        message = DEF_MESSAGE

        if is_admin_texting(update):
            try:
                if len(args) > 0:
                    response = self.bitmex_api.cancel_all_orders(symbol=args[0].upper())
                else:
                    response = self.bitmex_api.cancel_all_orders()

                logger.info(response)

                if isinstance(response, list) and len(response) > 0:
                    message = "Order(s) Canceled"
                elif isinstance(response, dict) and 'error' in response:
                    message = "{}\n{}".format(response['error']['name'],
                                              response['error']['message'])
                else:
                    message = 'No order(s) canceled'
            except Exception as e:
                logger.error(str(e))
                message = str(e)

        bot.send_message(chat_id=update.message.chat_id, text=message)

    def get_position(self, root_symbol):
        positions = self.bitmex_api.get_positions()

        symbol_pos = next((item for item in positions
                           if item["symbol"].startswith(root_symbol)), None)

        if symbol_pos:
            return symbol_pos
        else:
            raise Exception('Set leverage for {}'.format(root_symbol))

    def create_buy_market_order(self, bot, update, args):
        logger.info('%s %s', inspect.stack()[0][3], args)
        message = DEF_MESSAGE

        if is_admin_texting(update):
            try:
                if len(args) > 1:
                    root_symbol = args[0].upper()
                    qty = args[1]

                    if len(root_symbol) == 3:
                        if root_symbol in USD_CONTRACTS:
                            pair = root_symbol + "USD"
                        else:
                            pair = root_symbol + CONTRACTS_CODE

                        order = self.bitmex_api.create_order(pair,
                                                             orderType='Market',
                                                             orderQty=qty,
                                                             clOrdID=int(time.time()),
                                                             side='Buy')
                        logger.info(order)

                        if 'error' in order:
                            message = "{}\n{}".format(order['error']['name'],
                                                      order['error']['message'])
                        else:
                            is_rejected = True if order['ordRejReason'] else False

                            message = "Symbol: {}\n" \
                                      "Status: {}\n" \
                                      "Price: {}\n" \
                                      "Qty: {}\n" \
                                      "Time: {}\n" \
                                      "Side: {}\n" \
                                      "Order Type: {}\n" \
                                      "Order ID: {}\n" \
                                      "clOrd ID: {}\n" \
                                      "Execution Instruction: {}\n" \
                                      "StopPx: {}\n" \
                                      "TimeInForce: {}\n" \
                                      "Triggered: {}\n" \
                                      "{}\n\n".format(order['symbol'],
                                                      order['ordStatus'],
                                                      order['price'],
                                                      order['orderQty'],
                                                      order['timestamp'],
                                                      order['side'],
                                                      order['ordType'],
                                                      order['orderID'],
                                                      order['clOrdID'],
                                                      order['execInst'],
                                                      order['stopPx'],
                                                      order['timeInForce'],
                                                      order['triggered'],
                                                      order['ordRejReason'] if is_rejected else '')
                    else:
                        message = "Send 3 character root symbol"
                else:
                    message = 'Send 3 character root symbol and quantity'
            except Exception as e:
                logger.error(str(e))
                message = str(e)

        bot.send_message(chat_id=update.message.chat_id, text=message)

    def create_sell_market_order(self, bot, update, args):
        logger.info('%s %s', inspect.stack()[0][3], args)
        message = DEF_MESSAGE

        if is_admin_texting(update):
            try:
                if len(args) > 1:
                    root_symbol = args[0].upper()
                    qty = args[1]

                    if len(root_symbol) == 3:
                        if root_symbol in USD_CONTRACTS:
                            symbol = root_symbol + "USD"
                        else:
                            symbol = root_symbol + CONTRACTS_CODE

                        order = self.bitmex_api.create_order(symbol,
                                                             orderType='Market',
                                                             orderQty=qty,
                                                             clOrdID=int(time.time()),
                                                             side='Sell')
                        logger.info(order)

                        if 'error' in order:
                            message = "{}\n{}".format(order['error']['name'],
                                                      order['error']['message'])
                        else:
                            is_rejected = True if order['ordRejReason'] else False

                            message = "Symbol: {}\n" \
                                      "Status: {}\n" \
                                      "Price: {}\n" \
                                      "Qty: {}\n" \
                                      "Time: {}\n" \
                                      "Side: {}\n" \
                                      "Order Type: {}\n" \
                                      "Order ID: {}\n" \
                                      "clOrd ID: {}\n" \
                                      "Execution Instruction: {}\n" \
                                      "StopPx: {}\n" \
                                      "TimeInForce: {}\n" \
                                      "Triggered: {}\n" \
                                      "{}\n\n".format(order['symbol'],
                                                      order['ordStatus'],
                                                      order['price'],
                                                      order['orderQty'],
                                                      order['timestamp'],
                                                      order['side'],
                                                      order['ordType'],
                                                      order['orderID'],
                                                      order['clOrdID'],
                                                      order['execInst'],
                                                      order['stopPx'],
                                                      order['timeInForce'],
                                                      order['triggered'],
                                                      order['ordRejReason'] if is_rejected else '')
                    else:
                        message = "Send 3 character root symbol"
                else:
                    message = 'Send 3 character root symbol and quantity'
            except Exception as e:
                logger.error(str(e))
                message = str(e)

        bot.send_message(chat_id=update.message.chat_id, text=message)

    def set_leverage(self, bot, update, args):
        logger.info('%s %s', inspect.stack()[0][3], args)
        message = DEF_MESSAGE

        if is_admin_texting(update):
            try:
                if len(args) > 1:
                    root_symbol = args[0].upper()
                    leverage = args[1]

                    if len(root_symbol) == 3:
                        if root_symbol in USD_CONTRACTS:
                            pair = root_symbol + "USD"
                        else:
                            pair = root_symbol + CONTRACTS_CODE

                        response = self.bitmex_api.set_leverage(pair, leverage)
                        logger.info(response)

                        if 'error' in response:
                            message = "{}\n{}".format(response['error']['name'],
                                                      response['error']['message'])
                        else:
                            message = "Symbol: {}\n" \
                                      "Foreign Notional: {}\n" \
                                      "Home Notional: {}\n" \
                                      "Entry Price: {}\n" \
                                      "Mark Price: {}\n" \
                                      "Last Price: {}\n" \
                                      "Liq Price: {}\n" \
                                      "Margin: {}\n" \
                                      "Leverage: {}\n" \
                                      "Unrealised Pnl: {}\n" \
                                      "Realised Pnl: {}\n\n".format(response['symbol'],
                                                                    response['foreignNotional'],
                                                                    response['homeNotional'],
                                                                    response['avgEntryPrice'],
                                                                    response['markPrice'],
                                                                    response['lastPrice'],
                                                                    response['liquidationPrice'],
                                                                    float(response['posMargin']) / (10 ** 8),
                                                                    response['leverage'],
                                                                    float(response['unrealisedPnl']) / (10 ** 8),
                                                                    float(response['realisedPnl']) / (10 ** 8))
                    else:
                        message = 'Send 3 character root symbol (def: XBT)'
                else:
                    message = 'Send 3 character root symbol (def: XBT) and leverage'
            except Exception as e:
                logger.error(str(e))
                message = str(e)

        bot.send_message(chat_id=update.message.chat_id, text=message)

    def get_wallet_history(self, bot, update, args):
        logger.info('%s %s', inspect.stack()[0][3], args)
        message = DEF_MESSAGE

        if is_admin_texting(update):
            try:
                last_n = int(args[0]) if len(args) > 0 else 5
                response = self.bitmex_api.get_wallet_hist()

                if len(response) > 0:
                    logger.info(response)

                    balance = float(response[0]['walletBalance']) / 10 ** 8
                    message = "Balance: {}\n\n".format(balance)

                    for hist in response[:last_n]:
                        amount = float(hist['amount']) / 10 ** 8
                        message += "TxType: {}\nTxTime: {}\n" \
                                   "Status: {}\nAmount: {}\n" \
                                   "Address: {}\n\n".format(hist['transactType'],
                                                            hist['transactTime'],
                                                            hist['transactStatus'],
                                                            amount,
                                                            hist['address'])
                else:
                    message = "No wallet history"
            except Exception as e:
                logger.error(str(e))
                message = str(e)

        bot.send_message(chat_id=update.message.chat_id, text=message)

    def get_instrument(self, bot, update, args):
        logger.info('%s %s', inspect.stack()[0][3], args)
        message = DEF_MESSAGE

        if is_admin_texting(update):
            try:
                if len(args) > 0:
                    symbol = args[0]
                    response = self.bitmex_api.get_instruments(symbol=symbol)
                else:
                    response = self.bitmex_api.get_active_instruments()

                if len(response) > 0:
                    logger.info(response)
                    message = ""

                    for res in response:
                        message += "Symbol: {}\n" \
                                   "24H Volume: {}\n" \
                                   "24H Turnover: {}\n" \
                                   "{}" \
                                   "{}" \
                                   "{}" \
                                   "Maker Fee: {}\n" \
                                   "Taker Fee: {}\n" \
                                   "Open Interest: {}\n" \
                                   "Underlying Symbol: {}\n" \
                                   "Last Price: {}\n\n".format(res['symbol'],
                                                               res['homeNotional24h'],
                                                               res['turnover24h'],
                                                               "Funding Rate: {}\n".format(res['fundingRate']) if
                                                               res['fundingRate'] else '',
                                                               "Funding Time: {}\n".format(res['fundingTimestamp']) if
                                                               res['fundingTimestamp'] else '',
                                                               "Expiry: {}\n".format(res['expiry']) if res[
                                                                   'expiry'] else '',
                                                               res['makerFee'],
                                                               res['takerFee'],
                                                               res['openInterest'],
                                                               res['underlyingSymbol'],
                                                               res['lastPrice'])
                else:
                    message = "No Instruments found"
            except Exception as e:
                logger.error(str(e))
                message = str(e)

        bot.send_message(chat_id=update.message.chat_id, text=message)

    def get_margin_status(self, bot, update):
        logger.info(inspect.stack()[0][3])
        message = DEF_MESSAGE

        if is_admin_texting(update):
            try:
                response = self.bitmex_api.get_margin_status()
                logger.info(response)

                message = "Available Margin: {}\n" \
                          "Margin Balance: {}\n" \
                          "Wallet Balance: {}\n" \
                          "Margin Leverage: {:.2f}\n" \
                          "Realized PnL: {}\n" \
                          "Unrealized PnL: {}".format(float(response['availableMargin']) / (10 ** 8),
                                                      float(response['marginBalance']) / (10 ** 8),
                                                      float(response['walletBalance']) / (10 ** 8),
                                                      response['marginLeverage'],
                                                      float(response['realisedPnl']) / (10 ** 8),
                                                      float(response['unrealisedPnl']) / (10 ** 8))
            except Exception as e:
                logger.error(str(e))
                message = str(e)

        bot.send_message(chat_id=update.message.chat_id, text=message)

    def get_indices(self, bot, update, args):
        logger.info(inspect.stack()[0][3])
        message = DEF_MESSAGE

        if is_admin_texting(update):
            try:
                response = self.bitmex_api.indice_prices()
                logger.info(response)

                if len(response) > 0:
                    root_symbol = args[0] if len(args) > 0 else ''

                    if root_symbol:
                        root_symbol = root_symbol.upper()

                        if root_symbol in ['XBT', 'ETH']:
                            quote_symbol = 'USD'
                        else:
                            quote_symbol = 'XBT'

                        response = [res for res in response if
                                    res['quoteCurrency'] == quote_symbol and
                                    res['rootSymbol'] == root_symbol]
                    else:
                        underlying_symbols = ('XBT', 'ETH', 'XRPXBT',
                                              'EOSXBT', 'LTCXBT',
                                              'BCHXBT', 'ADAXBT',
                                              'TRXXBT')

                        response = [res for res in response if res['symbol'].endswith(underlying_symbols)]

                    if len(response) > 0:
                        message = ''
                        for res in response:
                            message += '{}:\n' \
                                       'Last Price: {}\n' \
                                       'Mark Price: {}\n\n'.format(res['symbol'],
                                                                   res['lastPrice'],
                                                                   res['markPrice'])
                    else:
                        message = 'No symbol found. Send 3 character root symbol'
                else:
                    message = 'No response from Api'

            except Exception as e:
                logger.error(str(e))
                message = str(e)

        bot.send_message(chat_id=update.message.chat_id, text=message)

    def unknown_command(self, bot, update):
        bot.send_message(chat_id=update.message.chat_id, text="Sorry, I didn't understand that command.")

    def unknown_text(self, bot, update):
        bot.send_message(chat_id=update.message.chat_id, text=update.message.text)
