from abc import ABC, abstractmethod

# Abstract Class
class PaymentMethod(ABC):
    
    @abstractmethod
    def process_payment(self, amount: float) -> bool:
        """Every payment method must implement this"""
        pass

    @abstractmethod
    def get_payment_type(self) -> str:
        pass


# Concrete Classes (Implementation)
class CreditCardPayment(PaymentMethod):
    def process_payment(self, amount: float) -> bool:
        print(f"💳 Processing ₹{amount} via Credit Card")
        return True

    def get_payment_type(self) -> str:
        return "Credit Card"


class UPIPayment(PaymentMethod):
    def process_payment(self, amount: float) -> bool:
        print(f"📱 Processing ₹{amount} via UPI")
        return True

    def get_payment_type(self) -> str:
        return "UPI"


# Usage
def make_payment(payment: PaymentMethod, amount: float):
    payment.process_payment(amount)

# This will work
cc = CreditCardPayment()
upi = UPIPayment()

make_payment(cc, 1500)
make_payment(upi, 500)

# This will raise error:
# payment = PaymentMethod()   # ← Not allowed