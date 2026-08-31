# schemas.py

from pydantic import BaseModel
from typing import Literal, Optional

class OrderDetails(BaseModel):
    order_id: Optional[str] = None
    product: Literal['wireless_earbuds', 'standing_desk_converter', 
                    'robot_vacuum', 'smart_blender', 'noise_cancelling_headphones', 
                    'portable_monitor', 'ergonomic_keyboard', 'air_purifier', 'misc']
    purchase_date: Optional[str] = None

class Ticket(BaseModel):
    customer_name: Optional[str] = None
    issue_category: Literal['billing', 'shipping', 'technical', 'account_access', 'product_defect',
                           'refund_request', 'general_inquiry', 'misc']
    urgency: Literal['High', 'Medium', 'Low']
    order: OrderDetails
    summary: str

class TicketRequestModel(BaseModel):
    ticket_str: str
