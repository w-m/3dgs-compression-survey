### Compressed 3D Gaussian Splatting for Accelerated Novel View Synthesis

This approach aims to reduce the memory consumption and rendering efficency of 3D Gaussian splat representations. The authors propose a compressed
3D Gaussian splat representation consisting of three main steps: 
1. sensitivity-aware clustering, where scene parameters are measured according to their contribution to the training images and encoded into compact codebooks via sensitivity-aware vector quantization; 
2. quantization-aware fine-tuning, which recovers lost information by fine-tuning parameters at reduced bit-rates using quantization-aware training; and 
3. entropy encoding, which exploits spatial coherence through entropy and run-length encoding by linearizing 3D Gaussians along a space-filling curve.
Furthermore a renderer for the commpressed scenes that uses GPU sorting and rasterization is proposed, which enables real-time novel view sythesis on low-end devices.