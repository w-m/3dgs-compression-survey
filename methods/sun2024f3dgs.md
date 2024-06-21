### F-3DGS: Factorized Coordinates and Representations for 3D Gaussian Splatting


The paper introduces a novel 3D Gaussian compression method using structured coordinates and decomposed representations through factorization. Inspired by tensor or matrix factorization techniques, this method generates 3D coordinates via a tensor product of 1D or 2D coordinates, enhancing spatial efficiency. It extends factorization to include attributes like color, scale, rotation, and opacity, which compresses the model size while maintaining essential characteristics. A binary mask is employed to eliminate non-essential Gaussians, significantly accelerating training and rendering speeds. Experiments demonstrate that this approach reduces storage requirements by over 90% without compromising image quality, proving its efficiency in representing 3D scenes.
<br><br>
<span style="color:red"><b>Note:</b> This paper is currently not included in the survey table because it shows unusually high results in the Tanks and Temples dataset and reports higher results for the original 3DGS than those in the original publication. This raises the possibility that their testing methods may differ from those used in other papers.</span>