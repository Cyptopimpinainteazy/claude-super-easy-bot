"""
FLASH LOAN EXECUTOR
===================
Handles flash loan execution and smart contract interactions for arbitrage
"""

from web3 import Web3
from eth_account import Account
from decimal import Decimal
from typing import Optional, Dict, List
import json

# ============================================================================
# AAVE V3 FLASH LOAN CONTRACT ABI (Simplified)
# ============================================================================

AAVE_POOL_ABI = json.loads('''[
    {
        "inputs": [
            {"internalType": "address", "name": "receiverAddress", "type": "address"},
            {"internalType": "address[]", "name": "assets", "type": "address[]"},
            {"internalType": "uint256[]", "name": "amounts", "type": "uint256[]"},
            {"internalType": "uint256[]", "name": "modes", "type": "uint256[]"},
            {"internalType": "address", "name": "onBehalfOf", "type": "address"},
            {"internalType": "bytes", "name": "params", "type": "bytes"},
            {"internalType": "uint16", "name": "referralCode", "type": "uint16"}
        ],
        "name": "flashLoan",
        "outputs": [],
        "stateMutability": "nonpayable",
        "type": "function"
    },
    {
        "inputs": [],
        "name": "getPool",
        "outputs": [{"internalType": "address", "name": "", "type": "address"}],
        "stateMutability": "view",
        "type": "function"
    }
]''')

# ERC20 Token ABI (minimal)
ERC20_ABI = json.loads('''[
    {
        "constant": true,
        "inputs": [{"name": "_owner", "type": "address"}],
        "name": "balanceOf",
        "outputs": [{"name": "balance", "type": "uint256"}],
        "type": "function"
    },
    {
        "constant": false,
        "inputs": [
            {"name": "_spender", "type": "address"},
            {"name": "_value", "type": "uint256"}
        ],
        "name": "approve",
        "outputs": [{"name": "", "type": "bool"}],
        "type": "function"
    },
    {
        "constant": true,
        "inputs": [],
        "name": "decimals",
        "outputs": [{"name": "", "type": "uint8"}],
        "type": "function"
    }
]''')

# Uniswap V2 Router ABI (minimal)
UNISWAP_V2_ROUTER_ABI = json.loads('''[
    {
        "inputs": [
            {"internalType": "uint256", "name": "amountIn", "type": "uint256"},
            {"internalType": "uint256", "name": "amountOutMin", "type": "uint256"},
            {"internalType": "address[]", "name": "path", "type": "address[]"},
            {"internalType": "address", "name": "to", "type": "address"},
            {"internalType": "uint256", "name": "deadline", "type": "uint256"}
        ],
        "name": "swapExactTokensForTokens",
        "outputs": [{"internalType": "uint256[]", "name": "amounts", "type": "uint256[]"}],
        "stateMutability": "nonpayable",
        "type": "function"
    },
    {
        "inputs": [
            {"internalType": "uint256", "name": "amountIn", "type": "uint256"},
            {"internalType": "address[]", "name": "path", "type": "address[]"}
        ],
        "name": "getAmountsOut",
        "outputs": [{"internalType": "uint256[]", "name": "amounts", "type": "uint256[]"}],
        "stateMutability": "view",
        "type": "function"
    }
]''')

# ============================================================================
# FLASH LOAN EXECUTOR
# ============================================================================

class FlashLoanExecutor:
    """Executes flash loan arbitrage transactions"""
    
    def __init__(self, w3: Web3, private_key: str, chain_config: Dict):
        self.w3 = w3
        self.account = Account.from_key(private_key)
        self.chain_config = chain_config
        
        # Initialize contracts
        pool_provider_address = chain_config['aave_pool_provider']
        self.pool_provider = self.w3.eth.contract(
            address=Web3.to_checksum_address(pool_provider_address),
            abi=AAVE_POOL_ABI
        )
        
        # Get actual pool address
        self.pool_address = self.pool_provider.functions.getPool().call()
        self.pool = self.w3.eth.contract(
            address=self.pool_address,
            abi=AAVE_POOL_ABI
        )
    
    def get_token_contract(self, token_address: str):
        """Get ERC20 token contract instance"""
        return self.w3.eth.contract(
            address=Web3.to_checksum_address(token_address),
            abi=ERC20_ABI
        )
    
    def get_router_contract(self, router_address: str):
        """Get DEX router contract instance"""
        return self.w3.eth.contract(
            address=Web3.to_checksum_address(router_address),
            abi=UNISWAP_V2_ROUTER_ABI
        )
    
    async def check_token_balance(self, token_address: str) -> Decimal:
        """Check token balance of account"""
        token = self.get_token_contract(token_address)
        balance = token.functions.balanceOf(self.account.address).call()
        decimals = token.functions.decimals().call()
        return Decimal(str(balance)) / Decimal(str(10 ** decimals))
    
    async def approve_token(self, token_address: str, spender: str, amount: int):
        """Approve token spending"""
        token = self.get_token_contract(token_address)
        
        tx = token.functions.approve(
            Web3.to_checksum_address(spender),
            amount
        ).build_transaction({
            'from': self.account.address,
            'gas': 100000,
            'gasPrice': self.w3.eth.gas_price,
            'nonce': self.w3.eth.get_transaction_count(self.account.address),
        })
        
        signed_tx = self.account.sign_transaction(tx)
        tx_hash = self.w3.eth.send_raw_transaction(signed_tx.rawTransaction)
        
        print(f"Approval tx: {tx_hash.hex()}")
        receipt = self.w3.eth.wait_for_transaction_receipt(tx_hash)
        return receipt
    
    async def get_swap_quote(self, router_address: str, amount_in: int, 
                           path: List[str]) -> int:
        """Get quote for a swap"""
        router = self.get_router_contract(router_address)
        
        amounts = router.functions.getAmountsOut(
            amount_in,
            [Web3.to_checksum_address(addr) for addr in path]
        ).call()
        
        return amounts[-1]
    
    async def execute_swap(self, router_address: str, amount_in: int,
                         min_amount_out: int, path: List[str],
                         deadline: int) -> Dict:
        """Execute a token swap"""
        router = self.get_router_contract(router_address)
        
        tx = router.functions.swapExactTokensForTokens(
            amount_in,
            min_amount_out,
            [Web3.to_checksum_address(addr) for addr in path],
            self.account.address,
            deadline
        ).build_transaction({
            'from': self.account.address,
            'gas': 300000,
            'gasPrice': self.w3.eth.gas_price,
            'nonce': self.w3.eth.get_transaction_count(self.account.address),
        })
        
        signed_tx = self.account.sign_transaction(tx)
        tx_hash = self.w3.eth.send_raw_transaction(signed_tx.rawTransaction)
        
        print(f"Swap tx: {tx_hash.hex()}")
        receipt = self.w3.eth.wait_for_transaction_receipt(tx_hash)
        
        return {
            'hash': tx_hash.hex(),
            'status': receipt['status'],
            'gas_used': receipt['gasUsed']
        }
    
    async def execute_flash_loan_arbitrage(self, 
                                          token_address: str,
                                          loan_amount: int,
                                          buy_router: str,
                                          sell_router: str,
                                          intermediate_token: str) -> Dict:
        """
        Execute flash loan arbitrage
        
        Flow:
        1. Take flash loan of token_address
        2. Swap on buy_router to intermediate_token
        3. Swap back on sell_router to token_address
        4. Repay flash loan + fee
        5. Keep profit
        """
        
        print(f"\n{'='*60}")
        print(f"🚀 EXECUTING FLASH LOAN ARBITRAGE")
        print(f"{'='*60}")
        print(f"Loan Token: {token_address}")
        print(f"Loan Amount: {loan_amount}")
        print(f"Buy Router: {buy_router}")
        print(f"Sell Router: {sell_router}")
        
        try:
            # Step 1: Prepare flash loan parameters
            assets = [Web3.to_checksum_address(token_address)]
            amounts = [loan_amount]
            modes = [0]  # 0 = no debt, pay back in this transaction
            
            # Encode arbitrage parameters
            params = self.w3.codec.encode(
                ['address', 'address', 'address'],
                [buy_router, sell_router, intermediate_token]
            )
            
            # Step 2: Execute flash loan
            # NOTE: This requires a deployed arbitrage contract that implements
            # executeOperation() callback. The contract should:
            # - Receive the flash loan
            # - Execute the swaps
            # - Repay the loan
            # - Send profit back to your wallet
            
            # For this example, we're showing the structure
            # In production, you need to deploy your own arbitrage contract
            
            print("\n⚠️  NOTE: This requires a deployed arbitrage contract!")
            print("The contract must implement IFlashLoanSimpleReceiver interface")
            
            # Mock execution for demonstration
            return {
                'success': False,
                'message': 'Requires deployed arbitrage contract',
                'estimated_profit': 0,
                'gas_cost': 0
            }
            
        except Exception as e:
            print(f"❌ Flash loan execution failed: {e}")
            return {
                'success': False,
                'error': str(e)
            }

# ============================================================================
# SIMPLE ARBITRAGE EXECUTOR (WITHOUT FLASH LOANS)
# ============================================================================

class SimpleArbitrageExecutor:
    """Execute arbitrage with owned capital (no flash loans)"""
    
    def __init__(self, w3: Web3, private_key: str):
        self.w3 = w3
        self.account = Account.from_key(private_key)
        self.flash_executor = FlashLoanExecutor(w3, private_key, {})
    
    async def execute_arbitrage(self,
                               token_in_address: str,
                               token_out_address: str,
                               amount: int,
                               buy_router: str,
                               sell_router: str,
                               min_profit: Decimal) -> Dict:
        """
        Execute simple two-leg arbitrage
        
        Steps:
        1. Check we have enough token_in
        2. Approve buy_router to spend token_in
        3. Swap token_in -> token_out on buy_router
        4. Approve sell_router to spend token_out
        5. Swap token_out -> token_in on sell_router
        6. Calculate profit
        """
        
        print(f"\n{'='*60}")
        print(f"⚡ EXECUTING SIMPLE ARBITRAGE")
        print(f"{'='*60}")
        
        try:
            # Check balance
            balance = await self.flash_executor.check_token_balance(token_in_address)
            print(f"Balance: {balance}")
            
            if balance < Decimal(str(amount)) / Decimal('1e18'):
                return {
                    'success': False,
                    'error': 'Insufficient balance'
                }
            
            # Get current timestamp + 20 minutes for deadline
            deadline = self.w3.eth.get_block('latest')['timestamp'] + 1200
            
            # Step 1: Get quote for first swap
            path1 = [token_in_address, token_out_address]
            amount_out_1 = await self.flash_executor.get_swap_quote(
                buy_router, amount, path1
            )
            print(f"First swap quote: {amount_out_1}")
            
            # Step 2: Get quote for second swap
            path2 = [token_out_address, token_in_address]
            amount_out_2 = await self.flash_executor.get_swap_quote(
                sell_router, amount_out_1, path2
            )
            print(f"Second swap quote: {amount_out_2}")
            
            # Calculate profit
            profit = amount_out_2 - amount
            profit_decimal = Decimal(str(profit)) / Decimal('1e18')
            
            print(f"Expected profit: {profit_decimal}")
            
            if profit_decimal < min_profit:
                return {
                    'success': False,
                    'error': f'Profit too low: {profit_decimal} < {min_profit}'
                }
            
            # Step 3: Approve first router
            print("\n📝 Approving first router...")
            await self.flash_executor.approve_token(
                token_in_address, buy_router, amount
            )
            
            # Step 4: Execute first swap
            print("\n💱 Executing first swap...")
            result1 = await self.flash_executor.execute_swap(
                buy_router, amount, int(amount_out_1 * 0.99), path1, deadline
            )
            
            if result1['status'] != 1:
                return {
                    'success': False,
                    'error': 'First swap failed'
                }
            
            # Step 5: Approve second router
            print("\n📝 Approving second router...")
            await self.flash_executor.approve_token(
                token_out_address, sell_router, amount_out_1
            )
            
            # Step 6: Execute second swap
            print("\n💱 Executing second swap...")
            result2 = await self.flash_executor.execute_swap(
                sell_router, amount_out_1, int(amount_out_2 * 0.99), path2, deadline
            )
            
            if result2['status'] != 1:
                return {
                    'success': False,
                    'error': 'Second swap failed'
                }
            
            # Calculate actual profit
            final_balance = await self.flash_executor.check_token_balance(token_in_address)
            actual_profit = final_balance - balance
            
            print(f"\n{'='*60}")
            print(f"✅ ARBITRAGE SUCCESSFUL!")
            print(f"{'='*60}")
            print(f"Profit: {actual_profit}")
            print(f"Gas used: {result1['gas_used'] + result2['gas_used']}")
            
            return {
                'success': True,
                'profit': float(actual_profit),
                'gas_used': result1['gas_used'] + result2['gas_used'],
                'tx_hashes': [result1['hash'], result2['hash']]
            }
            
        except Exception as e:
            print(f"❌ Arbitrage execution failed: {e}")
            return {
                'success': False,
                'error': str(e)
            }

# ============================================================================
# EXAMPLE USAGE
# ============================================================================

async def example_execute_arbitrage():
    """Example of how to execute an arbitrage"""
    
    # Configuration
    RPC_URL = "https://eth-mainnet.g.alchemy.com/v2/YOUR_API_KEY"
    PRIVATE_KEY = "your_private_key_here"  # NEVER commit this!
    
    # Token addresses (Ethereum mainnet)
    WETH = "0xC02aaA39b223FE8D0A0e5C4F27eAD9083C756Cc2"
    USDC = "0xA0b86991c6218b36c1d19D4a2e9Eb0cE3606eB48"
    
    # Router addresses
    UNISWAP_V2_ROUTER = "0x7a250d5630b4cf539739df2c5dacb4c659f2488d"
    SUSHISWAP_ROUTER = "0xd9e1cE17f2641f24aE83637ab66a2cca9C378B9F"
    
    # Initialize
    w3 = Web3(Web3.HTTPProvider(RPC_URL))
    executor = SimpleArbitrageExecutor(w3, PRIVATE_KEY)
    
    # Execute arbitrage
    # Buy 0.1 ETH worth on Uniswap, sell on Sushiswap
    amount = int(0.1 * 1e18)  # 0.1 WETH
    
    result = await executor.execute_arbitrage(
        token_in_address=WETH,
        token_out_address=USDC,
        amount=amount,
        buy_router=UNISWAP_V2_ROUTER,
        sell_router=SUSHISWAP_ROUTER,
        min_profit=Decimal('10')  # Minimum $10 profit
    )
    
    print(f"\nResult: {result}")

if __name__ == "__main__":
    import asyncio
    
    print("""
    ⚠️  WARNING ⚠️
    
    This is example code for educational purposes.
    
    Before running in production:
    1. Never commit private keys to version control
    2. Use environment variables for sensitive data
    3. Test on testnets first (Goerli, Mumbai, etc.)
    4. Implement proper error handling
    5. Add transaction monitoring and retry logic
    6. Consider MEV protection (Flashbots, etc.)
    7. Deploy and verify your own arbitrage contract for flash loans
    8. Implement slippage protection
    9. Add monitoring and alerting
    10. Understand the risks and start with small amounts
    """)
    
    # Uncomment to run:
    # asyncio.run(example_execute_arbitrage())
