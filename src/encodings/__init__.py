from .binary import generate_binary_clauses
from .binomial import generate_binomial_clauses
from .commander import generate_commander_clauses
from .product import generate_product_clauses
from .sequential_counter import generate_sequential_clauses

ENCODINGS = {
    "Binomial": generate_binomial_clauses,
    "Binary": generate_binary_clauses,
    "Commander": generate_commander_clauses,
    "Product": generate_product_clauses,
    "Sequential": generate_sequential_clauses,
}