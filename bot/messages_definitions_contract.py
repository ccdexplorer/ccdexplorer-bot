# ruff: noqa: F403, F405, E402, E501, F401

import math
from typing import TYPE_CHECKING

from pydantic import BaseModel, ConfigDict
from rich import print
from rich.console import Console
from ccdexplorer_fundamentals.cis import MongoTypeLoggedEvent, MongoTypeTokensTag
from ccdexplorer_fundamentals.enums import NET
from ccdexplorer_fundamentals.GRPCClient import GRPCClient
from ccdexplorer_fundamentals.GRPCClient.CCD_Types import *
from ccdexplorer_fundamentals.mongodb import (
    Collections,
    MongoDB,
    MongoLabeledAccount,
    MongoMotor,
    MongoTypeInvolvedAccount,
    MongoTypeInvolvedContract,
)
from ccdexplorer_fundamentals.tooter import Tooter, TooterChannel, TooterType
from telegram import Update
from telegram.ext import ContextTypes

from env import *
from notification_classes import *
from ccdexplorer_fundamentals.user_v2 import (
    AccountForUser,
    NotificationPreferences,
    NotificationServices,
    UserV2,
)

from .utils import Utils as Utils

if TYPE_CHECKING:
    from bot import Bot

console = Console()


class MessageContract(Utils):
    def define_contract_update_issued_message(
        self,
        event_type: EventTypeValidator | EventTypeAccount,
        notification_event: NotificationEvent,
        user: UserV2,
    ) -> MessageResponse:
        notification_event = self.add_labels_to_notitication_event(
            user, notification_event
        )
        receive_name = notification_event.event_type.contract.receive_name
        contract_address: ImpactedAddress = self.return_specific_address_type(
            notification_event.impacted_addresses, AddressType.contract
        )
        contract_with_info: MongoTypeTokensTag | None = (
            self.contracts_with_tag_info.get(contract_address.address.contract.to_str())
        )
        module_name = (
            (
                contract_with_info.display_name
                if contract_with_info.display_name
                else contract_address.label
            )
            if contract_with_info
            else contract_address.label
        )
        message = f'On smart contract <a href="https://ccdexplorer.io/mainnet/instance/{contract_address.address.contract.index}/{contract_address.address.contract.subindex}">{module_name}</a> the method "{receive_name}" was called.<br/><br/>'

        message += f"""

{self.footer(notification_event)}
"""
        return MessageResponse(
            **{
                "title_telegram": "",
                "title_email": "CCDExplorer Notification - Method called on smart contract",
                "message_telegram": message,
                "message_email": message,
            }
        )
