import logging
from utils.api_requests import APIClient

logger = logging.getLogger(__name__)


class DeltaClient(APIClient):
    def __init__(self, base_url, auth_url, realm, client_id, client_secret, add_auth_to_path=False):
        super().__init__(base_url=base_url, auth_url=auth_url, realm=realm, client_id=client_id, client_secret=client_secret, add_auth_to_path=add_auth_to_path)

    def get_email_by_cpr(self, cpr: str) -> str | None:
        """Return the email from an active engagement for the given CPR, if any."""
        if not cpr:
            raise ValueError("cpr must be provided")

        query = {
            "graphQueries": [
                {
                    "computeAvailablePages": False,
                    "graphQuery": {
                        "structure": {
                            "alias": "eng",
                            "userKey": "APOS-Types-Engagement",
                            "relations": [
                                {
                                    "alias": "person",
                                    "userKey": "APOS-Types-Engagement-TypeRelation-Person",
                                    "typeUserKey": "APOS-Types-Person",
                                    "direction": "OUT",
                                },
                            ],
                        },
                        "criteria": {
                            "type": "AND",
                            "criteria": [
                                {
                                    "type": "MATCH",
                                    "operator": "EQUAL",
                                    "left": {"source": "DEFINITION", "alias": "eng.person.$userKey"},
                                    "right": {"source": "STATIC", "value": cpr},
                                },
                                {
                                    "type": "MATCH",
                                    "operator": "EQUAL",
                                    "left": {"source": "DEFINITION", "alias": "eng.$state"},
                                    "right": {"source": "STATIC", "value": "STATE_ACTIVE"},
                                },
                            ],
                        },
                        "projection": {
                            "attributes": ["APOS-Types-Engagement-Attribute-Email"],
                        },
                    },
                    "validDate": "NOW",
                    "limit": 100,
                },
            ],
        }

        response = self.make_request(path="/api/object/graph-query", method="POST", json=query)
        emails = {
            attribute["value"]
            for result in response["graphQueryResult"]
            for instance in result["instances"]
            for attribute in instance.get("attributes", [])
            if attribute.get("userKey") == "APOS-Types-Engagement-Attribute-Email"
            and isinstance(attribute.get("value"), str)
            and attribute["value"]
        }
        if len(emails) > 1:
            raise ValueError("Multiple email addresses found for active engagements")
        return next(iter(emails), None)
