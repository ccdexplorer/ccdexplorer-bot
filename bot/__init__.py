# ruff: noqa: F403, F405, E402, E501, F401

from pydantic import BaseModel, ConfigDict
from ccdexplorer_fundamentals.tooter import Tooter, TooterChannel, TooterType
from ccdexplorer_fundamentals.enums import NET
from ccdexplorer_fundamentals.GRPCClient import GRPCClient
from ccdexplorer_fundamentals.GRPCClient.CCD_Types import *
from ccdexplorer_fundamentals.cis import MongoTypeLoggedEvent
from ccdexplorer_fundamentals.user_v2 import (
    UserV2,
    NotificationPreferences,
    AccountForUser,
    ContractForUser,
)
from notification_classes import *

from env import *
from ccdexplorer_fundamentals.mongodb import (
    Collections,
    CollectionsUtilities,
    MongoLabeledAccount,
    MongoTypePayday,
)
from telegram import Update
from telegram.ext import ContextTypes
from rich.console import Console
from rich import print
from .telegram_logic import Mixin as _telegram_logic
from .messages_logic import Mixin as _messages_logic
from .blocks_logic import Mixin as _blocks_logic
from .nodes_logic import Mixin as _nodes_logic

# from .messages_definitions import Mixin as _messages_definitions
from ccdexplorer_fundamentals.cis import MongoTypeTokensTag

console = Console()

import sys


class Bot(_telegram_logic, _messages_logic, _blocks_logic, _nodes_logic):
    def read_contracts_with_tag_info(self):
        contracts_with_tag_info = {}
        token_tags = self.connections.mongodb.mainnet[Collections.tokens_tags].find({})
        for token_tag in token_tags:
            for contract in token_tag["contracts"]:
                contracts_with_tag_info[contract] = MongoTypeTokensTag(**token_tag)
        self.contracts_with_tag_info = contracts_with_tag_info

    def read_nightly_accounts(self) -> dict[str:UserV2]:
        result = self.connections.mongodb.mainnet[Collections.nightly_accounts].find({})
        self.nightly_accounts_by_account_id = {x["_id"]: x for x in list(result)}
        self.nightly_accounts_by_account_index = {x["index"]: x for x in list(result)}

    def read_payday_last_blocks_validated(self) -> dict[str:UserV2]:
        pp = [{"$sort": {"date": -1}}, {"$limit": 1}]

        result = list(
            MongoTypePayday(**x)
            for x in self.connections.mongodb.mainnet[Collections.paydays].aggregate(pp)
        )[0]

        self.payday_last_blocks_validated = (
            result.height_for_last_block - result.height_for_first_block + 1
        )

    def read_users_from_collection(self):
        if "pytest" in sys.modules:
            result = self.connections.mongodb.utilities[
                CollectionsUtilities.users_v2_dev
            ].find({})
        else:
            result = self.connections.mongodb.utilities[
                CollectionsUtilities.users_v2_prod
            ].find({})
        self.users = {x["_id"]: UserV2(**x) for x in list(result)}
        for chat_id, user in self.users.items():
            for account_index, user_account in user.accounts.items():
                self.users[chat_id].accounts[account_index] = AccountForUser(
                    **user_account
                )
            for contract_index, contract in user.contracts.items():
                self.users[chat_id].contracts[contract_index] = ContractForUser(
                    **contract
                )

        # print("Users refreshed from collection.")

    def read_labeled_accounts(self):
        self.labeled_accounts: dict[CCD_AccountIndex:MongoLabeledAccount] = {
            x["account_index"]: MongoLabeledAccount(**x)
            for x in self.connections.mongodb.utilities[
                CollectionsUtilities.labeled_accounts
            ].find({"account_index": {"$exists": True}})
        }

    def do_initial_reads_from_collections(self):
        self.read_users_from_collection()
        self.read_labeled_accounts()
        self.read_contracts_with_tag_info()
        self.read_nightly_accounts()
        self.read_payday_last_blocks_validated()

    async def async_read_labeled_accounts(
        self, context: ContextTypes.DEFAULT_TYPE
    ) -> dict[str:UserV2]:
        self.read_labeled_accounts()

    async def async_read_users_from_collection(
        self, context: ContextTypes.DEFAULT_TYPE
    ) -> dict[str:UserV2]:
        self.read_users_from_collection()

    async def async_read_nightly_accounts(
        self, context: ContextTypes.DEFAULT_TYPE
    ) -> dict[str:UserV2]:
        self.read_nightly_accounts()

    async def async_read_payday_last_blocks_validated(
        self, context: ContextTypes.DEFAULT_TYPE
    ) -> dict[str:UserV2]:
        self.read_payday_last_blocks_validated()

    async def async_read_contracts_with_tag_info(
        self, context: ContextTypes.DEFAULT_TYPE
    ) -> dict[str:UserV2]:
        self.read_contracts_with_tag_info()

    def __init__(self, connections: Connections):
        self.connections = connections
        self.users = {}
        self.processing = False
        self.full_blocks_to_process: list[CCD_BlockComplete] = []
        self.event_queue: list[NotificationEvent] = []
        self.read_nightly_accounts()
        self.read_payday_last_blocks_validated()
        self.labeled_accounts: dict[CCD_AccountIndex:MongoLabeledAccount] = {
            x["account_index"]: MongoLabeledAccount(**x)
            for x in self.connections.mongodb.utilities[
                CollectionsUtilities.labeled_accounts
            ].find({"account_index": {"$exists": True}})
        }
        self.internal_freqency_timer = dt.datetime.now().astimezone(tz=dt.timezone.utc)
