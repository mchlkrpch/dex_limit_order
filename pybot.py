import os
import asyncio
from aiogram import Bot, Dispatcher, types, F
from aiogram.filters import Command
from web3 import Web3
from dotenv import load_dotenv

load_dotenv()

TOKEN = os.getenv("BOT_TOKEN")
RPC_URL = os.getenv("ALCHEMY_SEPOLIA_URL")
PRIVATE_KEY = os.getenv("PRIVATE_KEY")
CONTRACT_ADDRESS = os.getenv("CONTRACT_ADDRESS")
WETH_ADDRESS = "0x7b79995e5f793A07Bc00c21412e50Ecae098E7f9"
USDT_ADDRESS = "0xaA8E23Fb1079EA71e0a56F48a2aA51851D8433D0"

ABI = [
    {"inputs":[{"internalType":"address","name":"_tokenIn","type":"address"},{"internalType":"address","name":"_tokenOut","type":"address"},{"internalType":"uint256","name":"_amountIn","type":"uint256"},{"internalType":"uint256","name":"_targetPrice","type":"uint256"},{"internalType":"enum LimitOrderManager.OrderType","name":"_type","type":"uint8"}],"name":"createOrder","outputs":[],"stateMutability":"nonpayable","type":"function"},
    {"inputs":[],"name":"getLatestPrice","outputs":[{"internalType":"uint256","name":"","type":"uint256"}],"stateMutability":"view","type":"function"}
]

ERC20_ABI = [
    {"constant":True,"inputs":[{"name":"_owner","type":"address"},{"name":"_spender","type":"address"}],"name":"allowance","outputs":[{"name":"","type":"uint256"}],"type":"function"},
    {"constant":False,"inputs":[{"name":"_spender","type":"address"},{"name":"_value","type":"uint256"}],"name":"approve","outputs":[{"name":"","type":"bool"}],"type":"function"}
]

w3 = Web3(Web3.HTTPProvider(RPC_URL))
account = w3.eth.account.from_key(PRIVATE_KEY)
contract = w3.eth.contract(address=CONTRACT_ADDRESS, abi=ABI)
weth_token = w3.eth.contract(address=WETH_ADDRESS, abi=ERC20_ABI)

bot = Bot(token=TOKEN)
dp = Dispatcher()

@dp.message(Command("start"))
async def start(message: types.Message):
    await message.answer("Отправь: ETH 0.008\nПроверю Approve и создам ордер.")

@dp.message(F.text.regexp(r'^ETH\s(\d+\.?\d*)'))
async def create_order_handler(message: types.Message):
    try:
        amount_eth = float(message.text.split()[1])
        amount_wei = w3.to_wei(amount_eth, 'ether')
        status_msg = await message.answer("check (Approve)...")
        allowance = weth_token.functions.allowance(account.address, CONTRACT_ADDRESS).call()

        if allowance < amount_wei:
            await status_msg.edit_text("approve contract to use WETH...")
            approve_tx = weth_token.functions.approve(CONTRACT_ADDRESS, amount_wei * 10).build_transaction({
                'from': account.address,
                'nonce': w3.eth.get_transaction_count(account.address),
                'gas': 100000,
                'gasPrice': w3.eth.gas_price,
                'chainId': 11155111
            })
            signed_approve = w3.eth.account.sign_transaction(approve_tx, PRIVATE_KEY)
            tx_hash_app = w3.eth.send_raw_transaction(signed_approve.raw_transaction)
            w3.eth.wait_for_transaction_receipt(tx_hash_app)
            await status_msg.edit_text("got approved! creating order...")

        current_price = contract.functions.getLatestPrice().call()
        target_price = current_price - (50 * 10**8)

        tx = contract.functions.createOrder(
            WETH_ADDRESS,
            USDT_ADDRESS,
            amount_wei,
            target_price,
            0
        ).build_transaction({
            'from': account.address,
            'nonce': w3.eth.get_transaction_count(account.address),
            'gas': 350000,
            'gasPrice': w3.eth.gas_price,
            'chainId': 11155111
        })

        signed_tx = w3.eth.account.sign_transaction(tx, PRIVATE_KEY)
        tx_hash = w3.eth.send_raw_transaction(signed_tx.raw_transaction)
        await status_msg.edit_text(f"send. waiting block...")
        receipt = w3.eth.wait_for_transaction_receipt(tx_hash)
        if receipt['status'] == 1:
            await status_msg.edit_text(f"🚀 OK!\norder's block\nTX: {tx_hash.hex()}")
        else:
            await status_msg.edit_text("❌ Error. check if you're got WETH on yourbalance!")

    except Exception as e:
        await message.answer(f"Error:{str(e)}")


async def main():
    await dp.start_polling(bot)

if __name__ == "__main__":
    asyncio.run(main())