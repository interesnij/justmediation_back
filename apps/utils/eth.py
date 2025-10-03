from django.conf import settings
from web3 import Web3

abi = '[{"inputs":[],"stateMutability":"nonpayable","type":"constructor"},{"inputs":[{"internalType":"uint256","name":"recordId","type":"uint256"}],"name":"getRecord","outputs":[{"components":[{"internalType":"string","name":"id","type":"string"},{"internalType":"enum RecordContract.RecordKind","name":"kind","type":"uint8"},{"internalType":"uint256","name":"signedAt","type":"uint256"}],"internalType":"struct RecordContract.Record","name":"record","type":"tuple"}],"stateMutability":"view","type":"function"},{"inputs":[],"name":"getRecords","outputs":[{"components":[{"internalType":"string","name":"id","type":"string"},{"internalType":"enum RecordContract.RecordKind","name":"kind","type":"uint8"},{"internalType":"uint256","name":"signedAt","type":"uint256"}],"internalType":"struct RecordContract.Record[]","name":"_records","type":"tuple[]"}],"stateMutability":"view","type":"function"},{"inputs":[],"name":"getRecordsSize","outputs":[{"internalType":"uint256","name":"","type":"uint256"}],"stateMutability":"view","type":"function"},{"inputs":[{"internalType":"string","name":"id","type":"string"},{"internalType":"enum RecordContract.RecordKind","name":"kind","type":"uint8"}],"name":"newRecord","outputs":[{"internalType":"uint256","name":"recordId","type":"uint256"}],"stateMutability":"nonpayable","type":"function"}]'  # noqa: E501


def create_new_record(md5, kind):
    #infura_url = 'https://{}.infura.io/v3/{}'.format(
    #    settings.ETH_NETWORK_NAME, settings.WEB3_INFURA_PROJECT_ID)
    infura_url = 'https://polygon-mainnet.infura.io/v3/ac4d6f8e04d14a829dbe4f3a010cb60c'
    w3 = Web3(Web3.HTTPProvider(infura_url))

    contract = w3.eth.contract(address=settings.ETH_CONTRACT_ADDRESS, abi=abi)

    account = w3.eth.account.from_key(settings.ETH_PRIVATE_KEY)

    transaction = contract.functions.newRecord(
        str(md5), int(kind)
    ).buildTransaction({
        'from': account.address,
        'nonce': w3.eth.getTransactionCount(account.address)
    })

    signed_transaction = w3.eth.account.signTransaction(
        transaction, private_key=settings.ETH_PRIVATE_KEY)

    w3.eth.send_raw_transaction(signed_transaction.rawTransaction)

    return signed_transaction.hash.hex()
