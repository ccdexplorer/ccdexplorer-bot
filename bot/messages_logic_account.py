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

from .messages_definitions_account import MessageAccount as MessageAccount
from .utils import Utils as Utils

if TYPE_CHECKING:
    from bot import Bot

console = Console()


class ProcessAccount(MessageAccount, Utils):
    def process_event_type_account(
        self, user: UserV2, notification_event: NotificationEvent
    ):
        message_response = None
        notification_services_to_send = None
        event_type = EventTypeAccount(
            **notification_event.event_type.model_dump()[
                list(notification_event.event_type.model_fields_set)[0]
            ]
        )
        account_index = (
            notification_event.impacted_addresses[0].address.account.index
            if notification_event.impacted_addresses[0].address.account
            else None
        )
        if user.accounts.get(str(account_index)):
            user_account: AccountForUser = user.accounts[str(account_index)]

        else:
            return None, None

        if not user_account.account_notification_preferences:
            return None, None

        if event_type.module_deployed:
            notification_services_to_send = self.set_notification_service(
                user_account.account_notification_preferences.module_deployed
            )
            if any(notification_services_to_send.values()):
                message_response = self.define_module_deployed_message(
                    event_type, notification_event, user
                )

        if event_type.contract_initialized:
            notification_services_to_send = self.set_notification_service(
                user_account.account_notification_preferences.contract_initialized
            )
            if any(notification_services_to_send.values()):
                message_response = self.define_contract_initialized_message(
                    notification_event, user
                )

        if event_type.account_transfer:
            notification_services_to_send = self.set_notification_service(
                user_account.account_notification_preferences.account_transfer,
                event_type.account_transfer.amount,
            )

            if any(notification_services_to_send.values()):
                message_response = self.define_account_transfer_message(
                    notification_event, user
                )

        if event_type.transferred_with_schedule:
            scheduled_send_amount = sum(
                [int(x.amount) for x in event_type.transferred_with_schedule.amount]
            )
            notification_services_to_send = self.set_notification_service(
                user_account.account_notification_preferences.transferred_with_schedule,
                scheduled_send_amount,
            )

            if any(notification_services_to_send.values()):
                message_response = self.define_transferred_with_schedule_message(
                    notification_event, user
                )

        if event_type.delegation_configured:
            notification_services_to_send = self.set_notification_service(
                user_account.account_notification_preferences.delegation_configured
            )
            if any(notification_services_to_send.values()):
                message_response = self.define_delegation_configured_message(
                    event_type, notification_event, user
                )

        if event_type.data_registered:
            notification_services_to_send = self.set_notification_service(
                user_account.account_notification_preferences.data_registered
            )
            if any(notification_services_to_send.values()):
                message_response = self.define_data_registered_message(
                    notification_event, user
                )

        if event_type.payday_account_reward:
            notification_services_to_send = self.set_notification_service(
                user_account.account_notification_preferences.payday_account_reward
            )
            if any(notification_services_to_send.values()):
                message_response = self.define_payday_account_reward_message(
                    event_type, notification_event, user
                )

        if event_type.token_event:
            notification_services_to_send = self.set_notification_service(
                user_account.account_notification_preferences.token_event
            )
            if any(notification_services_to_send.values()):
                message_response = self.define_token_event_message(
                    notification_event, user
                )

        if event_type.validator_commission_changed:
            if (
                user_account.delegation_target
                == event_type.validator_commission_changed.validator_id
            ):
                notification_services_to_send = self.set_notification_service(
                    user_account.account_notification_preferences.validator_commission_changed
                )
                if any(notification_services_to_send.values()):
                    message_response = (
                        self.define_validator_target_commission_changed_message(
                            event_type.validator_commission_changed.events,
                            notification_event,
                            user,
                            user_account,
                        )
                    )

        return message_response, notification_services_to_send
