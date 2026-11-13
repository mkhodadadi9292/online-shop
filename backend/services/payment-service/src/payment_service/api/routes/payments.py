"""Payment endpoints."""

from __future__ import annotations

from fastapi import APIRouter, Depends

from payment_service.api.deps import get_payment_service
from payment_service.api.schemas import PaymentResponse, ProcessPaymentRequest
from payment_service.application.payment_service import PaymentService
from payment_service.domain.payment import Payment

router = APIRouter(tags=["payments"])


def _response(payment: Payment) -> PaymentResponse:
    return PaymentResponse(
        id=payment.id,
        order_id=payment.order_id,
        amount=payment.amount,
        status=payment.status.value,
        reference=payment.reference,
        created_at=payment.created_at,
    )


@router.get("/{payment_id}", response_model=PaymentResponse)
async def get_payment(
    payment_id: str,
    service: PaymentService = Depends(get_payment_service),
) -> PaymentResponse:
    return _response(await service.get(payment_id))


@router.post("", response_model=PaymentResponse, status_code=201)
async def process_payment(
    payload: ProcessPaymentRequest,
    service: PaymentService = Depends(get_payment_service),
) -> PaymentResponse:
    return _response(await service.process(payload.order_id, payload.amount))


@router.post("/{payment_id}/refund", response_model=PaymentResponse)
async def refund_payment(
    payment_id: str,
    service: PaymentService = Depends(get_payment_service),
) -> PaymentResponse:
    return _response(await service.refund(payment_id))
