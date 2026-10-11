class Payment:
    def process_payment(self, amount):
        pass

class CreditCardPayment(Payment):
    def __init__(self):
        self.fee = 0.2
    def process_payment(self, amount):
        if amount <= 0:
            print("Invalid payment amount.")
            return False
        fee = round(amount * 0.002)
        total_amount = amount + fee
        print("Processing payment through Credit card.")
        print(f"Original amount {amount}")
        print(f"Fee chanrged {fee}")
        print(f"Total charged {total_amount}.")
        print("Successfully processed payment through Credit card.")
        return True


class PayPalPayment(Payment):
    def process_payment(self, amount):
        if amount <= 0:
            print("Invalid payment amount.")
            return False
        print("Processing payment through PayPal...")
        print(f"Amount paid: {amount}")
        print("PayPal payment successful.")

class UPIPayment(Payment):
    def process_payment(self, amount):
        if amount <= 0:
            print("Invalid payment amount.")
        print("processing payment using UPI.")
        print(f"Amount paid: {amount}")
        print("UPI payment successful.")

def make_payment(payment_obj, amount):
    payment_obj.process_payment(amount)


credit_card = CreditCardPayment()

paypal = PayPalPayment()

upi = UPIPayment()


make_payment(credit_card, 1000)

print("-------------------")

make_payment(paypal, 500)

print("-------------------")

make_payment(upi, 250)