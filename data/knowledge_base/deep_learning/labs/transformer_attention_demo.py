import torch


def scaled_dot_product_attention(q, k, v):
    d_k = q.shape[-1]
    scores = q @ k.transpose(-2, -1) / (d_k ** 0.5)
    weights = torch.softmax(scores, dim=-1)
    return weights @ v, weights


if __name__ == "__main__":
    q = torch.randn(1, 3, 4)
    k = torch.randn(1, 3, 4)
    v = torch.randn(1, 3, 4)
    output, weights = scaled_dot_product_attention(q, k, v)
    print("weights:", weights.shape)
    print("output:", output.shape)
