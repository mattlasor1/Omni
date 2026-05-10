from setuptools import setup
from torch.utils.cpp_extension import BuildExtension, CUDAExtension
import os

# Only build if CUDA is actually available on the host machine
if os.system("nvcc --version") == 0:
    setup(
        name='omnitwin_csrc',
        ext_modules=[
            CUDAExtension('omnitwin_csrc', [
                'core_math.cu',
            ]),
        ],
        cmdclass={
            'build_ext': BuildExtension
        }
    )
else:
    print("CUDA not found. Skipping C++ Core Extension compilation. Will fallback to numpy in Python.")
