"""
Canonical schema definition for IBM AML transaction datasets.
"""

REQUIRED_COLUMNS = {
    "Timestamp",
    "From Bank",
    "Account",
    "To Bank",
    "Account.1",
    "Amount Received",
    "Receiving Currency",
    "Amount Paid",
    "Payment Currency",
    "Payment Format",
    "Is_Laundering",
}

OPTIONAL_COLUMNS = {
    "Bank Name_sender",
    "Entity ID_sender",
    "Entity Name_sender",
    "Bank Name_receiver",
    "Entity ID_receiver",
    "Entity Name_receiver",
    "Source_Set",
}

COLUMN_RENAMES = {
    "Timestamp": "timestamp",
    "From Bank": "from_bank",
    "Account": "from_account",
    "To Bank": "to_bank",
    "Account.1": "to_account",
    "Amount Received": "amount_received",
    "Receiving Currency": "receiving_currency",
    "Amount Paid": "amount_paid",
    "Payment Currency": "payment_currency",
    "Payment Format": "payment_format",
    "Is_Laundering": "is_laundering",
    "Bank Name_sender": "sender_bank_name",
    "Entity ID_sender": "sender_entity_id",
    "Entity Name_sender": "sender_entity_name",
    "Bank Name_receiver": "receiver_bank_name",
    "Entity ID_receiver": "receiver_entity_id",
    "Entity Name_receiver": "receiver_entity_name",
    "Source_Set": "source_set",
}