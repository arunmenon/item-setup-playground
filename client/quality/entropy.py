import numpy as np
from scipy.stats import entropy

# Define the true distribution P and the approximate distribution Q
P = np.array([0.1, 0.4, 0.5])
Q = np.array([0.2, 0.3, 0.5])

# Compute KL divergence from P to Q
kl_divergence = entropy(P, Q)
print(f"KL Divergence: {kl_divergence}")
