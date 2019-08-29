import numpy as np
from scipy import sparse
from a2dr.proximal.projection import proj_l1
from a2dr.proximal.composition import prox_scale

def prox_norm1(v, t = 1, *args, **kwargs):
    """Proximal operator of :math:`tf(ax-b) + c^Tx + d\\|x\\|_2^2`, where :math:`f(x) = \\|x\\|_1`
    for scalar t > 0, and the optional arguments are a = scale, b = offset, c = lin_term, and d = quad_term.
    We must have t > 0, a = non-zero, and d >= 0. By default, t = 1, a = 1, b = 0, c = 0, and d = 0.
    """
    return prox_scale(prox_norm1_base, *args, **kwargs)(v, t)

def prox_norm2(v, t = 1, *args, **kwargs):
    """Proximal operator of :math:`tf(ax-b) + c^Tx + d\\|x\\|_2^2`, where :math:`f(x) = \\|x\\|_2`
    for scalar t > 0, and the optional arguments are a = scale, b = offset, c = lin_term, and d = quad_term.
    We must have t > 0, a = non-zero, and d >= 0. By default, t = 1, a = 1, b = 0, c = 0, and d = 0.
    """
    return prox_scale(prox_norm2_base, *args, **kwargs)(v, t)

def prox_norm_inf(v, t = 1, *args, **kwargs):
    """Proximal operator of :math:`tf(ax-b) + c^Tx + d\\|x\\|_2^2`, where :math:`f(x) = \\|x\\|_{\\infty}`
    for scalar t > 0, and the optional arguments are a = scale, b = offset, c = lin_term, and d = quad_term.
    We must have t > 0, a = non-zero, and d >= 0. By default, t = 1, a = 1, b = 0, c = 0, and d = 0.
    """
    return prox_scale(prox_norm_inf_base, *args, **kwargs)(v, t)

def prox_norm_nuc(B, t = 1, *args, **kwargs):
    """Proximal operator of :math:`tf(aB-b) + cB + d\\|B\\|_F^2`, where :math:`f(B) = \\|B\\|_*`
    for scalar t > 0, and the optional arguments are a = scale, b = offset, c = lin_term, and d = quad_term.
    We must have t > 0, a = non-zero, and d >= 0. By default, t = 1, a = 1, b = 0, c = 0, and d = 0.
    """
    return prox_scale(prox_norm_nuc_base, *args, **kwargs)(B, t)

def prox_group_lasso(B, t = 1, *args, **kwargs):
    """Proximal operator of :math:`tf(aB-b) + cB + d\\|B\\|_F^2`, where :math:`f(B) = \\|B\\|_{2,1}` is the
    group lasso of :math:`B`, for scalar t > 0, and the optional arguments are a = scale, b = offset,
    c = lin_term, and d = quad_term. We must have t > 0, a = non-zero, and d >= 0. By default, t = 1, a = 1,
    b = 0, c = 0, and d = 0.
    """
    return prox_scale(prox_group_lasso_base, *args, **kwargs)(B, t)

def prox_norm1_base(v, t):
	"""Proximal operator of :math:`f(x) = \\|x\\|_1`.
	"""
	if sparse.issparse(v):
		max_elemwise = lambda x, y: x.maximum(y)
	else:
		max_elemwise = np.maximum
	return max_elemwise(v - t, 0) - max_elemwise(-v - t, 0)

def prox_norm2_base(v, t):
	"""Proximal operator of :math:`f(x) = \\|x\\|_2`.
	"""
	if sparse.issparse(v):
		norm = sparse.linalg.norm
		zeros = sparse.csr_matrix
	else:
		norm = np.linalg.norm
		zeros = np.zeros

	if len(v.shape) == 2:
		v_norm = norm(v,'fro')
	elif len(v.shape) == 1:
		v_norm = norm(v,2)
	if v_norm == 0:
		return zeros(v.shape)
	else:
		return np.maximum(1 - t*1.0/v_norm, 0) * v

def prox_norm_inf_base(v, t):
	"""Proximal operator of :math:`f(x) = \\|x\\|_{\\infty}`.
	"""
	# TODO: Sparse handling.
	return v - t * proj_l1(v/t)

def prox_norm_nuc_base(B, t):
	"""Proximal operator of :math:`f(B) = \\|B\\|_*`, the nuclear norm of :math:`B`.
	"""
	U, s, Vt = np.linalg.svd(B, full_matrices=False)
	s_new = np.maximum(s - t, 0)
	return U.dot(np.diag(s_new)).dot(Vt)

def prox_group_lasso_base(B, t):
	"""Proximal operator of :math:`f(B) = \\|B\\|_{2,1} = \\sum_j \\|B_j\\|_2`, the group lasso of :math:`B`,
	where :math:`B_j` is the j-th column of :math:`B`.
	"""
	# TODO: Sparse handling.
	if sparse.issparse(B):
		return sparse.hstack([prox_norm2(B[:,j], t) for j in range(B.shape[1])])
	else:
		return np.vstack([prox_norm2(B[:,j], t) for j in range(B.shape[1])]).T