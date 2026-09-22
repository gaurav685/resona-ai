"""Small feed-forward network for Big Five regression.

Input features -> Linear -> ReLU -> Dropout -> Linear -> ReLU -> Dropout ->
Linear -> 5 outputs (Openness, Conscientiousness, Extraversion,
Agreeableness, Neuroticism). Deliberately small — this is a 279-row
tabular dataset, not a place for a large network.
"""

from __future__ import annotations

import torch.nn as nn


class PersonalityNet(nn.Module):
    def __init__(self, input_dim: int, hidden1: int = 64, hidden2: int = 32, output_dim: int = 5, dropout: float = 0.3):
        super().__init__()
        self.net = nn.Sequential(
            nn.Linear(input_dim, hidden1),
            nn.ReLU(),
            nn.Dropout(dropout),
            nn.Linear(hidden1, hidden2),
            nn.ReLU(),
            nn.Dropout(dropout),
            nn.Linear(hidden2, output_dim),
        )

    def forward(self, x):
        return self.net(x)
