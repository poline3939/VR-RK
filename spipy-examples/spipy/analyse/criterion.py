import numpy as np
import sys
from spipy.image import radp

def help(module):
	if module=="r_factor":
		print("This function is used to calculate overall r-factor of two models")
		print("    -> Input: F_cal ( voxel models from calculation, 3d numpy.ndarray )")
		print("              F_obs ( voxel models from observation, 3d numpy.ndarray )")
		print("    -> Output: r-factor ( float )")
		return
	elif module=="r_factor_shell":
		print("This function is used to calculate r-factor in shells between two models")
		print("    -> Input: F_cal ( voxel models from calculation, 3d numpy.ndarray )")
		print("              F_obs ( voxel models from obversation, 3d numpy.ndarray )")
		print("              rlist ( list/array, radius of shells)")
		print("    -> Output: r-factor ( np.array, the same shape with rlist )")
		print("[NOTICE] (Size_x/2, Size_y/2, Size_z/2) is used as the center of input matrix")
		return
	elif module=="fsc":
		print("Calculate Fourier Shell Correlation between two models (in frequency space)")
		print("    -> Input: F1 ( the first voxel model, 3d numpy.array )")
		print("              F2 ( the second voxel model, 3d numpy.array)")
		print("              rlist ( list/array, radius of shells)")
		print("    -> Output: fsc ( np.array, the same shape with rlist )")
		return
	elif module=="r_split":
		print("Calculate r-split factors between two models (in frequency space)")
		print("    -> Input: F1 ( the first voxel model, 3d numpy.array )")
		print("              F2 ( the second voxel model, 3d numpy.array)")
		print("              rlist ( list/array, radius of shells)")
		print("    -> Output: rs ( np.array, the same shape with rlist )")
	elif module=="Pearson_cc":
		print("Calculate pearson correlation coefficient between two arrays")
		print("    -> Input: exp_d ( the first array, numpy.array, dimension=N)")
		print("              ref_d ( the second array, same shape with exp_d)")
		print("      option: axis ( default is -1, using the last dimension to calculate cc, if not -1 then use all dimensions)")
		print("    -> Output: pearsoncc ( numpy array, dimension = N-1)")
	elif module=="PRTF":
		print("Calculate phase retrieval transfer function of phased dataset (support 2D or 3D data)")
		print("    -> Input: phased_reciprocal ( the reciprocal dataset after independent phasing, dtype=numpy.complex128, shape=(N,Npx,Npy) or (N,Npx,Npy,Npz)")
		print("              center ( the center of phased dataset (zero frequency) )")
		print("     *option: mask ( dataset mask, shape=(Npx,Npy) or (Npx,Npy,Npz), a 0/1 pattern/volume, 1 is masked area )")
		print("    -> Output: radial profile of PRTF, shape=(Np,)")
	else:
		raise ValueError("No module names "+str(module))

def r_factor(F_cal, F_obs):
	if F_cal.shape != F_obs.shape:
		raise RuntimeError("F1 and F2 should be in the same size!")
	return np.sum(np.abs(np.abs(F_obs) - np.abs(F_cal))) / np.sum(np.abs(F_obs))

def r_factor_shell(F_cal, F_obs, rlist):
	if F_cal.shape != F_obs.shape:
		raise RuntimeError("F1 and F2 should be in the same size!")
	size = np.array(F_cal.shape)
	center = (size-1)/2.0
	shells = radp.shells_3d(rlist, size, center)
	Rf = np.zeros(len(rlist))
	for ind,shell in enumerate(shells):
		shell_f_cal = F_cal[shell[:,0],shell[:,1],shell[:,2]] + 1e-15
		shell_f_obs = F_obs[shell[:,0],shell[:,1],shell[:,2]] + 1e-15
		Rf[ind] = np.sum(np.abs(np.abs(shell_f_obs) - np.abs(shell_f_cal))) / np.sum(np.abs(shell_f_obs))
	return Rf

def fsc(F1, F2, rlist):
	if F1.shape != F2.shape:
		raise RuntimeError("F1 and F2 should be in the same size!")
	size = np.array(F1.shape)
	center = (size-1)/2.0
	shells = radp.shells_3d(rlist, size, center)
	FSC = np.zeros(len(rlist))
	for ind,shell in enumerate(shells):
		shell_f1 = F1[shell[:,0],shell[:,1],shell[:,2]] + 1e-15
		shell_f2 = F2[shell[:,0],shell[:,1],shell[:,2]] + 1e-15
		up = np.sum( shell_f1 * np.conj(shell_f2) )
		down = np.sqrt( np.sum( np.abs(shell_f1)**2 ) * np.sum( np.abs(shell_f2)**2 ) )
		FSC[ind] = np.abs(up) / down
	return FSC

def r_split(F1, F2, rlist):
	if F1.shape != F2.shape:
		raise RuntimeError("F1 and F2 should be in the same size!")
	size = np.array(F1.shape)
	center = (size-1)/2.0
	shells = radp.shells_3d(rlist, size, center)
	rs = np.zeros(len(rlist))
	for ind,shell in enumerate(shells):
		shell_f1 = F1[shell[:,0],shell[:,1],shell[:,2]] + 1e-15
		shell_f2 = F2[shell[:,0],shell[:,1],shell[:,2]] + 1e-15
		rs[ind] = np.sqrt(2) * np.sum(np.abs(np.abs(shell_f1) - np.abs(shell_f2))) / np.sum(np.abs(shell_f1) + np.abs(shell_f2))
	return rs

def Pearson_cc(exp_d, ref_d, axis=-1):
	if exp_d.shape != ref_d.shape:
		raise RuntimeError("exp_d and ref_d should be in the same size!")
	if axis == -1 and len(exp_d.shape)>1:
		new_shape = list(ref_d.shape)[:-1] + [1]
		mean_exp = np.mean(exp_d,axis=-1).reshape(new_shape)
		mean_ref = np.mean(ref_d,axis=-1).reshape(new_shape)
		numerator = np.mean((exp_d - mean_exp) * (ref_d - mean_ref) , axis=-1)
		dominator = np.sqrt((np.mean(exp_d**2, axis=-1)-np.mean(exp_d, axis=-1)**2) * (np.mean(ref_d**2, axis=-1)-np.mean(ref_d, axis=-1)**2))
	else:
		numerator = np.mean((exp_d - np.mean(exp_d)) * (ref_d - np.mean(ref_d)))
		dominator = np.sqrt((np.mean(exp_d**2)-np.mean(exp_d)**2) * (np.mean(ref_d**2)-np.mean(ref_d)**2))
	return numerator/dominator

def PRTF(phased_reciprocal, center, mask=None):
	if mask is not None and mask.shape != phased_reciprocal.shape[1:]:
		raise RuntimeError("mask shape is not compatible with input reciprocal data")
	phase = np.zeros(phased_reciprocal.shape,dtype=np.complex128)
	zero_index = np.where(np.abs(phased_reciprocal)!=0)
	phase[zero_index] = np.array(phased_reciprocal[zero_index])/np.abs(phased_reciprocal[zero_index])
	PRTF = np.abs(phase.mean(axis=0))
	if len(phased_reciprocal.shape) == 3:
		PRTF_rav = radp.radial_profile_2d(PRTF, center, mask)
	elif len(phased_reciprocal.shape) == 4:
		PRTF_rav = radp.radial_profile_3d(PRTF, center, mask)
	return PRTF_rav