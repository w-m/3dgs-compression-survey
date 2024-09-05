### gsplat

This approach leverages 3D Gaussian Splatting as Markov Chain Monte Carlo <a target="_blank" href="https://ubc-vision.github.io/3dgs-mcmc/">(3DGS-MCMC)</a>, interpreting the training process of positioning and optimizing Gaussians as a sampling procedure rather than minimizing a predefined loss function. 

Additionally, it incorporates compression techniques derived from the 
<span class="text-item"><span class="text-color-box" style="background-color: rgb(31, 119, 180);"></span><a href="#morgenstern2024compact" style="display: inline;">Self-Organizing Gaussians</a></span> paper, which organizes the parameters of 3DGS in a 2D grid, capitalizing on perceptual redundancies found in natural scenes, thereby significantly reducing storage requirements. 

Further compression is achieved by applying methods from 
<a target="_blank" href="https://aras-p.info/blog/2023/09/27/Making-Gaussian-Splats-more-smaller/">Making Gaussian Splats more smaller</a>, which reduces the size of Gaussian splats by clustering spherical harmonics into discrete elements and storing them as FP16 values.

This technique is implemented in 
<a target="_blank" href="https://docs.gsplat.studio">gsplat</a>, an open-source library designed for CUDA-accelerated  differentiable rasterization of 3D Gaussians, equipped with Python bindings.

