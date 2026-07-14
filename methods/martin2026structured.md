### Structured Image-based Coding for Efficient Gaussian Splatting Compression

GSICO proposes a fully post-training, codec-oriented compression framework that can be applied to pretrained vanilla 3DGS and <insert>Scaffold-GS</insert> models without access to the training images, retraining, or fine-tuning.
Similar to the work of Self-Organizing Gaussians (<insert>SOG</insert>), it maps Gaussian parameters into aligned 2D parameter images
GSICO replaces SOG's training-time grid regularization and PLAS with a hierarchical organization procedure: fixed-size groups of 256 primitives are formed using K-means, assigned to 16&times;16 image blocks, and arranged both across blocks and within each block using a novel greedy Nearest-Neighbor-based Sorting (NNS) algorithm.
For 3DGS, spherical-harmonic coefficients are transformed from RGB to YUV, clustering and sorting are guided by the luminance AC coefficients, and less perceptually important chrominance AC coefficients can be discarded.
For Scaffold-GS, anchor positions and offset features define the similarity space, while the small prediction MLPs are transmitted directly.
The resulting maps are independently quantized and encoded with JPEG XL, using lossy coding primarily for 3DGS appearance attributes and lossless coding for the more compression-sensitive Scaffold-GS representation.
GSICO therefore stands out as a model-agnostic, image-codec-based method that exploits parameter coherence entirely after reconstruction, rather than learning a compressed representation or adapting the scene for compression.
