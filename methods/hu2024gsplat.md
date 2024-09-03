### gsplat

This approach combines 3D Gaussian Splatting as Markov Chain Monte Carlo <a target="_blank" href="https://ubc-vision.github.io/3dgs-mcmc/">(3DGS-MCMC)</a> with compression techniques from the 

<span class="text-item"><span class="text-color-box" style="background-color: rgb(31, 119, 180);"></span><a href="#morgenstern2024compact" style="display: inline;">Self-Organizing Gaussians</a></span> 

paper and <a target="_blank" href="https://aras-p.info/blog/2023/09/27/Making-Gaussian-Splats-more-smaller/">Making Gaussian Splats more smaller</a>. It is implemented in <a target="_blank" href="https://docs.gsplat.studio">gsplat</a>, an open-source library for CUDA-accelerated differentiable rasterization of 3D gaussians with Python bindings. The library is inspired by the SIGGRAPH paper "3D Gaussian Splatting for Real-Time Rendering of Radiance Fields", but gsplat is faster, more memory efficient, and with a growing list of new features.

