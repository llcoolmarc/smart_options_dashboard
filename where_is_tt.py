import tt_client, inspect
print("Imported from:", tt_client.__file__)
print("Has place_equity_order:", hasattr(tt_client.TastytradeClient, "place_equity_order"))
