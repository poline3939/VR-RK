import numpy as np
import matplotlib.pyplot as plt
import h5py
from spipy.image import radp
from spipy.analyse import q
import sys

if __name__=="__main__":
	fi = sys.argv[1]
	try:
		exparam = sys.argv[2].split(',')
	except:
		exparam = None
	f = h5py.File(fi,'r')
	# prtf = np.abs(np.fft.fftshift(f['PRTF'][...]))
	# size = prtf.shape
	# prtf_rav = radp.radial_profile_2d(prtf,[size[0]/2,size[1]/2])
	sr = np.abs(np.fft.fftshift(f['sample retrieved'][...]))
	dr = np.abs(np.fft.fftshift(np.fft.fft2(np.fft.ifftshift(sr))))**2
	d = np.abs(np.fft.fftshift(f['data'][...]))
	# metric = f['convergence metric'][...]
	# mod_error = f['modulus error'][...]

	plt.figure(figsize=(20,10))

	plt.subplot(2,3,1)
	plt.imshow(np.log(1+sr))
	plt.title('retrieved (real space)')

	plt.subplot(2,3,2)
	plt.imshow(np.log(1+dr))
	plt.title('retrieved (reciprocal space)')

	plt.subplot(2,3,3)
	plt.imshow(np.log(1+d))
	plt.title('input (reciprocal space)')

	
	plt.savefig('input_fig')

	plt.figure(figsize=(20,10))


	plt.show()
