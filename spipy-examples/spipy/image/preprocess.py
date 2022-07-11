import sys
import numpy as np
import multiprocessing as mp
sys.path.append(__file__.split("/image/preprocess.py")[0] + "/analyse")
import saxs
import radp
import criterion

def help(module):
	if module=="fix_artifact":
		print("This function reduces artifacts of an adu dataset, whose patterns share the same artifacts")
		print("    -> Input: dataset (FLOAT adu patterns, numpy.ndarray, shape=(Nd,Nx,Ny))")
		print("              estimated_center (estimated pattern center, (Cx,Cy))")
		print("              artifacts (artifact location in pattern, numpy.ndarray, shape=(Na,2))")
		print("     *option: mask (mask area of patterns, 0/1 numpy.ndarray where 1 means masked, shape=(Nx,Ny), default=None)")
		print("    -> Return: dataset (To save RAM, your input dataset is modified directly)")
		print("[Notice] This function cannot reduce backgroud noise, try preprocess.adu2photon instead")
		print("Help exit.")
		return
	elif module=="fix_artifact_auto":
		print("This function implements another algorithm to fix artifacts, without providing the position of artifacts")
		print("    -> Input: dataset (FLOAT adu patterns, numpy.ndarray, shape=(Nd,Nx,Ny))")
		print("              estimated_center (estimated pattern center, (Cx,Cy))")
		print("     *option: njobs (number of processes to run in parallel, default=1)")
		print("     *option: mask (mask area of patterns, 0/1 numpy.ndarray where 1 means masked, shape=(Nx,Ny), default=None)")
		print("     *option: vol_of_bins (the number of similar patterns that will be processed together in a group, default=100)")
		print("    -> Output: dataset (To save RAM, your input dataset is modified directly)")
		print("[NOTICE] vol_of_bins is suggested to be 100~200 and the whole dataset is suggested to contain >1k patterns")
	elif module=="adu2photon":
		print("This function is used to evaluate adu value per photon and transfer adu to photon")
		print("    -> Input: dataset ( patterns of adu values, numpy.ndarray, shape=(Nd,Nx,Ny) )")
		print("     *option: mask ( masked area in patterns, shape=(Nx,Ny), a 0/1 2d-array where 1 means masked point, default=None )")
		print("     *option: photon_percent ( estimated percent of pixels that has photons, default=0.1)")
		print("     *option: nproc ( number of processes running in parallel, default=2)")
		print("     *option: transfer ( bool, Ture -> evaluate adu unit and transfer to photon, False -> just evaluate, default=True)")
		print("     *option: force_poisson ( bool, whether to determine photon numbers at each pixel according to poisson distribution, default=False, ignored if transfer=False )")
		print("    -> Return: adu (float) or [adu, data_photonCount] ( [float, int numpy.ndarray(Nd,Nx,Ny)] )")
		print("[Notice] This function is implemented with multi-processes. Nd is recommened to be >1k")
		print("Help exit.")
		return
	elif module=="hit_find":
		print("This function is used for hit finding, based on chi-square test. High score means hit")
		print("    -> Input: dataset ( raw patterns for intput, numpy.ndarray, shape=(Nd,Nx,Ny) )")
		print("              background ( averaged running background pattern, numpy.ndarray, shape=(Nx,Ny))")
		print("     *option: radii_range ( radii of annular area used for hit-finding, list/array, [center_x, center_y, inner_r, outer_r], unit=pixel, default=None)")
		print("     *option: mask (mask area of patterns, 0/1 numpy.ndarray where 1 means masked, shape=(Nx,Ny), default=None)")
		print("     *option: cut_off ( chi-square cut-off, positve int/float, default=None and a mix-gaussian analysis is used for clustering)")
		print("    -> Return: label ( 0/1 array, 1 stands for hit, the same order with 'dataset' )")
		print("[Notice] if use cut_off=None, it's better for input dataset to contain over 100 patterns")
	elif module=="hit_find_pearson":
		print("This function is used for hit finding, based on pearson correlation score between pattern and background. Low score means hit.")
		print("    -> Input: dataset ( raw patterns for intput, numpy.ndarray, shape=(Nd,Nx,Ny) )")
		print("              background ( averaged running background pattern, numpy.ndarray, shape=(Nx,Ny))")
		print("     *option: radii_range ( radii of annular area used for hit-finding, list/array, [center_x, center_y, inner_r, outer_r], unit=pixel, default=None)")
		print("     *option: mask (mask area of patterns, 0/1 numpy.ndarray where 1 means masked, shape=(Nx,Ny), default=None)")
		print("     *option: max_cc ( max cc for patterns to be identified as hits, -1~1 float, default=0.5)")
		print("    -> Return: label ( 0/1 array, 1 stands for hit, the same order with 'dataset' )")
	else:
		raise ValueError("No module names "+str(module))


def _fix_artifact_auto_single_process(data, label, center, I_prime, mask):

	def radp_flat(I_qphi, pats, center, mask):
		center_0 = np.round(center)
		x, y = np.indices((pats.shape[1:]))
		r = np.sqrt((x - center_0[0])**2 + (y - center_0[1])**2)
		r = r.astype(np.int)
		if mask is not None:
			maskdata = pats * (1-mask)
		else:
			maskdata = pats
		ref_Iq = radp.radial_profile_2d(I_qphi, center_0, mask)

		for ind,rad in enumerate(ref_Iq[:,0]):
			roi = np.where((r==rad) & (I_qphi>0))
			maskdata[:,roi[0],roi[1]] = maskdata[:,roi[0],roi[1]] * ref_Iq[ind,1] / I_qphi[roi]
		return maskdata

	import copy
	if len(data.shape)!=3:
		raise RuntimeError("Input data dimension error : dimension=" + str(len(data.shape)))
	for l in set(label):
		sbin = np.where(label==l)[0]
		data_bin = data[sbin]
		I_qphi = np.mean(data_bin,axis=0)
		G_tau = np.ones(I_qphi.shape)
		if mask is not None:
			I_qphi *= (1-mask)
			roi = np.where(I_qphi>0)
			G_tau[roi] = I_prime[roi]*(1-mask[roi])/I_qphi[roi]
		else:
			roi = np.where(I_qphi>0)
			G_tau[roi] = I_prime[roi]/I_qphi[roi]
		data[sbin] = G_tau * radp_flat(I_qphi, data_bin, center, mask)
	return data


def fix_artifact_auto(dataset, estimated_center, njobs=1, mask=None, vol_of_bins=100):
	import classify
	njobs = abs(int(njobs))
	dataset[np.isnan(dataset)] = 0
	dataset[np.isinf(dataset)] = 0
	dataset[np.where(dataset<0)] = 0
	center = saxs.friedel_search(np.sum(dataset,axis=0), estimated_center, mask)
	# calculate intensity distribution
	print("\nAnalysing spectral distribution ...")
	num_of_bins = int(np.ceil(len(dataset)/vol_of_bins))
	_,labels = classify.cluster_fSpec(dataset, mask, decomposition='SpecEM', ncomponent=2, clustering=num_of_bins, njobs=njobs)
	# fix
	print("\nFix artifacts ...")
	I_prime = np.mean(dataset, axis=0)
	if njobs==1:
		dataset = _fix_artifact_auto_single_process(dataset, labels, center, I_prime, mask)
	else:
		poolbin = np.linspace(0, num_of_bins, njobs+1, dtype=int)
		pool = mp.Pool(processes = njobs)
		result = []
		selected_index_all = []
		for ind,i in enumerate(poolbin[:-1]):
			start_label = i
			end_label = poolbin[ind+1]
			selection = np.arange(start_label, end_label)
			selected_index = np.where(np.in1d(labels, selection)==True)[0]
			data_part = dataset[selected_index]
			label_part = labels[selected_index]
			print(" Start process "+str(ind))
			result.append(pool.apply_async(_fix_artifact_auto_single_process, args=(data_part, label_part, center, I_prime, mask,)))
			selected_index_all.append(selected_index)
		pool.close()
		pool.join()
		for ind,re in enumerate(result):
			dataset[selected_index_all[ind]] = re.get()
	print("Done.")
	return dataset


def fix_artifact(dataset, estimated_center, artifacts, mask=None):

	if estimated_center is None or artifacts is None:
		raise RuntimeError("no estimated_center or artifacts")
	try:
		dataset[0, artifacts[:,0], artifacts[:,1]]
	except:
		raise RuntimeError("Your input artifacts is not valid")

	print("\nAnalysing artifact locations ...")
	dataset[np.isnan(dataset)] = 0
	dataset[np.isinf(dataset)] = 0
	dataset[np.where(dataset<0)] = 0
	powder = saxs.cal_saxs(dataset)
	center = np.array(saxs.friedel_search(powder, estimated_center, mask))
	inv_art_loc = 2*center - artifacts
	# whether inv_art_loc exceed pattern size
	normal_inv_art_loc = (inv_art_loc[:,0]<powder.shape[0]).astype(int) & (inv_art_loc[:,0]>=0).astype(int) \
		& (inv_art_loc[:,1]<powder.shape[1]).astype(int) & (inv_art_loc[:,1]>=0).astype(int)
	# whether a pair of artifact points is symmetried by center point
	art_pat = np.zeros(powder.shape)
	art_pat[artifacts] = 1
	pair_inv_art_loc_index = np.where(art_pat[inv_art_loc[:,0],inv_art_loc[:,1]]==1)[0]
	# whether inv_art_loc is in mask area
	if mask is not None:
		mask_inv_art_loc_index = np.where(mask[inv_art_loc[:,0],inv_art_loc[:,1]]==1)[0]
	else:
		mask_inv_art_loc_index = None
	# normal and unique locations
	print("Fix normal artifacts ...")
	normal_inv_art_loc[pair_inv_art_loc_index] = 0
	if mask is not None:
		normal_inv_art_loc[mask_inv_art_loc_index] = 0
	uniq_inv_art_loc = 1 - normal_inv_art_loc
	normal_artifacts = np.where(normal_inv_art_loc==1)[0]
	uniq_artifacts = np.where(uniq_inv_art_loc==1)[0]
	# fix artifacts at normal locations
	dataset[:, artifacts[normal_artifacts,0], artifacts[normal_artifacts,1]] = \
			dataset[:, inv_art_loc[normal_artifacts,0], inv_art_loc[normal_artifacts,1]]
	# fix artifacts at unique locations
	print("Fix unique artifacts ...")
	for loc in artifacts[uniq_inv_art_loc]:
		r = np.linalg.norm(loc)
		shell = radp.shells_2d([r], powder.shape, center)[0]
		mean_intens = np.mean(dataset[:, shell[:,0], shell[:,1]], axis=1)
		dataset[:, loc[0], loc[1]] = mean_intens
	return dataset

def adu2photon(dataset, mask=None, photon_percent=0.1, nproc=1, transfer=True, force_poisson=False):

	print("\nEvaluating adu units ...")
	no_photon_percent = 1 - photon_percent
	dataset[np.isnan(dataset)] = 0
	dataset[np.isinf(dataset)] = 0
	dataset[np.where(dataset<0)] = 0
	if mask is not None:
		mindex = np.where(mask==1)
		dataset[:,mindex[0],mindex[1]] = 0
	powder = saxs.cal_saxs(dataset)
	countp = np.bincount(np.round(powder.ravel()).astype(int))
	if mask is not None:
		countp[0] = countp[0] - len(np.where(mask==1))
	sumc = np.cumsum(countp)
	percentc = sumc/sumc[-1].astype(float)
	try:
		adu = np.where(np.abs(percentc-no_photon_percent)<0.1)[0][0]
	except:
		adu = np.where((percentc-no_photon_percent)>=0)[0][0]
	print("Estimated adu value is " + str(adu) + ". Done.\n")

	if transfer:
		print("Transferring adu patterns to photon count patterns ...")
		if nproc==1:
			out = _transfer(dataset, no_photon_percent, adu, force_poisson)
		else:
			result = []
			partition = range(0, len(dataset), np.ceil(len(dataset)/float(nproc)).astype(int))
			if len(partition)==nproc:
				partition.append(len(dataset))
			pool = mp.Pool(processes = nproc)
			for i in np.arange(nproc):
				data_part = dataset[partition[i]:partition[i+1]]
				result.append(pool.apply_async(_transfer, args=(data_part,no_photon_percent,adu,force_poisson,)))
				print("Start process " + str(i) + " .")
			pool.close()
			pool.join()
			out = np.zeros(dataset.shape, dtype='i4')
			for ind,p in enumerate(result):
				out[partition[ind]:partition[ind+1]] = p.get()
		print("Done.\n")
		return adu, out
	else:
		return adu

def _transfer(data, no_photon_percent, adu, force_poisson):

	def poisson(lamb):
		return np.random.poisson(lamb,1)[0]

	if data == []:
		return np.array([])
	re = np.zeros(data.shape, dtype='i4')
	for ind,pat in enumerate(data):
		"""
		countp = np.bincount(np.round(pat.ravel()).astype(int))
		sumc = np.cumsum(countp)
		percentc = sumc/sumc[-1].astype(float)
		try:
			adu_mine = np.where(np.abs(percentc-no_photon_percent)<0.1)[0][0]
		except:
			adu_mine = np.where((percentc-no_photon_percent)>=0)[0][0]
		real_adu = 0.6*adu_mine + 0.4*adu
		"""
		real_adu = adu
		if force_poisson:
			newp = np.frompyfunc(poisson,1,1)
			re[ind] = newp(pat/real_adu)
		else:
			newp = np.round(pat/real_adu).astype(int)
			re[ind] = newp
	return re

def hit_find(dataset, background, radii_range=None, mask=None, cut_off=None):
	dataset[np.isnan(dataset)] = 0
	dataset[np.isinf(dataset)] = 0
	dataset = np.abs(dataset)
	background[np.isnan(background)] = 0
	background[np.isinf(background)] = 0
	background = np.abs(background)
	if mask is not None:
		maskdataset = dataset * (1-mask)
		maskbackground = background * (1 - mask)
	else:
		maskdataset = dataset
		maskbackground = background
	dsize = maskdataset.shape
	if len(dsize)!=3 or background.shape!=dsize[1:]:
		raise RuntimeError("Input a set of 2d patterns! background should have the same shape with input!")
	# calculate
	chi = np.zeros((dsize[0],1))
	if radii_range is not None:
		if radii_range[0] is not None and radii_range[1] is not None:
			center = [0,0]
			center[0] = radii_range[0]
			center[1] = radii_range[1]
		else:
			center = saxs.friedel_search(saxs.cal_saxs(maskdataset), np.array(dsize[1:])/2, mask)
		inner_shell = radp.circle(2, radii_range[2]) + np.array(center).astype(int)
		outer_shell = radp.circle(2, radii_range[3]) + np.array(center).astype(int)
		shell = np.zeros(dsize[1:])
		shell[outer_shell[:,0], outer_shell[:,1]] = 1
		shell[inner_shell[:,0], inner_shell[:,1]] = 0
		shell[np.where(mask > 0)] = 0
		shell_index = np.where(shell == 1)
		del shell
		# calculate chi square
		for ind,p in enumerate(maskdataset):
			chi[ind,0] = np.sum( (p[shell_index] - maskbackground[shell_index])**2 )\
						 / np.sum( (maskbackground[shell_index] - np.mean(maskbackground[shell_index]))**2 )
	else:
		# calculate chi square
		for ind,p in enumerate(maskdataset):
			chi[ind,0] = np.sum( (p - maskbackground)**2 )\
						 / np.sum( (maskbackground - np.mean(maskbackground))**2 )
	# predict
	if type(cut_off)==float or type(cut_off)==int:
		# cut-off
		label = np.zeros(dsize[0])
		label[np.where(chi>cut_off)[0]] = 1
	else:
		# clustering
		from sklearn import mixture
		clust = mixture.GaussianMixture(n_components=2, covariance_type='full').fit(chi)
		label = clust.predict(chi)
		if np.mean(chi[np.where(label==0)[0]]) > np.mean(chi[np.where(label==1)[0]]):
			label = 1 - label
	return label

def hit_find_pearson(dataset, background, radii_range=None, mask=None, max_cc=0.5):
	dataset[np.isnan(dataset)] = 0
	dataset[np.isinf(dataset)] = 0
	dataset = np.abs(dataset)
	background[np.isnan(background)] = 0
	background[np.isinf(background)] = 0
	background = np.abs(background)
	if mask is not None:
		maskdataset = dataset * (1 - mask)
		maskbackground = background * (1 - mask)
	else:
		maskdataset = dataset
		maskbackground = background
	dsize = maskdataset.shape
	if len(dsize)!=3 or background.shape!=dsize[1:]:
		raise RuntimeError("Input a set of 2d patterns! background should have the same shape with input!")
	
	cc = np.zeros(dsize[0])
	if radii_range is not None:
		radii_range[2] = int(round(radii_range[2]))
		radii_range[3] = int(round(radii_range[3]))
		if radii_range[0] is None or radii_range[1] is None:
			center = saxs.friedel_search(saxs.cal_saxs(maskdataset), np.array(dsize[1:])/2, mask)
		else:
			center = [0,0]
			center[0] = radii_range[0]
			center[1] = radii_range[1]
		# calculate radial profile
		radp_bg = radp.radial_profile_2d(background, center, mask)[radii_range[2]:radii_range[3],1]
		for ind,p in enumerate(maskdataset):
			radp_d = radp.radial_profile_2d(p, center, mask)[radii_range[2]:radii_range[3],1]
			cc[ind] = criterion.Pearson_cc(radp_d, radp_bg, 0)
	else:
		center = saxs.friedel_search(saxs.cal_saxs(maskdataset), np.array(dsize[1:])/2, mask)
		# calculate radial profile
		radp_bg = radp.radial_profile_2d(background, center, mask)[:,1]
		for ind,p in enumerate(maskdataset):
			radp_d = radp.radial_profile_2d(p, center, mask)[:,1]
			cc[ind] = criterion.Pearson_cc(radp_d, radp_bg, 0)
	# predict
	label = np.zeros(dsize[0])
	label[np.where(cc < max_cc)[0]] = 1
	return label








