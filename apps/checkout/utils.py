import requests
from django.conf import settings

ELIGIBILITY_URL = "https://erp.betopiagroup.com/grocery-api/eligibility/"
GROCERY_ORDER_URL = "https://erp.betopiagroup.com/grocery-api/order/"
SHOPPING_REQUEST_URL = "https://erp.betopiagroup.com/advance-salary/shoppingrequest/"


def get_eligible_amount(email):
    """
    Hit central eligibility API to get the user's eligible shopping balance.
    Returns the eligible_money as float, or None if the call fails.
    Block order placement on failure - critical for financial safety.
    """
    if not email:
        return None

    payload = {"email": email}
    headers = {
        "X-API-Key": settings.GROCERY_ELIGIBILITY_API_KEY,
        "Content-Type": "application/json",
    }

    try:
        response = requests.post(
            ELIGIBILITY_URL,
            json=payload,
            headers=headers,
            timeout=10,
        )
        if response.status_code != 200:
            return None
        data = response.json()
        if data.get("success") is not True:
            return None
        return float(data.get("eligible_money"))
    except (requests.RequestException, KeyError, ValueError, TypeError):
        return None


def post_grocery_order(
    email, amount, product_name, order_id, date_time=None, funding_source="bank"
):
    """
    Submit the new grocery order to the central ERP grocery API.
    Returns True only if the response explicitly has success=true.
    """
    if not email:
        return False

    from django.utils import timezone

    if date_time is None:
        date_time = timezone.now().strftime("%Y-%m-%dT%H:%M:%S")

    payload = {
        "email": email,
        "amount": float(amount),
        "product_name": product_name,
        "order_id": order_id,
        "date_time": date_time,
        "funding_source": funding_source,
    }
    headers = {
        "X-API-Key": settings.GROCERY_ELIGIBILITY_API_KEY,
        "Content-Type": "application/json",
    }

    try:
        response = requests.post(
            GROCERY_ORDER_URL,
            json=payload,
            headers=headers,
            timeout=10,
        )
        if response.status_code != 200:
            return False
        data = response.json()
        return data.get("success") is True
    except (requests.RequestException, ValueError):
        return False


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
