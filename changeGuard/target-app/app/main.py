from fastapi import FastAPI, HTTPException
from pydantic import BaseModel

app = FastAPI(title="Payment Microservice")

class PaymentRequest(BaseModel):
    account_id: str
    amount: float
    currency: str = "USD"

@app.get("/health")
def health():
    return {"status": "ok"}

@app.post("/pay")
def process_payment(payment: PaymentRequest):
    if payment.amount <= 0:
        raise HTTPException(status_code=400, detail="Invalid payment amount")
    return {
        "status": "COMPLETED",
        "tx_id": f"tx_{payment.account_id}_98213",
        "amount": payment.amount
    }