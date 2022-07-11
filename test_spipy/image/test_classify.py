import numpy as np
import h5py
from spipy.image import classify

if __name__ == "__main__":
	f = h5py.File('../test_pattern.h5', 'r')
	data = f['patterns'][...]
	label = f['labels'][...]
	mask = f['mask'][...]
	f.close()
	
	# test classify.cluster_fSpec
	print("\n**1** Test classifiy.cluster_fSpec ...")

	print("\n(1) 'LLE'")
	d_comp, predict = classify.cluster_fSpec(data, mask=mask, low_filter=0.3, decomposition='LLE', ncomponent=2, nneighbors=5, LLEmethod='standard')
	print( "data shape after decomposition : " + str(d_comp.shape) )
	acc = len(np.where(label-predict==0)[0])/float(len(label))
	print( "predicted precision : " + str(max(acc,1-acc)) )

	print("\n(2) 'SVD'")
	d_comp, predict = classify.cluster_fSpec(data, mask=mask, low_filter=0.3, decomposition='SVD', ncomponent=2)
	print( "data shape after decomposition : " + str(d_comp.shape) )
	acc = len(np.where(label-predict==0)[0])/float(len(label))
	print( "predicted precision : " + str(max(acc,1-acc)) )

	print("\n(3) 'SpecEM'")
	d_comp, predict = classify.cluster_fSpec(data, mask=mask, low_filter=0.3, decomposition='SpecEM', ncomponent=2)
	print( "data shape after decomposition : " + str(d_comp.shape) )
	acc = len(np.where(label-predict==0)[0])/float(len(label))
	print( "predicted precision : " + str(max(acc,1-acc)) )

	# test classify.cluster_fTSNE
	print("\n**2** Test classify.cluster_fTSNE ...")
	d_comp, predict = classify.cluster_fTSNE(data, mask=mask, low_filter=0.3, no_dims=2, perplexity=10, use_pca=True, initial_dims=20, max_iter=500, theta=0.5, randseed=-1, verbose=True)
	print( "data shape after decomposition : " + str(d_comp.shape) )
	acc = len(np.where(label-predict==0)[0])/float(len(label))
	print( "predicted precision : " + str(max(acc,1-acc)) )

	

