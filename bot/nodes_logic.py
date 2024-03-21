# ruff: noqa: F403, F405, E402, E501, F401

from pydantic import BaseModel, ConfigDict
from rich import print
from rich.console import Console
from ccdexplorer_fundamentals.cis import (
    MongoTypeLoggedEvent,
    MongoTypeTokenAddress,
    burnEvent,
    mintEvent,
    transferEvent,
)
from ccdexplorer_fundamentals.enums import NET
from ccdexplorer_fundamentals.GRPCClient import GRPCClient
from ccdexplorer_fundamentals.GRPCClient.CCD_Types import *
from ccdexplorer_fundamentals.mongodb import (
    Collections,
    MongoDB,
    MongoMotor,
    MongoTypeInvolvedAccount,
    MongoTypeInvolvedContract,
)
from ccdexplorer_fundamentals.cis import MongoTypeTokensTag
from ccdexplorer_fundamentals.tooter import Tooter, TooterChannel, TooterType
from telegram import Update
from telegram.ext import ContextTypes

from env import *
from notification_classes import *
from ccdexplorer_fundamentals.user_v2 import (
    AccountForUser,
    NotificationPreferences,
    Reward,
    UserV2,
)
from ccdexplorer_fundamentals.node import ConcordiumNodeFromDashboard

console = Console()


class Mixin:
    def prepare_notification_event(
        self,
        event_type: EventType,
        tx_hash: str,
        block_info: CCD_BlockInfo,
        impacted_addresses: list[ImpactedAddress],
    ) -> NotificationEvent:
        return NotificationEvent(
            **{
                "event_type": event_type,
                "tx_hash": tx_hash,
                "block_height": block_info.height,
                "block_hash": block_info.hash,
                "block_slot_time": block_info.slot_time,
                "impacted_addresses": impacted_addresses,
            }
        )

    def add_notification_event_to_queue(self, notification_event: NotificationEvent):
        self.event_queue.append(notification_event)

    async def get_new_dashboard_nodes_from_mongo(
        self, context: ContextTypes.DEFAULT_TYPE
    ):
        try:
            net = NET(context.bot_data["net"]).value
            db_to_use = (
                self.connections.mongodb.mainnet
                if net == "mainnet"
                else self.connections.mongodb.testnet
            )

            result = db_to_use[Collections.blocks].aggregate(
                [{"$sort": {"height": -1}}, {"$limit": 1}]
            )

            if result:
                last_block_info = CCD_BlockInfo(**list(result)[0])

            heartbeat_last_timestamp_dashboard_nodes = db_to_use[
                Collections.helpers
            ].find_one({"_id": "heartbeat_last_timestamp_dashboard_nodes"})
            heartbeat_last_timestamp_dashboard_nodes: dt.datetime = (
                heartbeat_last_timestamp_dashboard_nodes["timestamp"].astimezone(
                    tz=dt.timezone.utc
                )
            )
            now = dt.datetime.now().astimezone(tz=dt.timezone.utc)

            if (now - heartbeat_last_timestamp_dashboard_nodes).seconds < (5 * 60):
                result = db_to_use[Collections.dashboard_nodes].find({})

                if result:
                    for raw_node in list(result):
                        node = ConcordiumNodeFromDashboard(**raw_node)
                        node_last_finalized_block_height = node.finalizedBlockHeight
                        heartbeat_last_finalized_block_height = last_block_info.height
                        if not node.consensusBakerId:
                            break

                        if (
                            heartbeat_last_finalized_block_height
                            - node_last_finalized_block_height
                            > 300
                        ):
                            notification_event = self.prepare_notification_event(
                                EventType(
                                    validator=EventTypeValidator(
                                        validator_running_behind=(
                                            heartbeat_last_finalized_block_height
                                            - node_last_finalized_block_height
                                        )
                                    )
                                ),
                                tx_hash=None,
                                block_info=None,
                                impacted_addresses=[
                                    ImpactedAddress(
                                        address=self.complete_address(
                                            node.consensusBakerId
                                        ),
                                        address_type=AddressType.validator,
                                    )
                                ],
                            )
                            self.add_notification_event_to_queue(notification_event)
        except Exception as e:
            console.log(e)
