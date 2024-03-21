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
from .messages_definitions_other import MessageOther as MessageOther
from .utils import Utils as Utils

if TYPE_CHECKING:
    from bot import Bot

console = Console()


class ProcessOther(MessageOther, Utils):
    def process_event_type_other(
        self, user: UserV2, notification_event: NotificationEvent
    ):
        message_response = None
        notification_services_to_send = None
        event_type = EventTypeOther(
            **notification_event.event_type.model_dump()[
                list(notification_event.event_type.model_fields_set)[0]
            ]
        )
        if (
            event_type.protocol_update
            and user.other_notification_preferences.protocol_update
        ):
            notification_services_to_send = self.set_notification_service(
                user.other_notification_preferences.protocol_update
            )
            if any(notification_services_to_send.values()):
                message_response = self.define_protocol_update_message(
                    notification_event, user
                )

        elif (
            event_type.add_anonymity_revoker_update
            and user.other_notification_preferences.add_anonymity_revoker_update
        ):
            notification_services_to_send = self.set_notification_service(
                user.other_notification_preferences.add_anonymity_revoker_update
            )
            if any(notification_services_to_send.values()):
                message_response = self.define_add_anonymity_revoker_update_message(
                    notification_event, user
                )

        elif (
            event_type.add_identity_provider_update
            and user.other_notification_preferences.add_identity_provider_update
        ):
            notification_services_to_send = self.set_notification_service(
                user.other_notification_preferences.add_identity_provider_update
            )
            if any(notification_services_to_send.values()):
                message_response = self.define_add_identity_provider_update_message(
                    notification_event, user
                )

        elif (
            event_type.module_deployed
            and user.other_notification_preferences.module_deployed
        ):
            notification_services_to_send = self.set_notification_service(
                user.other_notification_preferences.module_deployed
            )
            if any(notification_services_to_send.values()):
                message_response = self.define_module_deployed_message(
                    notification_event, user
                )

        elif (
            event_type.contract_initialized
            and user.other_notification_preferences.contract_initialized
        ):
            notification_services_to_send = self.set_notification_service(
                user.other_notification_preferences.contract_initialized
            )
            if any(notification_services_to_send.values()):
                message_response = self.define_contract_initialized_message(
                    notification_event, user
                )

        elif event_type.validator_lowered_stake:
            notification_services_to_send = self.set_notification_service(
                user.other_notification_preferences.validator_lowered_stake,
                event_type.validator_lowered_stake.unstaked_amount,
            )
            if any(notification_services_to_send.values()):
                message_response = self.define_other_lowered_stake_message(
                    notification_event, user
                )

        elif event_type.validator_commission_changed:
            notification_services_to_send = self.set_notification_service(
                user.other_notification_preferences.validator_commission_changed,
            )
            if any(notification_services_to_send.values()):
                message_response = self.define_commission_changed_message(
                    event_type.validator_commission_changed.events,
                    notification_event,
                    user,
                )

        elif event_type.account_transfer:
            notification_services_to_send = self.set_notification_service(
                user.other_notification_preferences.account_transfer,
                event_type.account_transfer.amount,
            )

            if any(notification_services_to_send.values()):
                message_response = self.define_account_transfer_message_for_other(
                    event_type, notification_event, user
                )

        elif event_type.transferred_with_schedule:
            scheduled_send_amount = sum(
                [int(x.amount) for x in event_type.transferred_with_schedule.amount]
            )
            notification_services_to_send = self.set_notification_service(
                user.other_notification_preferences.transferred_with_schedule,
                scheduled_send_amount,
            )

            if any(notification_services_to_send.values()):
                message_response = (
                    self.define_transferred_with_schedule_message_for_other(
                        event_type, notification_event, user
                    )
                )

        elif event_type.domain_name_minted:
            notification_services_to_send = self.set_notification_service(
                user.other_notification_preferences.domain_name_minted
            )

            if any(notification_services_to_send.values()):
                message_response = self.define_domain_name_minted_message(
                    notification_event, user
                )

        elif event_type.account_created:
            notification_services_to_send = self.set_notification_service(
                user.other_notification_preferences.account_created
            )

            if any(notification_services_to_send.values()):
                message_response = self.define_account_created_message(
                    notification_event, user
                )

        return message_response, notification_services_to_send
