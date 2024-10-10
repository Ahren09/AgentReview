import numpy as np
import torch


def pairwise_cos_sim(A: torch.Tensor, B: torch.Tensor, device="cuda:0"):
    if isinstance(A, np.ndarray):
        A = torch.from_numpy(A).to(device)

    if isinstance(B, np.ndarray):
        B = torch.from_numpy(B).to(device)

    from torch.nn.functional import normalize
    A_norm = normalize(A, dim=1)  # Normalize the rows of A
    B_norm = normalize(B, dim=1)  # Normalize the rows of B
    cos_sim = torch.matmul(A_norm,
                           B_norm.t())  # Calculate the cosine similarity
    return cos_sim