// @ts-ignore
import { ethers } from "hardhat";

async function main() {
    const CONTRACT_ADDRESS = process.env.CONTRACT_ADRESS;
    
    // Получаем экземпляр контракта
    const manager = await ethers.getContractAt("LimitOrderManager", CONTRACT_ADDRESS);

    console.log("--- БОТ ЗАПУЩЕН (Network: Sepolia) ---");
    console.log(`Мониторинг контракта: ${CONTRACT_ADDRESS}`);

    while (true) {
        try {
            const priceRaw = await manager.getLatestPrice();
            const price = Number(priceRaw) / 1e8;
            const now = new Date().toLocaleTimeString();
            console.log(`[${now}] Текущая цена ETH: $${price.toFixed(2)}`);
            const count = await manager.getOrdersCount();
            let activeOrdersFound = 0; // Добавляем счетчик активных

            for (let i = 0; i < Number(count); i++) {
                const order = await manager.orders(i);
                if (order.isActive) {
                    activeOrdersFound++; // Считаем только живые ордера
                    
                    const target = Number(order.targetPrice) / 1e8;
                    console.log(` > Ордер #${i}: Ждем цену ${order.orderType === 0n ? '>=' : '<='} $${target}`);
                    
                    if (order.orderType === 0n && priceRaw >= order.targetPrice) {
                        console.log(`!!! Условие ордера #${i} выполнено. Исполняю...`);
                        const tx = await manager.executeOrder(i);
                        await tx.wait();
                        console.log("Ордер успешно исполнен!");
                    }
                }
            }

            // Теперь проверяем наш локальный счетчик
            if (activeOrdersFound === 0) {
                console.log("На данный момент активных ордеров нет (все исполнены или еще не созданы).");
            }
        } catch (error) {
            console.error("Ошибка бота:", error);
        }

        await new Promise(r => setTimeout(r, 5000));
    }
}

main();