import requests
from django.conf import settings

ELIGIBILITY_URL = "https://erp.betopiagroup.com/grocery-api/eligibility/"
GROCERY_ORDER_URL = "https://erp.betopiagroup.com/grocery-api/order/"
REJECT_ORDER_URL = "https://erp.betopiagroup.com/grocery-api/order/reject"
SHOPPING_REQUEST_URL = "https://erp.betopiagroup.com/advance-salary/shoppingrequest/"


def get_eligible_amount(access_token):
    """
    Hit central eligibility API to get the user's eligible shopping balance.
    Uses the user's microsoft_access_token for authentication.
    Returns the eligible_money as float, or None if the call fails.
    Block order placement on failure - critical for financial safety.
    """
    if not access_token:
        return None

    headers = {
        "Authorization": f"Bearer {access_token}",
        "Content-Type": "application/json",
    }

    try:
        response = requests.post(
            ELIGIBILITY_URL,
            json={},
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
    access_token, amount, product_name, order_id, date_time=None, funding_source="bank"
):
    """
    Submit the new grocery order to the central ERP grocery API.
    Uses the user's microsoft_access_token for authentication.
    Returns True only if the response explicitly has success=true.
    """
    if not access_token:
        return False

    from django.utils import timezone

    if date_time is None:
        date_time = timezone.now().strftime("%Y-%m-%dT%H:%M:%S")

    payload = {
        "amount": float(amount),
        "product_name": product_name,
        "order_id": order_id,
        "date_time": date_time,
        "funding_source": funding_source,
    }
    headers = {
        "Authorization": f"Bearer {access_token}",
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


def reject_grocery_order(access_token, order_id):
    """
    Submit a reject request to the central ERP grocery API.
    Returns True only if the central API explicitly returns success=true.
    """
    if not access_token or not order_id:
        return False

    payload = {"order_id": order_id}
    headers = {
        "Authorization": f"Bearer {access_token}",
        "Content-Type": "application/json",
    }

    try:
        response = requests.post(
            REJECT_ORDER_URL,
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


def confirm_order_delivery(order_id):
    """
    Hit central order confirmation API to mark order as delivered.
    Deducts money and changes status to approved.
    Returns True only if the response explicitly has success=true.
    """
    if not order_id:
        return False

    payload = {"order_id": order_id}
    headers = {
        "X-API-Key": settings.GROCERY_ELIGIBILITY_API_KEY,
        "Content-Type": "application/json",
    }

    try:
        response = requests.post(
            "https://erp.betopiagroup.com/grocery-api/order/confirm/",
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
