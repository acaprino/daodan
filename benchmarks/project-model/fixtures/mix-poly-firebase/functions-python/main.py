import os

import stripe
from firebase_admin import firestore, initialize_app
from firebase_functions import https_fn

initialize_app()
stripe.api_key = os.environ.get("STRIPE_SECRET_KEY", "")


@https_fn.on_call()
def create_checkout_session(req: https_fn.CallableRequest) -> dict:
    session = stripe.checkout.Session.create(
        mode="payment",
        line_items=[{"price": req.data["price"], "quantity": 1}],
        success_url=req.data["return_url"],
    )
    firestore.client().collection("orders").document(session.id).set({"uid": req.auth.uid, "status": "open"})
    return {"url": session.url}
