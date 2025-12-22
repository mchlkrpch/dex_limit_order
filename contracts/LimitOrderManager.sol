// SPDX-License-Identifier: MIT
pragma solidity ^0.8.20;

import "@openzeppelin/contracts/token/ERC20/IERC20.sol";
import "@chainlink/contracts/src/v0.8/shared/interfaces/AggregatorV3Interface.sol";

interface IUniswapV2Router {
    function swapExactTokensForTokens(
        uint amountIn,
        uint amountOutMin,
        address[] calldata path,
        address to,
        uint deadline
    ) external returns (uint[] memory amounts);
}

contract LimitOrderManager {
    enum OrderType { TAKE_PROFIT, STOP_LOSS }

    struct Order {
        address creator;
        address tokenIn;
        address tokenOut;
        uint256 amountIn;
        uint256 targetPrice;
        OrderType orderType;
        bool isActive;
    }

    IUniswapV2Router public immutable uniswapRouter;
    AggregatorV3Interface public immutable priceFeed;
    
    Order[] public orders;

    constructor(address _router, address _priceFeed) {
        uniswapRouter = IUniswapV2Router(_router);
        priceFeed = AggregatorV3Interface(_priceFeed);
    }

    function createOrder(
        address _tokenIn,
        address _tokenOut,
        uint256 _amountIn,
        uint256 _targetPrice,
        OrderType _type
    ) external {
        // Пользователь должен заранее сделать approve этому контракту
        IERC20(_tokenIn).transferFrom(msg.sender, address(this), _amountIn);
        
        orders.push(Order({
            creator: msg.sender,
            tokenIn: _tokenIn,
            tokenOut: _tokenOut,
            amountIn: _amountIn,
            targetPrice: _targetPrice,
            orderType: _type,
            isActive: true
        }));
    }

    function getLatestPrice() public view returns (uint256) {
        (, int price, , , ) = priceFeed.latestRoundData();
        return uint256(price);
    }

    function executeOrder(uint256 _orderId) external {
        Order storage order = orders[_orderId];
        require(order.isActive, "Order not active");

        uint256 currentPrice = getLatestPrice();
        bool conditionMet = false;

        if (order.orderType == OrderType.TAKE_PROFIT) {
            conditionMet = currentPrice >= order.targetPrice;
        } else {
            conditionMet = currentPrice <= order.targetPrice;
        }

        require(conditionMet, "Price condition not met");
        order.isActive = false;

        IERC20(order.tokenIn).approve(address(uniswapRouter), order.amountIn);

        address[] memory path = new address[](2);
        path[0] = order.tokenIn;
        path[1] = order.tokenOut;

        uniswapRouter.swapExactTokensForTokens(
            order.amountIn,
            0,
            path,
            order.creator,
            block.timestamp + 15 minutes
        );
    }

    function getOrdersCount() public view returns (uint256) {
        return orders.length;
    }
}