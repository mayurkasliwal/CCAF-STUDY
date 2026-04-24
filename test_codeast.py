# sample_code.py  — run AST on this file

class BankAccount:
    def __init__(self, owner: str, balance: float = 0.0):
        self.owner = owner
        self.balance = balance
        self.transactions = []

    def deposit(self, amount: float) -> float:
        if amount <= 0:
            raise ValueError("Deposit amount must be positive")
        self.balance += amount
        self.transactions.append(("deposit", amount))
        return self.balance

    def withdraw(self, amount: float) -> float:
        if amount <= 0:
            raise ValueError("Withdrawal amount must be positive")
        if amount > self.balance:
            raise ValueError("Insufficient funds")
        self.balance -= amount
        self.transactions.append(("withdraw", amount))
        return self.balance

    def get_summary(self) -> dict:
        return {
            "owner": self.owner,
            "balance": self.balance,
            "total_transactions": len(self.transactions)
        }


def process_accounts(accounts: list) -> list:
    summaries = []
    for account in accounts:
        if account.balance > 1000:
            account.deposit(account.balance * 0.05)  # 5% interest
        summaries.append(account.get_summary())
    return summaries


# Main execution
if __name__ == "__main__":
    acc1 = BankAccount("Alice", 1500.0)
    acc2 = BankAccount("Bob", 500.0)

    acc1.withdraw(200)
    acc2.deposit(800)

    results = process_accounts([acc1, acc2])
    for r in results:
        print(r)