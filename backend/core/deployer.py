import json
from pathlib import Path
from web3 import Web3

RWA_COMPILED = (
    Path(__file__).parent.parent.parent.parent / "rwa_platform_py" / "compiled" / "RWAToken.json"
)


async def deploy_rwa_token(
    rpc_url: str,
    private_key: str,
    token_name: str,
    token_symbol: str,
    asset_name: str,
    asset_description: str,
    asset_location: str,
    asset_value_usd_cents: int,
    total_tokens: int,
    initial_mint_pct: int = 10,
    **_,
) -> dict:
    if not RWA_COMPILED.exists():
        raise FileNotFoundError(
            f"Compiled contract not found at {RWA_COMPILED}. "
            "Run `python scripts/compile.py` in the rwa_platform_py project first."
        )

    compiled = json.loads(RWA_COMPILED.read_text())
    w3 = Web3(Web3.HTTPProvider(rpc_url))
    if not w3.is_connected():
        raise ConnectionError(f"Cannot connect to Ethereum node at {rpc_url}")

    account = w3.eth.account.from_key(private_key)
    factory = w3.eth.contract(abi=compiled["abi"], bytecode=compiled["bytecode"])

    total_supply_wei = total_tokens * 10**18
    initial_mint_wei = int(total_supply_wei * initial_mint_pct / 100)

    deploy_tx = factory.constructor(
        token_name,
        token_symbol,
        asset_name,
        asset_description,
        asset_location,
        asset_value_usd_cents,
        total_supply_wei,
    ).build_transaction({
        "from": account.address,
        "nonce": w3.eth.get_transaction_count(account.address),
        "gas": 3_000_000,
        "gasPrice": w3.eth.gas_price,
    })

    signed = w3.eth.account.sign_transaction(deploy_tx, private_key)
    tx_hash = w3.eth.send_raw_transaction(signed.raw_transaction)
    receipt = w3.eth.wait_for_transaction_receipt(tx_hash)
    contract_address = receipt.contractAddress

    token = w3.eth.contract(address=contract_address, abi=compiled["abi"])
    mint_tx = token.functions.mint(account.address, initial_mint_wei).build_transaction({
        "from": account.address,
        "nonce": w3.eth.get_transaction_count(account.address),
        "gas": 200_000,
        "gasPrice": w3.eth.gas_price,
    })
    signed = w3.eth.account.sign_transaction(mint_tx, private_key)
    mint_hash = w3.eth.send_raw_transaction(signed.raw_transaction)
    w3.eth.wait_for_transaction_receipt(mint_hash)

    initial_minted = total_tokens * initial_mint_pct // 100

    return {
        "contract_address": contract_address,
        "deployer": account.address,
        "token_name": token_name,
        "token_symbol": token_symbol,
        "total_supply": total_tokens,
        "initial_minted": initial_minted,
        "deploy_tx": tx_hash.hex(),
    }
