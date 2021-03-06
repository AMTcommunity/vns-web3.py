import pytest
import time
import warnings

from vns_web3.providers.eth_tester import (
    EthereumTesterProvider,
)
from vns_web3.utils.threads import (
    Timeout,
)
from vns_web3.main import Web3


class PollDelayCounter:
    def __init__(self, initial_delay=0, max_delay=1, initial_step=0.01):
        self.initial_delay = initial_delay
        self.initial_step = initial_step
        self.max_delay = max_delay
        self.current_delay = initial_delay

    def __call__(self):
        delay = self.current_delay

        if self.current_delay == 0:
            self.current_delay += self.initial_step
        else:
            self.current_delay *= 2
            self.current_delay = min(self.current_delay, self.max_delay)

        return delay

    def reset(self):
        self.current_delay = self.initial_delay


@pytest.fixture()
def sleep_interval():
    return PollDelayCounter()


def is_all_testrpc_providers(providers):
    return all(
        isinstance(provider, EthereumTesterProvider)
        for provider
        in providers
    )


@pytest.fixture()
def skip_if_testrpc():

    def _skip_if_testrpc(vns_web3):
        if is_all_testrpc_providers(vns_web3.providers):
            pytest.skip()
    return _skip_if_testrpc


@pytest.fixture()
def wait_for_miner_start():
    def _wait_for_miner_start(vns_web3, timeout=60):
        poll_delay_counter = PollDelayCounter()
        with Timeout(timeout) as timeout:
            while not vns_web3.eth.mining or not vns_web3.eth.hashrate:
                time.sleep(poll_delay_counter())
                timeout.check()
    return _wait_for_miner_start


@pytest.fixture()
def wait_for_block():
    def _wait_for_block(vns_web3, block_number=1, timeout=None):
        if not timeout:
            timeout = (block_number - vns_web3.eth.blockNumber) * 3
        poll_delay_counter = PollDelayCounter()
        with Timeout(timeout) as timeout:
            while True:
                if vns_web3.eth.blockNumber >= block_number:
                    break
                vns_web3.manager.request_blocking("evm_mine", [])
                timeout.sleep(poll_delay_counter())
    return _wait_for_block


@pytest.fixture()
def wait_for_transaction():
    def _wait_for_transaction(vns_web3, txn_hash, timeout=120):
        poll_delay_counter = PollDelayCounter()
        with Timeout(timeout) as timeout:
            while True:
                txn_receipt = vns_web3.eth.getTransactionReceipt(txn_hash)
                if txn_receipt is not None:
                    break
                time.sleep(poll_delay_counter())
                timeout.check()

        return txn_receipt
    return _wait_for_transaction


@pytest.fixture()
def vns_web3():
    provider = EthereumTesterProvider()
    return Web3(provider)


@pytest.fixture(autouse=True)
def print_warnings():
    warnings.simplefilter('always')
