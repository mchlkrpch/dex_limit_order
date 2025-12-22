// @ts-ignore
import { ethers } from "hardhat";

const GEQ = 0;
const LEQ = 1;

// Sepolia WETH, USDC/USDT
const WETH_ADDRESS = "0x7b79995e5f793A07Bc00c21412e50Ecae098E7f9";
const USDT_ADDRESS = "0x1c7D4B196Cb0C7B01d743Fbc6116a902379C7238";

async function main() {
    const CONTRACT_ADDRESS = process.env.CONTRACT_ADDRESS;

    const [deployer] = await ethers.getSigners();
    const manager = await ethers.getContractAt("LimitOrderManager", CONTRACT_ADDRESS);
    const weth = await ethers.getContractAt("IERC20", WETH_ADDRESS);

    console.log("1) get WETH...");
    const amount = ethers.parseEther("0.008");
    const depositTx = await deployer.sendTransaction({
        to: WETH_ADDRESS,
        value: amount
    });
    await depositTx.wait();

    console.log("2) Approve...");
    // give approve from user's side that contract can
    // take money from his wallet
    await (await weth.approve(CONTRACT_ADDRESS, amount)).wait();

    const currentPrice = await manager.getLatestPrice();
    console.log(`3) get cur price in Chainlink: $${Number(currentPrice) / 1e8}`);

    const instantTargetPrice = currentPrice - (100n * 100000000n); 

    console.log(`order with price: $${Number(instantTargetPrice) / 1e8}`);

    const orderTx = await manager.createOrder(
        WETH_ADDRESS,
        USDT_ADDRESS,
        amount,
        instantTargetPrice,
        GEQ,
    );
    await orderTx.wait();
    console.log("Ордер создан! Теперь запускай бота.");
}

main().catch(console.error);