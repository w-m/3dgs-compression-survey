### BOGausS: Better Optimized Gaussian Splatting
BOGausS (Better Optimized Gaussian Splatting) proposes an improved training strategy for 3D Gaussian Splatting. BOGausS  solution is able to generate models up to ten times lighter than the original 3DGS with no quality degradation.

 BOGausS improvements are the result of several contributions:
<ul>
<li> Confidence estimation of 3D reconstruction. Through a parallel with Variational Bayesian Inference, a confidence metrics on geometry reconstruction is established. From these findings a minimal size for each Gaussian is defined depending on its localization. This prevents over-sampling Gaussians in some areas and enable adaptive scaling for updates of Gaussian features (position, scales) relative to their position within the scene (typically a faraway Gaussian will get stronger updates than a Gaussian located in the close focus area). </li>

<li>> Unbiased Sparse Adam Optimizer. We propose a revised Optimizer that ensures unbiased smooth Stochastic Gradient Descent. Sparse Adam aims at updating Gaussians that are only visible from considered training camera. However traditional Sparse Adam optimizers have biased filtered states estimator. We modified it to get unbiased states estimator, and to enable states inheritance when splitting a Gaussian. These adaptations allow to get a smoother loss evolution along training iterations. This optimizer also exploits reconstruction confidence intervals to automatically adapt to scene content and camera setup. </li>

<li> Density preserving Gaussian splitting. We propose a new splitting mechanism that allows smooth loss transition. This splitting is considering that a Gaussian kernel can be approximated as a summation of two smaller Gaussian kernels. These smaller kernels are obtained by a split operation along the longest principal axis. Children's center are offset as a fraction of the scale along this axis, and the scale is also reduced. Together with opacity correction for Gaussian children this ensure again smooth loss transition during training iterations. </li>

<li> Distortion-based densification of Gaussians. We propose densification and pruning strategy inspired from rate-distortion optimization with new prioritization metrics. Densification prioritization criterion is based on relative contributing error associated to Gaussians which aims at selecting the best split according to rate-distortion. Pruning is based on measure of the effective opacity of the Gaussians which is a good indicator of its low contribution to the rendering. </li>

<li> Exposure correction. Additionally, BOGausS can take benefits of exposure correction mechanism as proposed in some recent studies and provide further gains. </li>
</ul>