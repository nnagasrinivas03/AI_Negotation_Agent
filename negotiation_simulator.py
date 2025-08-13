import time
import random
import subprocess

# === Call LLM via Ollama CLI ===
def call_ollama(prompt):
    process = subprocess.Popen(
        ['ollama', 'run', 'llama3:8b'],
        stdin=subprocess.PIPE,
        stdout=subprocess.PIPE,
        stderr=subprocess.PIPE,
        text=True,
        encoding='utf-8'
    )
    stdout, _ = process.communicate(prompt)
    return stdout.strip()
class Agent:
    def __init__(self, role, secret_price, item_desc):
        self.role = role  # 'Buyer' or 'Seller'
        self.secret_price = secret_price  # min price (Seller) or max budget (Buyer)
        self.item_desc = item_desc
        self.last_offer = None
        self.persona = "Neutral"

    def offer(self, opponent_offer):
        """Decide next offer given opponent's last offer."""
        raise NotImplementedError

    def respond(self, opponent_offer):
        """Respond textually to opponent's offer."""
        return ""

    def is_acceptable(self, offer):
        """Check if offer meets this agent's constraints."""
        if self.role == 'Buyer':
            return offer <= self.secret_price
        else:
            return offer >= self.secret_price

class AggressiveSeller(Agent):
    def __init__(self, secret_min_price, item_desc, market_price):
        super().__init__('Seller', secret_min_price, item_desc)
        self.persona = "Aggressive Trader"
        self.market_price = market_price
        self.current_offer = market_price

    def offer(self, opponent_offer):
        if opponent_offer is None:
            self.last_offer = self.current_offer
        else:
            if opponent_offer < self.current_offer * 0.95:
                self.current_offer = max(self.secret_price, self.current_offer * 0.97)
            else:
                self.current_offer = max(self.secret_price, opponent_offer + (self.secret_price - opponent_offer)/2)
            self.last_offer = round(self.current_offer)
        return self.last_offer

    def respond(self, opponent_offer):
        responses = [
            f"Fresh {self.item_desc}, market rate ₹{self.market_price}. For you, ₹{self.last_offer}—final offer!",
            "Two buyers waiting. Take it or leave it.",
            "Quality like this won’t last. My offer stands."
        ]
        if opponent_offer is None:
            return f"Starting price: ₹{self.market_price} for {self.item_desc}."
        if opponent_offer < self.last_offer * 0.9:
            return "Your offer is too low. I can't go that far down."
        elif opponent_offer >= self.last_offer:
            return "Deal sounds fair. Let's close it."
        else:
            return random.choice(responses)

class AnalyticalBuyer(Agent):
    def __init__(self, secret_max_budget, item_desc, market_price):
        super().__init__('Buyer', secret_max_budget, item_desc)
        self.persona = "Data-Driven Analyst"
        self.market_price = market_price
        self.current_offer = secret_max_budget * 0.8

    def offer(self, opponent_offer):
        if opponent_offer is None:
            self.last_offer = round(self.current_offer)
        else:
            if opponent_offer > self.last_offer * 1.1:
                self.current_offer = min(self.secret_price, self.current_offer * 1.05)
            else:
                self.current_offer = min(self.secret_price, (self.last_offer + opponent_offer) / 2)
            self.last_offer = round(self.current_offer)
        return self.last_offer

    def respond(self, opponent_offer):
        if opponent_offer is None:
            return f"Looking to buy {self.item_desc} within ₹{self.secret_price} budget."
        elif opponent_offer <= self.last_offer:
            return "That’s a reasonable price. I can work with that."
        elif opponent_offer > self.secret_price:
            return "Your price exceeds my budget. Can we negotiate?"
        else:
            return "Let me crunch some numbers and get back to you."

def negotiate(seller, buyer, max_rounds=10, round_time=15):
    print(f"Negotiation starts for {seller.item_desc}!")
    print(f"Seller Persona: {seller.persona} | Buyer Persona: {buyer.persona}\n")

    seller_offer = None
    buyer_offer = None
    deal_price = None

    start_time = time.time()
    for round_num in range(1, max_rounds + 1):
        print(f"Round {round_num}:")

        seller_offer = seller.offer(buyer_offer)
        print(f"Seller offers: ₹{seller_offer}")
        print("Seller says:", seller.respond(buyer_offer))

        if buyer.is_acceptable(seller_offer):
            deal_price = seller_offer
            print(f"Buyer accepts the offer: ₹{deal_price}")
            break

        buyer_offer = buyer.offer(seller_offer)
        print(f"Buyer offers: ₹{buyer_offer}")
        print("Buyer says:", buyer.respond(seller_offer))

        if seller.is_acceptable(buyer_offer):
            deal_price = buyer_offer
            print(f"Seller accepts the offer: ₹{deal_price}")
            break

        if time.time() - start_time > round_time * max_rounds:
            print("Negotiation timed out.")
            break

        print("-" * 40)
        time.sleep(1)

    if deal_price is None:
        print("\nNo deal reached.")
        return None

    print(f"\nDeal closed at ₹{deal_price} for {seller.item_desc}!")

    # Scoring:
    # Profit/Savings (40%)
    # Character Score (40%) - assume perfect persona adherence = 1.5
    # Speed Bonus (20%) - bonus if deal closed in under 5 rounds

    seller_profit = deal_price - seller.secret_price
    buyer_savings = buyer.secret_price - deal_price

    profit_savings_score = (seller_profit if seller_profit > 0 else 0) / (seller.market_price - seller.secret_price)
    profit_savings_score = max(0, min(profit_savings_score, 1))

    character_score = 1.5

    speed_bonus = 1.0 if round_num <= 5 else 0.5

    final_score = (profit_savings_score * 0.4) + (character_score * 0.4) + (speed_bonus * 0.2)

    print(f"\nScoring:")
    print(f"Seller Profit: ₹{seller_profit} ({profit_savings_score*100:.1f}%)")
    print(f"Buyer Savings: ₹{buyer_savings}")
    print(f"Character Score: {character_score*100:.1f}%")
    print(f"Speed Bonus: {speed_bonus*100:.1f}%")
    print(f"Final Score (Weighted): {final_score*100:.1f}%")

    return deal_price, final_score

# Running sample negotiations

def run_test_negotiation():
    products = [
        {
            "name": "Kesar Mangoes",
            "grade": "A",
            "origin": "Junagadh",
            "ripeness": "Optimal",
            "quantity": 30,
            "base_price": 1200  
        },
        {
            "name": "Coffee Beans",
            "grade": "Specialty",
            "origin": "Coorg",
            "ripeness": "Fresh Roasted",
            "quantity": 90,
            "base_price": 600
        }
    ]

    for product in products:
        # Seller minimum acceptable price
        seller_secret_min_price = int(product["base_price"] * 0.8)  # e.g. 80% of base price
        # Buyer maximum budget
        buyer_secret_max_budget = int(product["base_price"] * 1.1)  # e.g. 110% of base price

        seller = AggressiveSeller(secret_min_price=seller_secret_min_price,
                                  item_desc=f"{product['name']} ({product['grade']})",
                                  market_price=product["base_price"])

        buyer = AnalyticalBuyer(secret_max_budget=buyer_secret_max_budget,
                                item_desc=f"{product['name']} ({product['grade']})",
                                market_price=product["base_price"])

        print(f"\n=== 🧪 New Negotiation: {product['name']} ===")
        result = negotiate(seller, buyer)
        if result:
            price, score = result
            print(f"✅ Deal at ₹{price} with score {score:.2f}")
        else:
            print("❌ No Deal")

if __name__ == "__main__":
    run_test_negotiation()
