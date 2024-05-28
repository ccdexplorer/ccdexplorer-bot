# ruff: noqa: F403, F405, E402, E501, F401

# from unittest.mock import Mock
import os

import pytest
from rich import print
from ccdexplorer_fundamentals.cis import MongoTypeLoggedEvent, MongoTypeTokensTag
from ccdexplorer_fundamentals.enums import NET
from ccdexplorer_fundamentals.GRPCClient import GRPCClient
from ccdexplorer_fundamentals.GRPCClient.CCD_Types import *
from ccdexplorer_fundamentals.GRPCClient.CCD_Types import CCD_BlockComplete
from ccdexplorer_fundamentals.mongodb import (
    Collections,
    MongoDB,
    MongoTypeInvolvedAccount,
    MongoTypeInvolvedContract,
)
from ccdexplorer_fundamentals.tooter import Tooter

from bot import Bot, Connections

from notification_classes import *
from ccdexplorer_fundamentals.user_v2 import (
    AccountForUser,
    AccountNotificationPreferences,
    NotificationPreferences,
    NotificationService,
    NotificationServices,
    OtherNotificationPreferences,
    UserV2,
    ValidatorNotificationPreferences,
)


@pytest.fixture
def grpcclient():
    return GRPCClient()


@pytest.fixture
def mongodb():
    tooter = Tooter()
    mongodb = MongoDB(tooter)
    return mongodb


@pytest.fixture
def bot(grpcclient: GRPCClient, mongodb: MongoDB):
    grpcclient = GRPCClient()
    tooter = Tooter()
    bot = Bot(
        Connections(
            tooter=tooter, mongodb=mongodb, mongomoter=None, grpcclient=grpcclient
        )
    )
    bot.do_initial_reads_from_collections()
    return bot


def read_block_information_v3(
    block_height,
    tx_index: int,
    grpcclient: GRPCClient,
    mongodb: MongoDB,
    net: str = "mainnet",
):
    db_to_use = mongodb.mainnet if net == "mainnet" else mongodb.testnet
    block_info = grpcclient.get_finalized_block_at_height(block_height, NET(net))
    transaction_summaries = grpcclient.get_block_transaction_events(
        block_info.hash, NET(net)
    ).transaction_summaries
    if len(transaction_summaries) > 0:
        transaction_summaries = [transaction_summaries[tx_index]]
    special_events = grpcclient.get_block_special_events(block_info.hash, NET(net))

    result = db_to_use[Collections.tokens_logged_events].find(
        {"block_height": block_height}
    )

    ### Logged Events
    if result:
        logged_events_in_block = [MongoTypeLoggedEvent(**x) for x in result]
    else:
        logged_events_in_block = []

    ### Special Events
    special_events = grpcclient.get_block_special_events(block_info.hash, NET(net))

    block_complete = CCD_BlockComplete(
        **{
            "block_info": block_info,
            "transaction_summaries": transaction_summaries,
            "special_events": special_events,
            "logged_events": logged_events_in_block,
            "net": net,
        }
    )

    return block_complete


###################################
# TESTS
###################################

# Set this to have messages actually be sent
SEND_MESSAGES = True


@pytest.mark.asyncio
async def test_contract_update_issued(
    bot: Bot, grpcclient: GRPCClient, mongodb: MongoDB
):
    """ """

    block = read_block_information_v3(9289847, 0, grpcclient, mongodb)
    await bot.find_events_in_block_transactions(block)
    (
        message_response,
        notification_services_to_send,
    ) = await bot.determine_if_user_should_be_notified_of_event(
        bot.users["user_for_test"], bot.event_queue[0]
    )

    assert bot.event_queue[0].event_type.contract is not None
    assert message_response is not None
    assert notification_services_to_send[NotificationServices.telegram] is True

    print(message_response)
    print(notification_services_to_send)
    if SEND_MESSAGES:
        await bot.send_notification_queue()


@pytest.mark.asyncio
async def test_contract_update_issued_mint_domain(
    bot: Bot, grpcclient: GRPCClient, mongodb: MongoDB
):
    """ """

    block = read_block_information_v3(9985999, 5, grpcclient, mongodb)
    await bot.find_events_in_block_transactions(block)
    (
        message_response,
        notification_services_to_send,
    ) = await bot.determine_if_user_should_be_notified_of_event(
        bot.users["user_for_test"], bot.event_queue[0]
    )

    assert bot.event_queue[0].event_type.contract is not None
    assert message_response is not None
    assert notification_services_to_send[NotificationServices.telegram] is True

    print(message_response)
    print(notification_services_to_send)
    if SEND_MESSAGES:
        await bot.send_notification_queue()
