#include <torch/extension.h>
#include <cuda.h>
#include <cuda_runtime.h>
#include <vector>

// CUDA kernel to compute O(N^2) correlation matrix across the entire vector space
// This radically accelerates the Tensor Cross-Pollination (Epiphany) engine.
__global__ void dot_product_kernel(
    const float* __restrict__ vectors,
    float* __restrict__ output_matrix,
    int num_vectors,
    int vector_dim) {
    
    int row = blockIdx.y * blockDim.y + threadIdx.y;
    int col = blockIdx.x * blockDim.x + threadIdx.x;
    
    if (row < num_vectors && col < num_vectors) {
        float dot_product = 0.0f;
        for (int i = 0; i < vector_dim; ++i) {
            dot_product += vectors[row * vector_dim + i] * vectors[col * vector_dim + i];
        }
        output_matrix[row * num_vectors + col] = dot_product;
    }
}

// C++ wrapper for the Python binding
torch::Tensor fast_correlation_matrix(torch::Tensor vectors) {
    auto num_vectors = vectors.size(0);
    auto vector_dim = vectors.size(1);
    
    auto output_matrix = torch::zeros({num_vectors, num_vectors}, torch::TensorOptions().device(vectors.device()));
    
    dim3 threads(16, 16);
    dim3 blocks((num_vectors + threads.x - 1) / threads.x, (num_vectors + threads.y - 1) / threads.y);
    
    dot_product_kernel<<<blocks, threads>>>(
        vectors.data_ptr<float>(),
        output_matrix.data_ptr<float>(),
        num_vectors,
        vector_dim
    );
    
    return output_matrix;
}

// Bind to Python
PYBIND11_MODULE(TORCH_EXTENSION_NAME, m) {
    m.def("fast_correlation_matrix", &fast_correlation_matrix, "Fast O(N^2) Correlation Matrix (CUDA)");
}
