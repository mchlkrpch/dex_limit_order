// @ts-ignore
import { ethers } from "hardhat";

async function main() {
  const UNISWAP_ROUTER = "0xC532a74256D3Db42D0Bf7a0400fEFDbad7694008";
  const CHAINLINK_FEED = "0x694AA1769357215DE4FAC081bf1f309aDC325306";

  const Manager = await ethers.getContractFactory("LimitOrderManager");
  const manager = await Manager.deploy(UNISWAP_ROUTER, CHAINLINK_FEED);
  await manager.waitForDeployment();

  console.log(`Contract deployed to: ${await manager.getAddress()}`);
}
main().catch(console.error);