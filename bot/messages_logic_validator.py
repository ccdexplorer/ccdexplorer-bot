# ruff: noqa: F403, F405, E402, E501, F401

from typing import TYPE_CHECKING

from rich import print
from rich.console import Console
from env import *
from notification_classes import *
from ccdexplorer_fundamentals.user_v2 import (
    AccountForUser,
    UserV2,
)
from .messages_definitions_validator import MessageValidator as MessageValidator
from .utils import Utils as Utils

if TYPE_CHECKING:
    from bot import Bot

console = Console()


class ProcessValidator(MessageValidator, Utils):
    def process_event_type_validator(
        self, user: UserV2, notification_event: NotificationEvent
    ):
        message_response = None
        notification_services_to_send = None
        event_type = EventTypeValidator(
            **notification_event.event_type.model_dump()[
                list(notification_event.event_type.model_fields_set)[0]
            ]
        )

        # We will use the first impacted address for determining whether a user
        # should be notified.
        account_index = (
            notification_event.impacted_addresses[0].address.account.index
            if notification_event.impacted_addresses[0].address.account
            else None
        )
        if user.accounts.get(str(account_index)):
            user_account: AccountForUser = user.accounts[str(account_index)]

            if not user_account.validator_notification_preferences:
                return None, None

            if event_type.baker_configured or event_type.validator_configured:
                notification_services_to_send = self.set_notification_service(
                    user_account.validator_notification_preferences.validator_configured
                )
                if any(notification_services_to_send.values()):
                    message_response = self.define_baker_configured_message(
                        event_type, notification_event, user
                    )

            if event_type.delegation_configured:
                notification_services_to_send = self.set_notification_service(
                    user_account.validator_notification_preferences.delegation_configured
                )
                if any(notification_services_to_send.values()):
                    message_response = self.define_delegation_configured_message(
                        event_type, notification_event, user
                    )

            if event_type.payday_pool_reward:
                notification_services_to_send = self.set_notification_service(
                    user_account.validator_notification_preferences.payday_pool_reward
                )

                if any(notification_services_to_send.values()):
                    message_response = self.define_payday_pool_reward_message(
                        notification_event, user
                    )

            if event_type.block_validated:
                notification_services_to_send = self.set_notification_service(
                    user_account.validator_notification_preferences.block_validated
                )

                if any(notification_services_to_send.values()):
                    message_response = self.define_block_baked_by_baker_message(
                        notification_event, user
                    )

            if event_type.validator_running_behind:
                notification_services_to_send = self.set_notification_service(
                    user_account.validator_notification_preferences.validator_running_behind
                )

                if any(notification_services_to_send.values()):
                    message_response = self.define_validator_running_behind_message(
                        notification_event, user
                    )

        return message_response, notification_services_to_send
