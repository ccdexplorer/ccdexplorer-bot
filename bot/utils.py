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
from ccdexplorer_fundamentals.mongodb import MongoLabeledAccount
from telegram import Update
from telegram.ext import ContextTypes

from env import *
from notification_classes import *
from ccdexplorer_fundamentals.user_v2 import (
    AccountForUser,
    NotificationPreferences,
    NotificationServices,
    Reward,
    UserV2,
)


class Utils:
    def complete_address(self, impacted_address):
        grpcclient: GRPCClient = self.connections.grpcclient
        if impacted_address:
            if isinstance(impacted_address, CCD_ContractAddress):
                return CCD_Address_Complete(contract=impacted_address)

            elif isinstance(impacted_address, CCD_AccountAddress):
                if len(impacted_address) > 28:
                    account_id = impacted_address

                    from_nightly = self.nightly_accounts_by_account_id.get(account_id)
                    if from_nightly:
                        account_index = from_nightly["index"]
                    else:
                        account_index = grpcclient.get_account_info(
                            "last_final", impacted_address
                        ).index

                    return CCD_Address_Complete(
                        account=CCD_AccountAddress_Complete(
                            id=account_id, index=account_index
                        )
                    )

                else:
                    contract = CCD_ContractAddress.from_str(impacted_address)
                    return CCD_Address_Complete(contract=contract)

            elif isinstance(impacted_address, int):
                account_index = impacted_address
                from_nightly = self.nightly_accounts_by_account_index.get(account_index)
                if from_nightly:
                    account_id = from_nightly["_id"]
                else:
                    account_id = self.connections.grpcclient.get_account_info(
                        "last_final", account_index=impacted_address
                    ).address

                return CCD_Address_Complete(
                    account=CCD_AccountAddress_Complete(
                        id=account_id, index=account_index
                    )
                )

    def find_label_for_impacted_address(
        self, impacted_address: ImpactedAddress, user: UserV2
    ):
        if impacted_address.address.contract:
            lookup_value = impacted_address.address.contract.to_str()

        if impacted_address.address.account:
            lookup_value = impacted_address.address.account.index

        if user.accounts.get(str(lookup_value)):
            user_account: AccountForUser = user.accounts[str(lookup_value)]
            impacted_address.label = user_account.label

        elif self.labeled_accounts.get(lookup_value):
            labeled_account: MongoLabeledAccount = self.labeled_accounts[lookup_value]
            impacted_address.label = labeled_account.label

        else:
            if impacted_address.address.contract:
                impacted_address.label = impacted_address.address.contract.index
            else:
                impacted_address.label = impacted_address.address.account.index

        return impacted_address

    def add_labels_to_notitication_event(
        self,
        user: UserV2,
        notification_event: NotificationEvent,
    ) -> Optional[str]:
        enriched_impacted_addresses = []
        for impacted_address in notification_event.impacted_addresses:
            enriched_impacted_addresses.append(
                self.find_label_for_impacted_address(impacted_address, user)
            )
        notification_event.impacted_addresses = enriched_impacted_addresses
        return notification_event

    def set_notification_service(
        self,
        notifcation_object: NotificationPreferences,
        amount_for_limit: microCCD = None,
    ):
        send_to_service_dict: dict[NotificationServices:bool] = {}
        for ns in NotificationServices:
            send_to_service_dict[ns] = False

        if not notifcation_object:
            return send_to_service_dict

        # if a limit is not relevant or not given, there is no need to compare to a limit.
        if not amount_for_limit:
            if notifcation_object.telegram:
                send_to_service_dict[NotificationServices.telegram] = (
                    notifcation_object.telegram.enabled
                )
            else:
                send_to_service_dict[NotificationServices.telegram] = False

            if notifcation_object.email:
                send_to_service_dict[NotificationServices.email] = (
                    notifcation_object.email.enabled
                )
            else:
                send_to_service_dict[NotificationServices.email] = False

            return send_to_service_dict

        # If this is a notification event where a limit is relevant, first check this case.
        # as we have returned early, there is a amount_for_limit here.
        if notifcation_object.telegram:
            if notifcation_object.telegram.limit:
                send_to_service_dict[NotificationServices.telegram] = (
                    notifcation_object.telegram.enabled
                    and (notifcation_object.telegram.limit < amount_for_limit)
                )
            else:
                send_to_service_dict[NotificationServices.telegram] = (
                    notifcation_object.telegram.enabled
                )
        else:
            send_to_service_dict[NotificationServices.telegram] = False

        if notifcation_object.email:
            if notifcation_object.email.limit:
                send_to_service_dict[NotificationServices.email] = (
                    notifcation_object.email.enabled
                    and (notifcation_object.email.limit < amount_for_limit)
                )
            else:
                send_to_service_dict[NotificationServices.email] = (
                    notifcation_object.email.enabled
                )
        else:
            send_to_service_dict[NotificationServices.email] = False

        return send_to_service_dict

    def return_specific_address_type(
        self, impacted_addresses: list[ImpactedAddress], address_type: AddressType
    ):
        for impacted_address in impacted_addresses:
            if impacted_address.address_type == address_type:
                return impacted_address
        print(f"Can't find {address_type} in impacted addresses!")
