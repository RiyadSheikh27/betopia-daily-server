import requests
from django.conf import settings


ELIGIBILITY_URL = "https://erp.betopiagroup.com/advance-salary/eligibility/"
SHOPPING_REQUEST_URL = "https://erp.betopiagroup.com/advance-salary/shoppingrequest/"


def get_eligible_amount(access_token):
    """
    Hit central eligibility API to get the user's eligible shopping balance.
    Returns the eligible_amount as float, or None if the call fails.
    Block order placement on failure - critical for financial safety.
    """
    try:
        response = requests.get(
            ELIGIBILITY_URL,
            headers={"Authorization": f"Bearer {access_token}"},
            timeout=10,
        )
        if response.status_code != 200:
            return None
        data = response.json()
        return data["eligibility"]["eligible_amount"]
    except (requests.RequestException, KeyError, ValueError):
        return None


def hit_shopping_request(access_token, employee_id, amount, product_name, order_id):
    """
    Hit central shopping request API to confirm an accepted order.
    Returns True only if the response explicitly has success=true.
    """
    from django.utils import timezone

    payload = {
        "employee_id": str(employee_id),
        "amount": float(amount),
        "date_time": timezone.now().strftime("%Y-%m-%dT%H:%M:%S"),
        "product_name": product_name,
        "order_id": order_id,
    }
    try:
        response = requests.post(
            SHOPPING_REQUEST_URL,
            json=payload,
            headers={"Authorization": f"Bearer {access_token}"},
            timeout=10,
        )
        if response.status_code != 200:
            return False
        data = response.json()
        return data.get("success") is True
    except (requests.RequestException, ValueError):
        return False